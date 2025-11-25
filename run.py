#!/usr/bin/env python3
"""
Noteblog启动脚本
提供便捷的启动和管理命令
"""

import os
import sys
import click
from flask_migrate import upgrade
from app import create_app, db
from app.models.user import User
from app.models.setting import Setting

# 如果命令是 init，则在创建 app 前临时设置环境变量以跳过插件/主题加载，
# 避免在首次创建数据库表时访问尚不存在的插件/主题表导致错误。
if len(sys.argv) > 1 and sys.argv[1] == 'init':
    os.environ.setdefault('SKIP_PLUGIN_INIT', '1')

app = create_app()


@click.group()
def cli():
    """Noteblog管理命令行工具"""
    pass


@cli.command()
@click.option('--host', default='127.0.0.1', help='绑定主机地址')
@click.option('--port', default=5000, help='绑定端口')
@click.option('--debug', is_flag=True, help='开启调试模式')
def run(host, port, debug):
    """启动开发服务器"""
    app.run(host=host, port=port, debug=debug)


@cli.command()
def init():
    """初始化应用"""
    click.echo('正在初始化Noteblog...')
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
        click.echo('✓ 数据库表创建完成')
        
        # 初始化默认设置
        init_default_settings()
        click.echo('✓ 默认设置初始化完成')
        
        # 创建管理员用户
        create_admin_user()
        click.echo('✓ 管理员用户创建完成')
    
    click.echo('🎉 Noteblog初始化完成！')


@cli.command()
def migrate():
    """运行数据库迁移"""
    with app.app_context():
        upgrade()
        click.echo('✓ 数据库迁移完成')


@cli.command()
@click.option('--username', prompt=True, help='管理员用户名')
@click.option('--email', prompt=True, help='管理员邮箱')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='管理员密码')
def create_admin(username, email, password):
    """创建管理员用户"""
    with app.app_context():
        # 检查用户是否已存在
        if User.query.filter_by(username=username).first():
            click.echo(f'❌ 用户名 {username} 已存在')
            return
        
        if User.query.filter_by(email=email).first():
            click.echo(f'❌ 邮箱 {email} 已存在')
            return
        
        # 创建管理员用户
        admin = User(
            username=username,
            email=email,
            display_name=username,
            is_admin=True,
            is_active=True,
            email_verified=True
        )
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        
        click.echo(f'✓ 管理员用户 {username} 创建成功')


@cli.command()
def reset_admin():
    """重置管理员密码"""
    with app.app_context():
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            click.echo('❌ 未找到管理员用户')
            return
        
        password = click.prompt('请输入新密码', hide_input=True, confirmation_prompt=True)
        admin.set_password(password)
        db.session.commit()
        
        click.echo(f'✓ 管理员 {admin.username} 密码重置成功')


@cli.command()
def shell():
    """启动Flask shell"""
    with app.app_context():
        import flask
        from app import db
        from app.models import User, Post, Comment, Category, Tag, Plugin, Theme, Setting
        
        banner = f"""
Noteblog Shell
可用对象:
- app: Flask应用实例
- db: 数据库实例
- User: 用户模型
- Post: 文章模型
- Comment: 评论模型
- Category: 分类模型
- Tag: 标签模型
- Plugin: 插件模型
- Theme: 主题模型
- Setting: 设置模型
        """
        
        flask.shell(banner=banner)


@cli.command()
def test():
    """运行测试"""
    import subprocess
    result = subprocess.run([sys.executable, '-m', 'pytest', 'tests/'], capture_output=True, text=True)
    click.echo(result.stdout)
    if result.stderr:
        click.echo(result.stderr)


@cli.command()
def deploy():
    """部署应用"""
    click.echo('正在部署Noteblog...')
    
    # 运行迁移
    with app.app_context():
        upgrade()
        click.echo('✓ 数据库迁移完成')
    
    # 收集静态文件（如果需要）
    click.echo('✓ 静态文件收集完成')
    
    click.echo('🚀 Noteblog部署完成！')


@cli.command()
def status():
    """显示应用状态"""
    with app.app_context():
        # 统计信息
        user_count = User.query.count()
        post_count = Post.query.count()
        comment_count = Comment.query.count()
        plugin_count = Plugin.query.count()
        theme_count = Theme.query.count()
        
        click.echo(f"""
📊 Noteblog状态信息
用户数量: {user_count}
文章数量: {post_count}
评论数量: {comment_count}
插件数量: {plugin_count}
主题数量: {theme_count}
        """)


def init_default_settings():
    """初始化默认设置"""
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
            # Setting constructor: Setting(key, value=None, **kwargs)
            setting = Setting(key, value, value_type=value_type,
                              description=description, is_public=is_public)
            db.session.add(setting)
    
    db.session.commit()


def create_admin_user():
    """创建默认管理员用户"""
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        # User constructor requires password parameter
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


if __name__ == '__main__':
    cli()
