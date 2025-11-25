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

# 使用内存数据库或临时目录中的数据库
# 在 Vercel serverless 环境中，使用内存数据库更可靠
db_path = os.path.join(temp_dir, 'noteblog.db')
os.environ.setdefault('DATABASE_URL', f'sqlite:///{db_path}')

# 确保数据库目录存在
os.makedirs(temp_dir, exist_ok=True)

# 使用原有的应用工厂函数，但修改实例路径
from app import create_app, db

# 创建 Flask 应用 - 使用临时目录作为实例路径
app = create_app()

# 强制设置数据库路径到临时目录
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['INSTANCE_PATH'] = temp_dir

# 确保数据库文件可以创建
try:
    # 尝试创建数据库文件以确保权限正确
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.close()
    print(f"数据库文件路径: {db_path}")
except Exception as e:
    print(f"数据库文件创建失败: {e}")
    # 如果无法创建文件，使用内存数据库
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
    
    for key, value, value_type, description, is_public in default_settings:
        setting = Setting.query.filter_by(key=key).first()
        if not setting:
            setting = Setting(key, value, value_type=value_type,
                              description=description, is_public=is_public)
            db.session.add(setting)
    
    db.session.commit()

def create_admin_user():
    """创建默认管理员用户"""
    from app.models.user import User
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

# Vercel 需要导出一个名为 'app' 的 WSGI 应用
# 但在 serverless 环境中，我们需要处理一些初始化逻辑

# 在应用上下文中初始化数据库表和默认设置
with app.app_context():
    try:
        # 创建数据库表
        db.create_all()
        print("数据库表创建完成")
        
        # 初始化默认设置（模拟 run.py init 的行为）
        init_default_settings()
        print("默认设置初始化完成")
        
        # 创建管理员用户
        create_admin_user()
        print("管理员用户创建完成")
        
    except Exception as e:
        # 在 serverless 环境中，某些数据库操作可能会失败
        # 我们可以记录错误但继续运行
        print(f"初始化过程中出现错误: {e}")

# 导出 WSGI 应用
# Vercel 会自动调用这个应用来处理请求
application = app
