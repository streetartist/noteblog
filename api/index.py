"""
Vercel Serverless Function 入口文件 (最终版)
"""
import sys
import os
import tempfile

# --- 环境和路径设置 ---
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
temp_dir = tempfile.gettempdir()
os.environ.setdefault('FLASK_INSTANCE_PATH', temp_dir)
os.makedirs(temp_dir, exist_ok=True)

# --- 应用创建和初始化 ---
from app import create_app, db

# 1. 创建一个已经包含所有插件和蓝图的应用实例
app = create_app()

# 2. 在应用上下文中，执行一次性的数据库初始化和数据填充
with app.app_context():
    print("Vercel实例启动：开始数据库检查和初始化...")
    try:
        # 这会创建所有尚未存在的表
        db.create_all()

        # --- 填充默认数据 (如果需要) ---
        from app.models.setting import Setting
        from app.models.user import User

        # 检查并创建默认设置
        if not Setting.query.filter_by(key='site_title').first():
            print("正在填充默认设置...")
            # (这里可以添加创建默认设置的代码，如果需要的话)
            # 例如: new_setting = Setting(...) db.session.add(new_setting)
            db.session.commit()

        # 检查并创建管理员用户
        if not User.query.filter_by(is_admin=True).first():
            print("正在创建默认管理员用户...")
            admin = User('admin', 'admin@example.com', 'admin123', display_name='管理员', is_admin=True, is_active=True)
            db.session.add(admin)
            db.session.commit()
            
        print("数据库检查和初始化完成。")
    except Exception as e:
        print(f"在Vercel初始化过程中发生错误: {e}")
        db.session.rollback()

# --- 导出 WSGI 应用 ---
application = app