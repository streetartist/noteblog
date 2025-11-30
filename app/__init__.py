"""
Noteblog - 基于 Flask 的可扩展博客框架
"""
from flask import Flask
from flask import send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cors = CORS()

def create_app(config_name='default'):
    """应用工厂函数"""
    # 检查是否有自定义实例路径（用于 Vercel 部署）
    instance_path = os.getenv('FLASK_INSTANCE_PATH')
    if instance_path:
        # 确保实例路径存在
        os.makedirs(instance_path, exist_ok=True)
        app = Flask(__name__, instance_path=instance_path)
    else:
        app = Flask(__name__)
    
    # 确保默认实例目录存在，便于后续写入上传等数据
    os.makedirs(app.instance_path, exist_ok=True)

    # 配置
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # 数据库配置 - 修复 SQLAlchemy 方言问题
    database_url = os.getenv('DATABASE_URL', 'sqlite:///noteblog.db')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 上传/文件相关配置
    raw_upload_folder = os.getenv('UPLOAD_FOLDER')
    if raw_upload_folder:
        upload_folder = raw_upload_folder if os.path.isabs(raw_upload_folder) else os.path.join(app.instance_path, raw_upload_folder)
    else:
        upload_folder = os.path.join(app.instance_path, 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder

    try:
        app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    except (TypeError, ValueError):
        app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    allowed_uploads = os.getenv('ALLOWED_UPLOAD_EXTENSIONS', 'jpg,jpeg,png,gif,webp')
    app.config['ALLOWED_UPLOAD_EXTENSIONS'] = {ext.strip().lower() for ext in allowed_uploads.split(',') if ext.strip()}

    allowed_mimes = os.getenv('ALLOWED_UPLOAD_MIME_TYPES', 'image/png,image/jpeg,image/gif,image/webp')
    app.config['ALLOWED_UPLOAD_MIME_TYPES'] = {mime.strip().lower() for mime in allowed_mimes.split(',') if mime.strip()}
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    cors.init_app(app)
    
    # 登录管理器配置
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录以访问此页面。'
    
    # 注册蓝图
    from app.views import main, auth, admin, api
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp, url_prefix='/auth')
    app.register_blueprint(admin.bp, url_prefix='/admin')
    app.register_blueprint(api.bp, url_prefix='/api')
    
    # 初始化插件系统
    from app.services.plugin_manager import plugin_manager
    # 某些初始化流程（例如首次运行创建数据库表）在插件表尚不存在时
    # plugin_manager 会尝试访问数据库导致错误。通过环境变量
    # SKIP_PLUGIN_INIT=1 可以在初始化过程中跳过插件/主题加载。
    if os.getenv('SKIP_PLUGIN_INIT', '0') != '1':
        plugin_manager.init_app(app)
    
    # 初始化主题系统
    from app.services.theme_manager import theme_manager
    if os.getenv('SKIP_PLUGIN_INIT', '0') != '1':
        theme_manager.init_app(app)

    # 注册请求处理钩子
    @app.before_request
    def before_request_handler():
        if hasattr(app, 'plugin_manager'):
            app.plugin_manager.do_action('before_request')

    @app.after_request
    def after_request_handler(response):
        if hasattr(app, 'plugin_manager'):
            # after_request钩子通常需要接收response对象
            # 但我们的do_action不直接处理返回值，所以这里只是触发
            app.plugin_manager.do_action('after_request', response)
        return response
    
    # 添加全局模板上下文处理器
    @app.context_processor
    def inject_plugin_hooks():
        """为所有模板注入插件钩子"""
        if os.getenv('SKIP_PLUGIN_INIT', '0') == '1':
            return {}
        
        try:
            from app.services.plugin_manager import plugin_manager
            
            # 获取插件钩子内容
            plugin_hooks = {
                'sidebar_bottom': plugin_manager.get_template_hooks('sidebar_bottom')
            }
            
            return {'plugin_hooks': plugin_hooks}
        except Exception:
            # 如果插件管理器不可用，返回空字典
            return {}

    # 提供主题静态文件（/themes/<theme>/static/...）的路由，便于主题资源加载
    @app.route('/themes/<theme_name>/static/<path:filename>')
    def theme_static(theme_name, filename):
        themes_dir = os.path.join(os.getcwd(), 'themes')
        static_dir = os.path.join(themes_dir, theme_name, 'static')
        # send_from_directory 会处理路径安全性
        return send_from_directory(static_dir, filename)
    
    # 提供插件静态文件（/static/plugins/<plugin>/...）的路由，便于插件资源加载
    @app.route('/static/plugins/<plugin_name>/<path:filename>')
    def plugin_static(plugin_name, filename):
        plugins_dir = os.path.join(os.getcwd(), 'plugins')
        static_dir = os.path.join(plugins_dir, plugin_name, 'static')
        # send_from_directory 会处理路径安全性
        return send_from_directory(static_dir, filename)

    # 提供上传文件访问路由（/uploads/...）
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        upload_dir = app.config.get('UPLOAD_FOLDER', os.path.join(app.instance_path, 'uploads'))
        return send_from_directory(upload_dir, filename)
    
    # 全局错误处理器
    @app.errorhandler(404)
    def not_found(error):
        """404 错误处理"""
        from app.models.setting import SettingManager
        from flask_login import current_user
        site_brand = SettingManager.get('site_title', 'Noteblog')
        context = {
            'error': error,
            'site_title': site_brand,
            'page_title': f"页面未找到 - {site_brand}",
            'current_user': current_user
        }
        
        # 使用主题管理器渲染404模板
        if hasattr(app, 'theme_manager') and app.theme_manager.current_theme:
            return app.theme_manager.render_template('404.html', **context), 404
        else:
            # 如果主题管理器不可用，返回简单的404页面
            return """
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>页面未找到</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    h1 { color: #666; }
                </style>
            </head>
            <body>
                <h1>404 - 页面未找到</h1>
                <p>抱歉，您访问的页面不存在。</p>
                <a href="/">返回首页</a>
            </body>
            </html>
            """, 404

    @app.errorhandler(500)
    def internal_error(error):
        """500 错误处理"""
        from app.models.setting import SettingManager
        from flask_login import current_user
        
        # 回滚数据库会话
        db.session.rollback()
        site_brand = SettingManager.get('site_title', 'Noteblog')
        context = {
            'error': error,
            'site_title': site_brand,
            'page_title': f"服务器错误 - {site_brand}",
            'current_user': current_user
        }
        
        # 使用主题管理器渲染500模板
        if hasattr(app, 'theme_manager') and app.theme_manager.current_theme:
            return app.theme_manager.render_template('500.html', **context), 500
        else:
            # 如果主题管理器不可用，返回简单的500页面
            return """
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>服务器错误</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    h1 { color: #666; }
                </style>
            </head>
            <body>
                <h1>500 - 服务器内部错误</h1>
                <p>抱歉，服务器遇到了一个错误，请稍后再试。</p>
                <a href="/">返回首页</a>
            </body>
            </html>
            """, 500
    
    return app
