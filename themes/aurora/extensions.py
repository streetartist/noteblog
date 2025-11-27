"""Aurora 主题扩展入口，采用插件式结构暴露蓝图与自定义页面。"""
from flask import Blueprint, jsonify
from flask_login import login_required

from app.services.theme_manager import ThemeExtensionBase, theme_manager


class AuroraThemeExtension(ThemeExtensionBase):
    """Aurora 主题扩展，提供后台接口与自定义页面声明。"""

    def __init__(self):
        super().__init__(
            theme_name='aurora',
            display_name='Aurora',
            version='1.0.0',
            description='Aurora 主题扩展',
        )
        self._register_admin_blueprint()
        self._register_custom_pages()

    def _register_admin_blueprint(self) -> None:
        blueprint = Blueprint('aurora_theme_extension', __name__, url_prefix='/admin/theme/aurora')

        @blueprint.route('/status')
        @login_required
        def theme_status():
            info = self._resolve_theme_info()
            return jsonify(info)

        self.add_blueprint(blueprint)

    def _register_custom_pages(self) -> None:
        self.add_custom_page({
            'name': 'aurora-timeline',
            'route': '/aurora/timeline',
            'template': 'pages/timeline.html',
            'methods': ['GET'],
            'context': {
                'page_title': 'Aurora 时间线'
            }
        })

    def _resolve_theme_info(self):
        stored_info = theme_manager.get_theme_info(self.theme_name) or {}
        defaults = self.get_info()
        return {
            'name': stored_info.get('display_name', defaults['display_name']),
            'version': stored_info.get('version', defaults['version']),
            'description': stored_info.get('description', defaults['description']),
            'supports_customizer': stored_info.get('supports_customizer', defaults['supports_customizer'])
        }


extension = AuroraThemeExtension()

# ThemeManager 仍会读取这些模块变量来完成蓝图和页面注册
THEME_BLUEPRINTS = extension.get_blueprints()
CUSTOM_PAGES = extension.get_custom_pages()


def register(app, theme_manager, theme):
    """保持与 ThemeManager 的 register 钩子兼容。"""
    return extension.register(app=app, theme_manager=theme_manager, theme=theme)


def create_extension():
    """方便测试或未来直接访问扩展实例的工厂函数。"""
    return extension
