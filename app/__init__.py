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
        app = Flask(__name__, instance_path=instance_path)
    else:
        app = Flask(__name__)
    
    # 配置
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///noteblog.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
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

    # 提供主题静态文件（/themes/<theme>/static/...）的路由，便于主题资源加载
    @app.route('/themes/<theme_name>/static/<path:filename>')
    def theme_static(theme_name, filename):
        themes_dir = os.path.join(app.root_path, '..', 'themes')
        static_dir = os.path.join(themes_dir, theme_name, 'static')
        # send_from_directory 会处理路径安全性
        return send_from_directory(static_dir, filename)
    
    return app
