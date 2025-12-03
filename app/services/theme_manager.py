"""主题管理器"""
import importlib
import importlib.util
import inspect
import json
import os
import sys
import traceback
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import object_session
from flask import current_app, render_template_string

from app import db
from app.models.theme import Theme, ThemeHook


class ThemeManager:
    """主题管理器"""

    def __init__(self):
        self.app = None
        self._current_theme = None
        self._current_theme_id = None
        self.theme_hooks = {}
        self.theme_modules: Dict[str, Dict[str, Any]] = {}
        self._registered_theme_blueprints = set()
        self._registered_theme_routes = set()
        self._extension_candidates = ('extensions', 'backend', 'frontend')

    @property
    def current_theme(self) -> Optional[Theme]:
        """Return the active Theme instance, re-attaching it when needed."""
        if self._current_theme is not None:
            if object_session(self._current_theme) is not None:
                return self._current_theme
        if self._current_theme_id is not None:
            # Always fetch a fresh instance bound to the current session.
            self._current_theme = Theme.query.get(self._current_theme_id)
        return self._current_theme

    @current_theme.setter
    def current_theme(self, theme: Optional[Theme]):
        self._current_theme = theme
        self._current_theme_id = theme.id if theme else None

    def init_app(self, app):
        """初始化应用"""
        self.app = app
        app.theme_manager = self

        # 在应用上下文中初始化主题
        with app.app_context():
            self.discover_themes()
            self.load_current_theme()

    def discover_themes(self):
        """发现主题"""
        themes_dir = os.path.join(os.getcwd(), 'themes')

        if not os.path.exists(themes_dir):
            os.makedirs(themes_dir)
            return

        for theme_name in os.listdir(themes_dir):
            theme_path = os.path.join(themes_dir, theme_name)

            # 检查是否为主题目录
            if os.path.isdir(theme_path):
                self._register_theme(theme_name, theme_path)

    def _register_theme(self, theme_name: str, theme_path: str):
        """注册主题到数据库"""
        # 检查主题是否已注册
        existing_theme = Theme.query.filter_by(name=theme_name).first()
        if existing_theme:
            return

        # 读取主题配置文件
        config_file = os.path.join(theme_path, 'theme.json')
        if not os.path.exists(config_file):
            return

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 创建主题记录
            theme = Theme(
                name=theme_name,
                display_name=config.get('display_name', theme_name),
                description=config.get('description', ''),
                version=config.get('version', '1.0.0'),
                author=config.get('author', ''),
                author_website=config.get('author_website', ''),
                license=config.get('license', ''),
                min_noteblog_version=config.get('min_noteblog_version', ''),
                max_noteblog_version=config.get('max_noteblog_version', ''),
                install_path=theme_path,
                is_system=config.get('is_system', False),
                supports_widgets=config.get('supports_widgets', True),
                supports_menus=config.get('supports_menus', True),
                supports_customizer=config.get('supports_customizer', True),
                supports_post_formats=config.get('supports_post_formats', False),
                screenshot=config.get('screenshot', ''),
                demo_url=config.get('demo_url', '')
            )

            # 设置配置模式
            if 'config_schema' in config:
                theme.set_config_schema(config['config_schema'])

            db.session.add(theme)
            db.session.commit()

        except Exception as e:
            current_app.logger.error(f"注册主题 {theme_name} 失败: {e}")

    def load_current_theme(self):
        """加载当前主题"""
        from app.models.setting import SettingManager

        theme_name = SettingManager.get('active_theme', 'default')
        theme = Theme.query.filter_by(name=theme_name).first()

        if theme:
            self.current_theme = theme
            self._load_theme_hooks(theme)
            self._load_theme_extensions(theme)
        else:
            # 如果没有找到主题，尝试加载默认主题
            default_theme = Theme.query.filter_by(name='default').first()
            if default_theme:
                self.current_theme = default_theme
                self._load_theme_hooks(default_theme)
                self._load_theme_extensions(default_theme)

    def _load_theme_hooks(self, theme: Theme):
        """加载主题钩子"""
        # 清空现有钩子
        self.theme_hooks.clear()

        # 从数据库加载钩子
        hooks = ThemeHook.query.filter_by(theme_id=theme.id).all()
        for hook in hooks:
            if hook.hook_name not in self.theme_hooks:
                self.theme_hooks[hook.hook_name] = []

            self.theme_hooks[hook.hook_name].append({
                'callback': hook.callback_function,
                'priority': hook.priority,
                'type': hook.hook_type
            })

        # 尝试加载主题的钩子文件
        hooks_file = os.path.join(theme.install_path, 'hooks.py')
        if os.path.exists(hooks_file):
            try:
                spec = importlib.util.spec_from_file_location("theme_hooks", hooks_file)
                hooks_module = importlib.util.module_from_spec(spec)
                sys.modules["theme_hooks"] = hooks_module
                spec.loader.exec_module(hooks_module)

                # 注册钩子
                if hasattr(hooks_module, 'register_hooks'):
                    hooks_module.register_hooks(self)

            except Exception as e:
                current_app.logger.error(f"加载主题钩子失败: {e}")

    def _load_theme_extensions(self, theme: Theme):
        """加载主题扩展，包括后端/前端模块以及声明式页面。"""
        if not self.app or not theme:
            return

        theme_key = theme.name
        if theme_key not in self.theme_modules:
            self.theme_modules[theme_key] = {}

        for module_name in self._extension_candidates:
            if module_name in self.theme_modules[theme_key]:
                continue
            module = self._load_theme_module(theme, module_name)
            if module:
                self.theme_modules[theme_key][module_name] = module

        self._register_configured_pages(theme)

    def _load_theme_module(self, theme: Theme, module_name: str):
        """按约定导入主题模块（backend/frontend），并尝试注册其蓝图。"""
        module_path = os.path.join(theme.install_path, f'{module_name}.py')
        module_dir = os.path.join(theme.install_path, module_name)
        is_package = False

        if not os.path.exists(module_path):
            package_init = os.path.join(module_dir, '__init__.py')
            if os.path.exists(package_init):
                module_path = package_init
                is_package = True
            else:
                return None

        module_id = f"theme_{theme.name}_{module_name}"
        try:
            spec_kwargs = {}
            if is_package:
                spec_kwargs['submodule_search_locations'] = [os.path.dirname(module_path)]
            spec = importlib.util.spec_from_file_location(module_id, module_path, **spec_kwargs)
            if spec is None or spec.loader is None:
                self.app.logger.error(f"无法为主题 {theme.name} 的 {module_name} 创建导入规范")
                return None

            module = importlib.util.module_from_spec(spec)
            if is_package:
                module.__path__ = [os.path.dirname(module_path)]
                module.__package__ = module_id
            sys.modules[module_id] = module
            spec.loader.exec_module(module)

            self._register_theme_module_blueprints(module, theme, module_name)
            self._register_module_custom_pages(module, theme)

            register_callable = getattr(module, 'register', None)
            if callable(register_callable):
                register_callable(app=self.app, theme_manager=self, theme=theme)

            self.app.logger.info(f"主题 {theme.name} 的 {module_name} 模块加载完成")
            return module
        except Exception as exc:
            self.app.logger.error(f"加载主题 {theme.name} 的 {module_name} 模块失败: {exc}")
            self.app.logger.debug(traceback.format_exc())
            return None

    def _register_theme_module_blueprints(self, module, theme: Theme, module_name: str):
        """发现并注册主题模块提供的蓝图。"""
        if not self.app:
            return

        blueprint_candidates = []
        if hasattr(module, 'THEME_BLUEPRINTS'):
            blueprint_candidates.extend(getattr(module, 'THEME_BLUEPRINTS') or [])

        for _, obj in inspect.getmembers(module):
            if self._looks_like_blueprint(obj):
                blueprint_candidates.append(obj)

        if not blueprint_candidates:
            return

        with self.app.app_context():
            for blueprint in blueprint_candidates:
                blueprint_key = f"{theme.name}:{module_name}:{getattr(blueprint, 'name', id(blueprint))}"
                if blueprint_key in self._registered_theme_blueprints:
                    continue
                try:
                    self.app.register_blueprint(blueprint)
                    self._registered_theme_blueprints.add(blueprint_key)
                    self.app.logger.info(
                        f"主题 {theme.name} 注册蓝图 {blueprint.name} (模块: {module_name})"
                    )
                except Exception as exc:
                    self.app.logger.error(
                        f"注册主题 {theme.name} 蓝图 {getattr(blueprint, 'name', 'unknown')} 失败: {exc}"
                    )

    def _register_module_custom_pages(self, module, theme: Theme):
        """从主题模块中提取声明式页面。"""
        pages_source = []

        if hasattr(module, 'CUSTOM_PAGES'):
            pages_source = getattr(module, 'CUSTOM_PAGES') or []
        elif hasattr(module, 'get_custom_pages'):
            getter = getattr(module, 'get_custom_pages')
            try:
                pages_source = getter(theme=theme, app=self.app, theme_manager=self)
            except TypeError:
                pages_source = getter()
        
        if not pages_source:
            return

        if not isinstance(pages_source, list):
            self.app.logger.warning(f"主题 {theme.name} 模块 {module.__name__} 的 custom_pages 需要是列表")
            return

        for page in pages_source:
            if not isinstance(page, dict):
                continue
            route = page.get('route')
            template_name = page.get('template')
            if not route or not template_name:
                continue
            endpoint = page.get('endpoint') or page.get('name')
            methods = page.get('methods') or ['GET']
            context_payload = page.get('context') or {}
            self.register_theme_page(
                route,
                template_name,
                endpoint=endpoint,
                methods=methods,
                theme=theme,
                extra_context=context_payload
            )

    @staticmethod
    def _looks_like_blueprint(obj) -> bool:
        """粗略判断对象是否为 Flask Blueprint 实例。"""
        try:
            return all(
                hasattr(obj, attr)
                for attr in ('register', 'name', 'import_name')
            )
        except RuntimeError:
            return False

    def _register_configured_pages(self, theme: Theme):
        """读取 theme.json 的 custom_pages 配置并注册路由。"""
        config_path = os.path.join(theme.install_path, 'theme.json')
        if not os.path.exists(config_path):
            return

        try:
            with open(config_path, 'r', encoding='utf-8') as config_file:
                config = json.load(config_file)
        except Exception as exc:
            if self.app:
                self.app.logger.error(f"读取主题 {theme.name} 配置失败: {exc}")
            return

        pages = config.get('custom_pages') or []
        if not isinstance(pages, list):
            if self.app:
                self.app.logger.warning(f"主题 {theme.name} 的 custom_pages 必须为数组")
            return

        for page in pages:
            if not isinstance(page, dict):
                continue
            route = page.get('route')
            template_name = page.get('template')
            if not route or not template_name:
                continue
            endpoint = page.get('endpoint') or page.get('name')
            methods = page.get('methods') or ['GET']
            context_payload = page.get('context') or {}
            self.register_theme_page(
                route,
                template_name,
                endpoint=endpoint,
                methods=methods,
                theme=theme,
                extra_context=context_payload
            )

    def register_theme_page(
        self,
        route: str,
        template_name: str,
        *,
        endpoint: Optional[str] = None,
        methods: Optional[List[str]] = None,
        theme: Optional[Theme] = None,
        extra_context: Optional[Dict[str, Any]] = None
    ):
        """注册一个简单的主题页面路由，自动渲染指定模板。"""
        if not self.app:
            raise RuntimeError('ThemeManager 尚未绑定到 Flask 应用')

        theme = theme or self.current_theme
        if not theme:
            raise RuntimeError('当前没有激活的主题')

        if not route.startswith('/'):
            route = f'/{route}'

        safe_template = template_name.replace('/', '_').replace('.', '_')
        endpoint = endpoint or f"{theme.name}_page_{safe_template}"
        methods = methods or ['GET']
        extra_context = extra_context or {}
        route_key = f"{theme.name}:{endpoint}"

        if route_key in self._registered_theme_routes:
            return

        manager = self
        expected_theme_name = theme.name

        def _view(**view_kwargs):
            from flask import abort

            if not manager.current_theme or manager.current_theme.name != expected_theme_name:
                abort(404)
            context = dict(extra_context)
            if view_kwargs:
                context.update(view_kwargs)
            return manager.render_template(template_name, **context)

        _view.__name__ = endpoint.replace('.', '_')

        with self.app.app_context():
            self.app.add_url_rule(route, endpoint, _view, methods=methods)

        self._registered_theme_routes.add(route_key)
        self.app.logger.info(
            f"主题 {theme.name} 注册页面 {route} -> {template_name} (endpoint: {endpoint})"
        )

    def register_theme_hook(self, hook_name: str, callback: str,
                            hook_type: str = 'template', priority: int = 10):
        """注册主题钩子"""
        if hook_name not in self.theme_hooks:
            self.theme_hooks[hook_name] = []

        self.theme_hooks[hook_name].append({
            'callback': callback,
            'priority': priority,
            'type': hook_type
        })

        # 按优先级排序
        self.theme_hooks[hook_name].sort(key=lambda x: x['priority'])

        # 保存到数据库
        if self.current_theme:
            hook = ThemeHook(
                theme_id=self.current_theme.id,
                hook_name=hook_name,
                hook_type=hook_type,
                callback_function=callback,
                priority=priority
            )
            db.session.add(hook)
            db.session.commit()

    def _url_for_helper(self, endpoint, **values):
        """url_for函数的辅助实现"""
        try:
            from flask import url_for
            return url_for(endpoint, **values)
        except Exception:
            # 如果url_for不可用，返回简单的路径映射
            url_mappings = {
                'main.index': '/',
                'main.login': '/auth/login',
                'main.register': '/auth/register',
                'main.logout': '/auth/logout',
                'main.profile': '/auth/profile',
                'main.edit_profile': '/auth/edit',
                'main.change_password': '/auth/change-password',
                'main.forgot_password': '/auth/forgot-password',
                'main.search': '/search',
                'main.post': '/post',
                'admin.index': '/admin',
                'admin.posts': '/admin/posts',
                'admin.new_post': '/admin/posts/new',
                'admin.edit_post': '/admin/posts/edit',
                'admin.categories': '/admin/categories',
                'admin.tags': '/admin/tags',
                'admin.comments': '/admin/comments',
                'admin.users': '/admin/users',
                'admin.settings': '/admin/settings',
                'admin.themes': '/admin/themes',
                'admin.plugins': '/admin/plugins',
            }

            if endpoint in url_mappings:
                base_url = url_mappings[endpoint]
                # 处理带参数的URL
                if values:
                    if endpoint == 'main.post' and 'id' in values:
                        return f"{base_url}/{values['id']}"
                    elif endpoint == 'admin.edit_post' and 'id' in values:
                        return f"{base_url}/{values['id']}"
                return base_url

            # 默认返回endpoint作为路径
            return f"/{endpoint.replace('.', '/')}"

    def get_theme_hooks(self, hook_name: str):
        """获取主题钩子"""
        hooks = []
        if hook_name in self.theme_hooks:
            for hook_info in self.theme_hooks[hook_name]:
                if hook_info.get('type') == 'template':
                    try:
                        hooks.append(hook_info['callback'])
                    except Exception as e:
                        current_app.logger.error(f"获取主题钩子 {hook_name} 失败: {e}")

        return hooks

    def render_template(self, template_name: str, **context):
        """渲染主题模板"""
        if not self.current_theme:
            # 如果没有主题，使用默认模板
            return render_template_string("<h1>未找到主题</h1>", **context)

        template_path = os.path.join(self.current_theme.install_path, 'templates', template_name)

        # 如果当前主题没有该模板，尝试回退到default主题
        if not os.path.exists(template_path):
            default_theme = Theme.query.filter_by(name='default').first()
            if default_theme and default_theme.name != self.current_theme.name:
                default_template_path = os.path.join(default_theme.install_path, 'templates', template_name)
                if os.path.exists(default_template_path):
                    template_path = default_template_path
                    current_app.logger.info(f"主题 {self.current_theme.name} 缺少模板 {template_name}，回退到default主题")

        # 在渲染前补充常用上下文变量，避免主题模板因缺少变量而报错
        try:
            from app.models.post import Post, Category, Tag
            from app.models.setting import SettingManager
            from flask_login import current_user as flask_current_user
        except Exception:
            Post = Category = Tag = None
            SettingManager = None
            flask_current_user = None

        if 'recent_posts' not in context:
            try:
                if Post is not None:
                    context['recent_posts'] = Post.query.filter_by(status='published').order_by(
                        Post.published_at.desc()
                    ).limit(5).all()
                else:
                    context['recent_posts'] = []
            except Exception:
                context['recent_posts'] = []

        if 'categories' not in context:
            try:
                if Category is not None:
                    context['categories'] = Category.query.filter_by(is_active=True).all()
                else:
                    context['categories'] = []
            except Exception:
                context['categories'] = []

        if 'tags' not in context:
            try:
                if Tag is not None:
                    context['tags'] = Tag.query.all()
                else:
                    context['tags'] = []
            except Exception:
                context['tags'] = []

        if 'site_title' not in context:
            try:
                context['site_title'] = SettingManager.get('site_title', 'Noteblog') if SettingManager else None
            except Exception:
                context['site_title'] = None

        if 'page_title' not in context:
            try:
                base_title = context.get('site_title')
                if not base_title:
                    base_title = SettingManager.get('site_title', 'Noteblog') if SettingManager else 'Noteblog'
                context['page_title'] = base_title
            except Exception:
                context['page_title'] = context.get('site_title') or 'Noteblog'

        if 'site_description' not in context:
            try:
                context['site_description'] = SettingManager.get('site_description', '') if SettingManager else ''
            except Exception:
                context['site_description'] = ''

        if 'allow_comments' not in context:
            try:
                context['allow_comments'] = SettingManager.get('allow_comments', True) if SettingManager else True
            except Exception:
                context['allow_comments'] = True

        if 'current_user' not in context:
            context['current_user'] = flask_current_user

        # 应用全局模板上下文过滤器
        from app.services.plugin_manager import plugin_manager
        context = plugin_manager.apply_filters('template_context', context)

        if os.path.exists(template_path):
            # 使用 Jinja2 渲染模板
            from jinja2 import Environment, FileSystemLoader

            if template_path.startswith(os.path.join(self.current_theme.install_path, 'templates')):
                template_dir = os.path.join(self.current_theme.install_path, 'templates')
            else:
                default_theme = Theme.query.filter_by(name='default').first()
                if default_theme:
                    template_dir = os.path.join(default_theme.install_path, 'templates')
                else:
                    template_dir = os.path.join(self.current_theme.install_path, 'templates')

            env = Environment(loader=FileSystemLoader(template_dir))

            env.globals['get_theme_hooks'] = self.get_theme_hooks
            env.globals['get_theme_config'] = self.get_theme_config
            env.globals['url_for'] = self._url_for_helper

            try:
                from flask import get_flashed_messages, request, session, g

                env.globals['get_flashed_messages'] = get_flashed_messages
                env.globals['request'] = request
                env.globals['session'] = session
                env.globals['g'] = g
                env.globals['config'] = current_app.config
            except Exception:
                pass

            try:
                template = env.get_template(template_name)
                return template.render(**context)
            except Exception as e:
                current_app.logger.error(f"渲染模板 {template_name} 失败: {e}")
                return f"<h1>模板渲染错误</h1><p>{e}</p>"
        else:
            return f"<h1>模板未找到</h1><p>{template_path}</p>"

    def get_theme_config(self):
        """获取主题配置"""
        if self.current_theme:
            return self.current_theme.get_config()
        return {}

    def set_theme_config(self, config_dict: Dict):
        """设置主题配置"""
        if self.current_theme:
            self.current_theme.set_config(config_dict)

    def get_theme_info(self, theme_name: str = None):
        """获取主题信息"""
        if theme_name:
            theme = Theme.query.filter_by(name=theme_name).first()
        else:
            theme = self.current_theme

        if theme:
            return theme.to_dict()
        return None

    def get_all_themes(self):
        """获取所有主题"""
        themes = Theme.query.all()
        return [theme.to_dict() for theme in themes]

    def activate_theme(self, theme_name: str):
        """激活主题"""
        theme = Theme.query.filter_by(name=theme_name).first()
        if theme:
            theme.activate()
            self.current_theme = theme
            self._load_theme_hooks(theme)
            self._load_theme_extensions(theme)

            from app.models.setting import SettingManager
            SettingManager.set('active_theme', theme_name)

            return True
        return False

    def get_current_theme(self):
        """获取当前主题"""
        return self.current_theme

    def get_theme_static_url(self, static_file: str):
        """获取主题静态文件URL"""
        if self.current_theme:
            return f"/themes/{self.current_theme.name}/static/{static_file}"
        return f"/themes/default/static/{static_file}"

    def get_theme_template_path(self, template_name: str):
        """获取主题模板路径"""
        if self.current_theme:
            return os.path.join(self.current_theme.install_path, 'templates', template_name)
        return None

    def theme_exists(self, theme_name: str):
        """检查主题是否存在"""
        theme = Theme.query.filter_by(name=theme_name).first()
        return theme is not None

    def create_theme(self, theme_name: str, theme_config: Dict):
        """创建新主题"""
        themes_dir = os.path.join(os.getcwd(), 'themes')
        theme_path = os.path.join(themes_dir, theme_name)

        if os.path.exists(theme_path):
            return False, "主题已存在"

        try:
            # 创建主题目录结构
            os.makedirs(theme_path)
            os.makedirs(os.path.join(theme_path, 'templates'))
            os.makedirs(os.path.join(theme_path, 'templates', 'pages'))
            os.makedirs(os.path.join(theme_path, 'static'))
            os.makedirs(os.path.join(theme_path, 'static', 'css'))
            os.makedirs(os.path.join(theme_path, 'static', 'js'))
            os.makedirs(os.path.join(theme_path, 'static', 'images'))

            # 创建主题配置文件
            config_file = os.path.join(theme_path, 'theme.json')
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(theme_config, f, ensure_ascii=False, indent=2)

            # 创建基础模板文件
            base_template = """<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>{% block title %}{{ site_title or 'Noteblog' }}{% endblock %}</title>
    {% block head %}{% endblock %}
</head>
<body>
    {% block header %}{% endblock %}

    <main>
        {% block content %}{% endblock %}
    </main>

    {% block footer %}{% endblock %}

    {% block scripts %}{% endblock %}
</body>
</html>"""

            with open(os.path.join(theme_path, 'templates', 'base.html'), 'w', encoding='utf-8') as f:
                f.write(base_template)

            # 注册主题
            self._register_theme(theme_name, theme_path)

            return True, "主题创建成功"

        except Exception as e:
            return False, f"创建主题失败: {e}"


class ThemeExtensionBase:
    """Simple helper so theme extensions can mirror the plugin-style API."""

    def __init__(
        self,
        theme_name: str,
        *,
        display_name: Optional[str] = None,
        version: str = "1.0.0",
        description: str = "",
        supports_customizer: bool = True,
    ):
        self.theme_name = theme_name
        self.display_name = display_name or theme_name.title()
        self.version = version
        self.description = description
        self.supports_customizer = supports_customizer
        self._blueprints: List[Any] = []
        self._custom_pages: List[Dict[str, Any]] = []

    def get_info(self) -> Dict[str, Any]:
        """Expose a consistent info payload for admin/status endpoints."""
        return {
            'name': self.theme_name,
            'display_name': self.display_name,
            'version': self.version,
            'description': self.description,
            'supports_customizer': self.supports_customizer,
        }

    def add_blueprint(self, blueprint: Any) -> None:
        if blueprint:
            self._blueprints.append(blueprint)

    def add_custom_page(self, page_definition: Dict[str, Any]) -> None:
        if page_definition:
            self._custom_pages.append(page_definition)

    def get_blueprints(self) -> List[Any]:
        return list(self._blueprints)

    def get_custom_pages(self) -> List[Dict[str, Any]]:
        return list(self._custom_pages)

    def register(self, app, theme_manager, theme) -> None:  # pragma: no cover - optional hook
        """Allow subclasses to perform imperative setup when ThemeManager loads them."""


# 创建全局主题管理器实例
theme_manager = ThemeManager()
