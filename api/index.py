"""
Vercel Serverless Function 入口文件
用于将 Flask 应用部署到 Vercel
"""
import sys
import os
import tempfile

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# 设置环境变量以跳过插件初始化（避免在serverless环境中出现问题）
os.environ.setdefault('SKIP_PLUGIN_INIT', '1')

# 为 Vercel 环境设置可写的临时目录
temp_dir = tempfile.gettempdir()
os.environ.setdefault('FLASK_INSTANCE_PATH', temp_dir)

# 在 Vercel serverless 环境中，优先使用内存数据库
# 因为无服务器环境的文件系统是临时的
use_memory_db = os.getenv('USE_MEMORY_DB', 'true').lower() == 'true'

if use_memory_db:
    # 使用内存数据库 - 最适合无服务器环境
    db_uri = 'sqlite:///:memory:'
    print("使用内存数据库")
else:
    # 尝试使用临时文件数据库
    db_path = os.path.join(temp_dir, 'noteblog.db')
    db_uri = f'sqlite:///{db_path}'
    print(f"使用文件数据库: {db_path}")

os.environ.setdefault('DATABASE_URL', db_uri)

# 确保数据库目录存在
os.makedirs(temp_dir, exist_ok=True)

# 使用原有的应用工厂函数，但修改实例路径
from app import create_app, db

# 创建 Flask 应用 - 使用临时目录作为实例路径
app = create_app()

# 强制设置数据库路径
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['INSTANCE_PATH'] = temp_dir

# 如果使用文件数据库，确保文件可以创建
if not use_memory_db:
    try:
        # 尝试创建数据库文件以确保权限正确
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.close()
        print(f"数据库文件创建成功: {db_path}")
    except Exception as e:
        print(f"数据库文件创建失败: {e}")
        # 如果无法创建文件，切换到内存数据库
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        print("切换到内存数据库")

def init_default_settings():
    """初始化默认设置"""
    from app.models.setting import Setting
    default_settings = [
        ('site_title', 'Noteblog', 'string', '网站标题', True),
        ('site_description', '一个基于Flask的博客系统', 'string', '网站描述', True),
        ('site_keywords', 'blog, flask, python', 'string', '网站关键词', True),
        ('site_author', 'Noteblog', 'string', '网站作者', True),
        ('posts_per_page', '10', 'integer', '每页显示文章数量', False),
        ('comment_moderation', 'true', 'boolean', '是否需要评论审核', False),
        ('allow_registration', 'true', 'boolean', '是否允许用户注册', False),
        ('default_role', 'user', 'string', '默认用户角色', False),
        ('theme', 'default', 'string', '当前主题', False),
        ('timezone', 'Asia/Shanghai', 'string', '时区设置', False),
        ('date_format', '%Y-%m-%d', 'string', '日期格式', False),
        ('time_format', '%H:%M:%S', 'string', '时间格式', False),
    ]
    
    try:
        for key, value, value_type, description, is_public in default_settings:
            setting = Setting.query.filter_by(key=key).first()
            if not setting:
                setting = Setting(key, value, value_type=value_type,
                                  description=description, is_public=is_public)
                db.session.add(setting)
        
        db.session.commit()
        print("默认设置初始化成功")
    except Exception as e:
        print(f"默认设置初始化失败: {e}")
        db.session.rollback()

def create_admin_user():
    """创建默认管理员用户"""
    from app.models.user import User
    try:
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            admin = User(
                'admin',
                'admin@example.com',
                'admin123',
                display_name='管理员',
                is_admin=True,
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            print("管理员用户创建成功")
    except Exception as e:
        print(f"管理员用户创建失败: {e}")
        db.session.rollback()

# 全局变量来跟踪初始化状态
_db_initialized = False

# 创建一个初始化函数，在每次请求时调用
def ensure_database_initialized():
    """确保数据库已初始化"""
    global _db_initialized
    
    # 如果已经初始化过，直接返回
    if _db_initialized:
        return True
    
    try:
        # 创建数据库表
        db.create_all()
        print("数据库表创建完成")
        
        # 初始化默认设置
        init_default_settings()
        
        # 创建管理员用户
        create_admin_user()
        
        _db_initialized = True
        return True
    except Exception as e:
        print(f"数据库初始化错误: {e}")
        _db_initialized = False
        return False

# 修改应用以处理数据库初始化
@app.before_request
def before_request():
    """在每个请求前确保数据库已初始化"""
    global _db_initialized
    
    # 如果还没有初始化，尝试初始化
    if not _db_initialized:
        ensure_database_initialized()
    
    # 尝试连接数据库以确保其可用性
    try:
        # 简单的数据库连接测试
        with db.engine.connect() as conn:
            conn.execute(db.text('SELECT 1'))
    except Exception as e:
        print(f"数据库连接测试失败: {e}")
        # 如果连接失败，重置初始化状态并尝试重新初始化
        _db_initialized = False
        ensure_database_initialized()

# 初始化数据库（如果可能）
ensure_database_initialized()

# 导出 WSGI 应用
# Vercel 会自动调用这个应用来处理请求
application = app
