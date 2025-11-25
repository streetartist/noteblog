"""
主题管理器
"""
import os
import json
from typing import Dict, List, Any, Optional
from flask import current_app, render_template_string
from app import db
from app.models.theme import Theme, ThemeHook

class ThemeManager:
    """主题管理器"""
    
    def __init__(self):
        self.app = None
        self.current_theme = None
        self.theme_hooks = {}
        
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
        else:
            # 如果没有找到主题，尝试加载默认主题
            default_theme = Theme.query.filter_by(name='default').first()
            if default_theme:
                self.current_theme = default_theme
                self._load_theme_hooks(default_theme)
    
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
                import sys
                import importlib.util
                
                spec = importlib.util.spec_from_file_location("theme_hooks", hooks_file)
                hooks_module = importlib.util.module_from_spec(spec)
                sys.modules["theme_hooks"] = hooks_module
                spec.loader.exec_module(hooks_module)
                
                # 注册钩子
                if hasattr(hooks_module, 'register_hooks'):
                    hooks_module.register_hooks(self)
                    
            except Exception as e:
                current_app.logger.error(f"加载主题钩子失败: {e}")
    
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
                    # 可以添加更多特殊情况
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
                        # 这里可以执行回调函数或返回回调信息
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
        
        # 在渲染前补充常用上下文变量，避免主题模板因缺少变量而报错
        try:
            from app.models.post import Post, Category, Tag
            from app.models.setting import SettingManager
            from flask_login import current_user as flask_current_user
        except Exception:
            Post = Category = Tag = None
            SettingManager = None
            flask_current_user = None

        # recent_posts: 最新文章列表（前5篇）
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

        # categories & tags
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

        # site title/description
        if 'site_title' not in context:
            try:
                context['site_title'] = SettingManager.get('site_title', 'Noteblog') if SettingManager else None
            except Exception:
                context['site_title'] = None

        if 'site_description' not in context:
            try:
                context['site_description'] = SettingManager.get('site_description', '') if SettingManager else ''
            except Exception:
                context['site_description'] = ''

        if 'current_user' not in context:
            context['current_user'] = flask_current_user

        if os.path.exists(template_path):
            # 使用 Jinja2 渲染模板
            from jinja2 import Environment, FileSystemLoader
            
            template_dir = os.path.join(self.current_theme.install_path, 'templates')
            env = Environment(loader=FileSystemLoader(template_dir))
            
            # 添加全局函数和常用 Flask 上下文（使主题模板能访问 flash/messages/request/session/g 等）
            env.globals['get_theme_hooks'] = self.get_theme_hooks
            env.globals['get_theme_config'] = self.get_theme_config
            env.globals['url_for'] = self._url_for_helper

            # 将 Flask 的常用模板帮助函数注入到 Jinja 环境中，避免使用原生 Jinja2 渲染时找不到这些名称
            try:
                from flask import get_flashed_messages, request, session, g

                env.globals['get_flashed_messages'] = get_flashed_messages
                env.globals['request'] = request
                env.globals['session'] = session
                env.globals['g'] = g
                # 提供 config 访问（只读视图）
                env.globals['config'] = current_app.config
            except Exception:
                # 在极少数环境中这些对象可能不可用，保持渲染不中断
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
            
            # 更新设置
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
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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

# 创建全局主题管理器实例
theme_manager = ThemeManager()
