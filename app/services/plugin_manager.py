"""
插件管理器
"""
import os
import sys
import importlib
import importlib.util
import inspect
from typing import Dict, List, Any, Callable
from flask import current_app
from app import db
from app.models.plugin import Plugin, PluginHook

class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        self.app = None
        self.hooks = {}  # 钩子注册表 {hook_name: [hook_info, ...]}
        self.plugins = {}  # 已加载的插件 {plugin_name: plugin_instance}
        self.plugin_modules = {}  # 插件模块 {plugin_name: module}
        
    def init_app(self, app):
        """初始化应用"""
        self.app = app
        app.plugin_manager = self
        
        # 在应用上下文中初始化插件
        with app.app_context():
            self.discover_plugins()
            self.load_active_plugins()
    
    def discover_plugins(self):
        """发现插件（仅扫描，不自动注册）"""
        plugins_dir = os.path.join(os.getcwd(), 'plugins')
        
        if not os.path.exists(plugins_dir):
            os.makedirs(plugins_dir)
            return
        
        # 只扫描插件目录，不自动注册到数据库
        # 插件注册将在用户点击安装时进行
        pass
    
    def _register_plugin(self, plugin_name: str, plugin_path: str):
        """注册插件到数据库"""
        # 检查插件是否已注册
        existing_plugin = Plugin.query.filter_by(name=plugin_name).first()
        if existing_plugin:
            return
        
        # 读取插件配置文件
        config_file = os.path.join(plugin_path, 'plugin.json')
        if not os.path.exists(config_file):
            return
        
        try:
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 创建插件记录
            plugin = Plugin(
                name=plugin_name,
                display_name=config.get('display_name', plugin_name),
                description=config.get('description', ''),
                version=config.get('version', '1.0.0'),
                author=config.get('author', ''),
                author_website=config.get('author_website', ''),
                license=config.get('license', ''),
                min_noteblog_version=config.get('min_noteblog_version', ''),
                max_noteblog_version=config.get('max_noteblog_version', ''),
                install_path=plugin_path,
                is_system=config.get('is_system', False)
            )
            
            db.session.add(plugin)
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"注册插件 {plugin_name} 失败: {e}")
    
    def load_active_plugins(self):
        """加载激活的插件"""
        active_plugins = Plugin.query.filter_by(is_active=True).all()
        
        for plugin in active_plugins:
            try:
                self._load_plugin(plugin)
            except Exception as e:
                current_app.logger.error(f"加载插件 {plugin.name} 失败: {e}")
    
    def _load_plugin(self, plugin: Plugin):
        """加载单个插件"""
        plugin_path = plugin.install_path
        
        # 确保插件路径存在
        if not os.path.exists(plugin_path):
            current_app.logger.error(f"插件路径不存在: {plugin_path}")
            return
        
        # 导入插件模块
        module_name = plugin.name
        try:
            # 使用插件目录作为包路径进行导入
            # 这样可以正确处理相对导入
            plugins_dir = os.path.join(os.getcwd(), 'plugins')
            if plugins_dir not in sys.path:
                sys.path.insert(0, plugins_dir)
            
            # 导入插件模块
            spec = importlib.util.spec_from_file_location(
                module_name, 
                os.path.join(plugin_path, '__init__.py')
            )
            if spec is None:
                current_app.logger.error(f"无法为插件 {plugin.name} 创建模块规范")
                return
                
            module = importlib.util.module_from_spec(spec)
            
            # 设置模块的 __package__ 属性以支持相对导入
            module.__package__ = module_name
            
            spec.loader.exec_module(module)
            self.plugin_modules[plugin.name] = module
            
            # 查找插件类
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    hasattr(obj, '__module__') and 
                    obj.__module__ == module_name and
                    name != 'PluginBase'):
                    plugin_class = obj
                    break
            
            if plugin_class:
                # 实例化插件
                plugin_instance = plugin_class()
                self.plugins[plugin.name] = plugin_instance
                
                # 注册插件的钩子
                if hasattr(plugin_instance, 'register_hooks'):
                    plugin_instance.register_hooks()
                
                # 注册插件的蓝图
                self._register_plugin_blueprints(module, plugin.name)
                
                current_app.logger.info(f"插件 {plugin.name} 加载成功")
            else:
                current_app.logger.warning(f"插件 {plugin.name} 中未找到插件类")
                
        except Exception as e:
            current_app.logger.error(f"导入插件 {plugin.name} 失败: {e}")
            import traceback
            current_app.logger.error(f"详细错误信息: {traceback.format_exc()}")
    
    def _register_plugin_blueprints(self, module, plugin_name: str):
        """注册插件的蓝图"""
        try:
            # 在应用上下文中注册蓝图
            with self.app.app_context():
                # 查找模块中的所有蓝图
                for name, obj in inspect.getmembers(module):
                    # 检查是否是蓝图实例（friend_links插件使用这种方式）
                    # 使用更安全的方式检查蓝图属性，避免触发请求上下文
                    is_blueprint_instance = False
                    try:
                        if (hasattr(obj, 'register') and 
                            hasattr(obj, 'import_name') and
                            hasattr(obj, 'deferred_functions')):  # Blueprint特有属性
                            is_blueprint_instance = True
                    except RuntimeError:
                        # 如果检查属性时出现上下文错误，跳过这个对象
                        continue
                    
                    if is_blueprint_instance:
                        # 这是一个蓝图实例
                        blueprint = obj
                        # 延迟注册蓝图，避免在注册时触发路由函数中的current_app访问
                        try:
                            self.app.register_blueprint(blueprint)
                            self.app.logger.info(f"插件 {plugin_name} 蓝图 {name} 注册成功")
                        except Exception as register_error:
                            self.app.logger.error(f"注册蓝图 {name} 时出错: {register_error}")
                            # 继续尝试其他蓝图，不中断整个注册过程
                            continue
                    
                    # 检查是否是蓝图类
                    elif inspect.isclass(obj):
                        try:
                            if (hasattr(obj, 'register') and 
                                hasattr(obj, 'name') and 
                                hasattr(obj, 'url_prefix')):
                                # 这是一个Flask Blueprint类
                                blueprint = obj()
                                if hasattr(blueprint, 'register'):
                                    self.app.register_blueprint(blueprint)
                                    self.app.logger.info(f"插件 {plugin_name} 蓝图类 {name} 注册成功")
                        except RuntimeError:
                            # 如果检查属性时出现上下文错误，跳过这个类
                            continue
                        except Exception as register_error:
                            self.app.logger.error(f"注册蓝图类 {name} 时出错: {register_error}")
                            continue
                        
        except Exception as e:
            self.app.logger.error(f"注册插件 {plugin_name} 蓝图失败: {e}")
            import traceback
            self.app.logger.error(f"详细错误信息: {traceback.format_exc()}")
    
    def register_hook(self, hook_name: str, callback: Callable, 
                     priority: int = 10, accepted_args: int = 1, 
                     plugin_name: str = None):
        """注册钩子"""
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        
        hook_info = {
            'callback': callback,
            'priority': priority,
            'accepted_args': accepted_args,
            'plugin_name': plugin_name
        }
        
        self.hooks[hook_name].append(hook_info)
        
        # 按优先级排序
        self.hooks[hook_name].sort(key=lambda x: x['priority'])
        
        # 如果有插件名，保存到数据库
        if plugin_name:
            plugin = Plugin.query.filter_by(name=plugin_name).first()
            if plugin:
                hook = PluginHook(
                    plugin_id=plugin.id,
                    hook_name=hook_name,
                    hook_type='action',  # 默认为 action 类型
                    callback_function=callback.__name__,
                    priority=priority,
                    accepted_args=accepted_args
                )
                db.session.add(hook)
                db.session.commit()
    
    def register_filter(self, filter_name: str, callback: Callable,
                       priority: int = 10, accepted_args: int = 1,
                       plugin_name: str = None):
        """注册过滤器"""
        if filter_name not in self.hooks:
            self.hooks[filter_name] = []
        
        hook_info = {
            'callback': callback,
            'priority': priority,
            'accepted_args': accepted_args,
            'plugin_name': plugin_name,
            'type': 'filter'
        }
        
        self.hooks[filter_name].append(hook_info)
        
        # 按优先级排序
        self.hooks[filter_name].sort(key=lambda x: x['priority'])
        
        # 保存到数据库
        if plugin_name:
            plugin = Plugin.query.filter_by(name=plugin_name).first()
            if plugin:
                hook = PluginHook(
                    plugin_id=plugin.id,
                    hook_name=filter_name,
                    hook_type='filter',
                    callback_function=callback.__name__,
                    priority=priority,
                    accepted_args=accepted_args
                )
                db.session.add(hook)
                db.session.commit()
    
    def register_template_hook(self, hook_name: str, callback: Callable,
                              priority: int = 10, plugin_name: str = None):
        """注册模板钩子"""
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        
        hook_info = {
            'callback': callback,
            'priority': priority,
            'accepted_args': 0,
            'plugin_name': plugin_name,
            'type': 'template'
        }
        
        self.hooks[hook_name].append(hook_info)
        
        # 按优先级排序
        self.hooks[hook_name].sort(key=lambda x: x['priority'])
        
        # 保存到数据库
        if plugin_name:
            plugin = Plugin.query.filter_by(name=plugin_name).first()
            if plugin:
                hook = PluginHook(
                    plugin_id=plugin.id,
                    hook_name=hook_name,
                    hook_type='template',
                    callback_function=callback.__name__,
                    priority=priority,
                    accepted_args=0
                )
                db.session.add(hook)
                db.session.commit()
    
    def do_action(self, hook_name: str, *args, **kwargs):
        """执行动作钩子"""
        if hook_name in self.hooks:
            for hook_info in self.hooks[hook_name]:
                try:
                    callback = hook_info['callback']
                    accepted_args = hook_info['accepted_args']
                    
                    # 限制参数数量
                    if len(args) > accepted_args:
                        args = args[:accepted_args]
                    
                    callback(*args, **kwargs)
                except Exception as e:
                    plugin_name = hook_info.get('plugin_name', 'unknown')
                    current_app.logger.error(f"执行钩子 {hook_name} (插件: {plugin_name}) 失败: {e}")
    
    def apply_filters(self, filter_name: str, value: Any, *args, **kwargs):
        """应用过滤器"""
        if filter_name in self.hooks:
            for hook_info in self.hooks[filter_name]:
                if hook_info.get('type') == 'filter':
                    try:
                        callback = hook_info['callback']
                        accepted_args = hook_info['accepted_args']
                        
                        # 限制参数数量，第一个参数是值
                        filter_args = [value] + list(args[:accepted_args-1])
                        value = callback(*filter_args, **kwargs)
                    except Exception as e:
                        plugin_name = hook_info.get('plugin_name', 'unknown')
                        current_app.logger.error(f"应用过滤器 {filter_name} (插件: {plugin_name}) 失败: {e}")
        
        return value
    
    def get_template_hooks(self, hook_name: str):
        """获取模板钩子"""
        hooks = []
        if hook_name in self.hooks:
            for hook_info in self.hooks[hook_name]:
                if hook_info.get('type') == 'template':
                    try:
                        callback = hook_info['callback']
                        result = callback()
                        if result:
                            hooks.append(result)
                    except Exception as e:
                        plugin_name = hook_info.get('plugin_name', 'unknown')
                        current_app.logger.error(f"获取模板钩子 {hook_name} (插件: {plugin_name}) 失败: {e}")
        
        return hooks
    
    def install_plugin(self, plugin_name: str):
        """安装插件"""
        try:
            # 先检查插件是否已存在
            plugin = Plugin.query.filter_by(name=plugin_name).first()
            if plugin:
                current_app.logger.error(f"插件 {plugin_name} 已存在")
                return False
            
            # 注册插件到数据库
            plugins_dir = os.path.join(os.getcwd(), 'plugins')
            plugin_path = os.path.join(plugins_dir, plugin_name)
            
            if not os.path.exists(plugin_path):
                current_app.logger.error(f"插件目录 {plugin_path} 不存在")
                return False
            
            # 调用注册方法
            self._register_plugin(plugin_name, plugin_path)
            
            # 重新获取插件对象
            plugin = Plugin.query.filter_by(name=plugin_name).first()
            if not plugin:
                current_app.logger.error(f"插件 {plugin_name} 注册失败")
                return False
            
            # 加载插件
            self._load_plugin(plugin)
            plugin_instance = self.plugins.get(plugin_name)
            
            if plugin_instance and hasattr(plugin_instance, 'install'):
                # 调用插件的install方法
                result = plugin_instance.install()
                if result:
                    current_app.logger.info(f"插件 {plugin_name} 安装成功")
                    return True
                else:
                    current_app.logger.error(f"插件 {plugin_name} 安装失败")
                    return False
            else:
                current_app.logger.error(f"插件 {plugin_name} 没有install方法")
                return False
                
        except Exception as e:
            current_app.logger.error(f"安装插件 {plugin_name} 失败: {e}")
            return False
    
    def activate_plugin(self, plugin_name: str):
        """激活插件"""
        plugin = Plugin.query.filter_by(name=plugin_name).first()
        if plugin:
            plugin.activate()
            self._load_plugin(plugin)
            return True
        return False
    
    def deactivate_plugin(self, plugin_name: str):
        """停用插件"""
        plugin = Plugin.query.filter_by(name=plugin_name).first()
        if plugin:
            plugin.deactivate()
            
            # 从内存中卸载插件
            if plugin_name in self.plugins:
                del self.plugins[plugin_name]
            
            if plugin_name in self.plugin_modules:
                del self.plugin_modules[plugin_name]
            
            # 移除插件的钩子
            hooks_to_remove = []
            for hook_name, hook_list in self.hooks.items():
                self.hooks[hook_name] = [
                    hook for hook in hook_list 
                    if hook.get('plugin_name') != plugin_name
                ]
            
            return True
        return False
    
    def get_plugin_info(self, plugin_name: str):
        """获取插件信息"""
        plugin = Plugin.query.filter_by(name=plugin_name).first()
        if plugin:
            return plugin.to_dict()
        return None
    
    def get_all_plugins(self):
        """获取所有插件"""
        plugins = Plugin.query.all()
        return [plugin.to_dict() for plugin in plugins]
    
    def get_active_plugins(self):
        """获取激活的插件"""
        plugins = Plugin.query.filter_by(is_active=True).all()
        return [plugin.to_dict() for plugin in plugins]

# 创建全局插件管理器实例
plugin_manager = PluginManager()

# 基础插件类
class PluginBase:
    """插件基类"""
    
    def __init__(self):
        self.name = ""
        self.version = "1.0.0"
        self.description = ""
        self.author = ""
    
    def register_hooks(self):
        """注册钩子，子类需要重写此方法"""
        pass
    
    def activate(self):
        """插件激活时调用"""
        pass
    
    def deactivate(self):
        """插件停用时调用"""
        pass
    
    def get_config(self):
        """获取插件配置"""
        from app.models.plugin import Plugin
        plugin = Plugin.query.filter_by(name=self.name).first()
        if plugin:
            return plugin.get_config()
        return {}
    
    def set_config(self, config_dict):
        """设置插件配置"""
        from app.models.plugin import Plugin
        plugin = Plugin.query.filter_by(name=self.name).first()
        if plugin:
            plugin.set_config(config_dict)
