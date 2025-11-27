"""Serenity 主题扩展入口：使用插件化方式暴露蓝图与自定义页面。"""
from flask import Blueprint, jsonify
from flask_login import login_required

from app.services.theme_manager import ThemeExtensionBase, theme_manager


class SerenityThemeExtension(ThemeExtensionBase):
    """Serenity 主题扩展实现。"""

    def __init__(self):
        super().__init__(
            theme_name='serenity',
            display_name='Serenity',
            version='1.0.0',
            description='Serenity 主题扩展',
        )
        self._register_admin_blueprint()
        self._register_custom_pages()

    def _register_admin_blueprint(self) -> None:
        blueprint = Blueprint('serenity_theme_extension', __name__, url_prefix='/admin/theme/serenity')

        @blueprint.route('/status')
        @login_required
        def theme_status():
            return jsonify(self._resolve_theme_info())

        self.add_blueprint(blueprint)

    def _register_custom_pages(self) -> None:
        self.add_custom_page({
            'name': 'serenity-timeline',
            'route': '/serenity/timeline',
            'template': 'pages/timeline.html',
            'methods': ['GET'],
            'context': {
                'page_title': 'Serenity 时间线',
                'page_description': '用一页的篇幅，记录值得记住的每一次发布',
            }
        })

    def _resolve_theme_info(self):
        stored_info = theme_manager.get_theme_info(self.theme_name) or {}
        defaults = self.get_info()
        return {
            'name': stored_info.get('display_name', defaults['display_name']),
            'version': stored_info.get('version', defaults['version']),
            'description': stored_info.get('description', defaults['description']),
            'supports_customizer': stored_info.get('supports_customizer', defaults['supports_customizer']),
        }


extension = SerenityThemeExtension()

THEME_BLUEPRINTS = extension.get_blueprints()
CUSTOM_PAGES = extension.get_custom_pages()


def register(app, theme_manager, theme):
    return extension.register(app=app, theme_manager=theme_manager, theme=theme)


def create_extension():
    return extension
