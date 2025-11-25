"""
Noteblog 主应用入口
"""
from app import create_app, db
from app.models.setting import SettingManager
from flask_migrate import upgrade

app = create_app()

# 在应用上下文中初始化数据库表和默认设置
with app.app_context():
    # 创建数据库表
    db.create_all()
    
    # 初始化默认设置
    SettingManager.init_default_settings()

@app.shell_context_processor
def make_shell_context():
    """为 shell 提供上下文"""
    from app.models import User, Post, Category, Tag, Comment, Plugin, Theme, Setting
    return {
        'db': db,
        'User': User,
        'Post': Post,
        'Category': Category,
        'Tag': Tag,
        'Comment': Comment,
        'Plugin': Plugin,
        'Theme': Theme,
        'Setting': Setting,
        'SettingManager': SettingManager
    }

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
