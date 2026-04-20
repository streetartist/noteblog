"""
友链插件
在侧边栏显示友链
"""
import os
from flask import current_app, render_template, Blueprint, request, jsonify
from app.services.plugin_manager import PluginBase
from .models import FriendLink


class FriendLinksPlugin(PluginBase):
    """友链插件类"""
    
    def __init__(self):
        super().__init__()
        self.name = 'friend_links'
        self.version = '1.0.0'
        self.description = '在侧边栏显示友链'
        self.author = 'Noteblog'
        
    def get_info(self):
        """返回插件信息"""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'hooks': self.get_registered_hooks(),
            'filters': self.get_registered_filters()
        }
    
    def install(self):
        """插件安装时的操作"""
        current_app.logger.info(f"Installing {self.name} plugin")
        
        # 创建数据库表
        try:
            from app import db
            db.create_all()
            current_app.logger.info("Friend links table created successfully")
        except Exception as e:
            current_app.logger.error(f"Failed to create friend links table: {e}")
            return False
        
        # 添加一些默认友链
        if FriendLink.query.count() == 0:
            default_links = [
                {
                    'name': 'GitHub',
                    'url': 'https://github.com',
                    'description': '全球最大的代码托管平台',
                    'logo': 'https://github.com/favicon.ico',
                    'sort_order': 100
                },
                {
                    'name': 'Python',
                    'url': 'https://python.org',
                    'description': 'Python官方网站',
                    'logo': 'https://python.org/favicon.ico',
                    'sort_order': 90
                },
                {
                    'name': 'Flask',
                    'url': 'https://flask.palletsprojects.com',
                    'description': 'Python Web框架',
                    'logo': 'https://flask.palletsprojects.com/favicon.ico',
                    'sort_order': 80
                }
            ]
            
            for link_data in default_links:
                link = FriendLink(**link_data)
                link.save()
        
        return True
    
    def uninstall(self):
        """插件卸载时的操作"""
        current_app.logger.info(f"Uninstalling {self.name} plugin")
        # 可选择是否删除数据库表
        return True
    
    def get_links(self):
        """获取友链列表"""
        config = self.get_config()
        max_links = config.get('max_links', 10)
        
        links = FriendLink.get_active_links()
        if len(links) > max_links:
            links = links[:max_links]
            
        return links
    
    def render_sidebar_widget(self):
        """渲染侧边栏友链组件"""
        config = self.get_config()
        
        # 只有在配置显示时才渲染
        if not config.get('show_in_sidebar', True):
            return ""
        
        # 渲染友链模板
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'sidebar.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        context = {
            'friend_links': {
                'title': config.get('title', '友情链接'),
                'links': self.get_links(),
                'open_new_window': config.get('open_new_window', True),
                'show_description': config.get('show_description', False)
            }
        }
        
        # 使用插件管理器的模板渲染方法，提供Flask上下文
        html_content = current_app.plugin_manager.render_plugin_template(
            self.name, template_content, context
        )
        
        # 注册 JavaScript 和 CSS 加载钩子
        self._register_assets()
        
        return html_content
    
    def _register_assets(self):
        """注册资源文件（CSS 和 JavaScript）"""
        # 注册 CSS 到 head 钩子
        if hasattr(current_app, 'plugin_manager'):
            current_app.plugin_manager.register_template_hook(
                'head_assets',
                lambda: f'<link rel="stylesheet" href="/static/plugins/friend_links/css/friend_links.css">',
                priority=10,
                plugin_name=self.name
            )
            
            # 注册 JavaScript 到 scripts 钩子
            current_app.plugin_manager.register_template_hook(
                'scripts_assets',
                self._get_script_content,
                priority=10,
                plugin_name=self.name
            )
    
    def _get_script_content(self):
        """获取 JavaScript 内容"""
        # 等待 Vue 应用初始化完成后再加载友情链接功能
        return '''
<script>
// 等待Vue应用初始化完成后再加载友情链接功能
(function() {
    // 检查Vue应用是否已经挂载
    function waitForVueApp() {
        if (window._noteblog_app && document.getElementById('app').__vue__) {
            // Vue应用已挂载，加载友情链接功能
            loadFriendLinksScript();
        } else {
            // Vue应用未挂载，等待一段时间后重试
            setTimeout(waitForVueApp, 100);
        }
    }
    
    // 动态加载友情链接脚本
    function loadFriendLinksScript() {
        // 检查是否已经加载过
        if (document.getElementById('friend-links-script')) {
            return;
        }
        
        const script = document.createElement('script');
        script.id = 'friend-links-script';
        script.src = '/static/plugins/friend_links/js/friend_links.js';
        script.onload = function() {
            // 脚本加载完成后初始化友情链接功能
            if (window.FriendLinks && typeof window.FriendLinks.init === 'function') {
                window.FriendLinks.init();
                window.FriendLinks.adjustLayout();
                window.FriendLinks.watchTheme();
                window.FriendLinks.initLazyLoading();
            }
        };
        document.head.appendChild(script);
    }
    
    // 开始等待Vue应用
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', waitForVueApp);
    } else {
        waitForVueApp();
    }
})();
</script>
        '''
    
    def register_hooks(self):
        """注册插件钩子"""
        # 注册侧边栏底部钩子
        if hasattr(current_app, 'plugin_manager'):
            current_app.plugin_manager.register_template_hook(
                'sidebar_bottom', 
                self.render_sidebar_widget, 
                priority=10, 
                plugin_name=self.name
            )


# 插件入口点
def create_plugin():
    """创建插件实例"""
    return FriendLinksPlugin()


# 创建蓝图
friend_links_bp = Blueprint('friend_links', __name__, 
                           template_folder='templates',
                           static_folder='static')


@friend_links_bp.route('/plugins/friend_links/admin')
def admin_page():
    """插件的管理页面"""
    try:
        plugin = current_app.plugin_manager.get_plugin('friend_links')
        if plugin:
            config = plugin.get_config()
            links = [link.to_dict() for link in FriendLink.get_all_links()]
            return render_template('friend_links_admin.html', config=config, links=links)
        return "插件未找到", 404
    except Exception as e:
        current_app.logger.error(f"获取友链插件失败: {e}")
        return f"插件加载失败: {str(e)}", 500


@friend_links_bp.route('/plugins/friend_links/api/config', methods=['POST'])
def api_config():
    """API：保存配置"""
    try:
        plugin = current_app.plugin_manager.get_plugin('friend_links')
        if not plugin:
            return jsonify({'success': False, 'message': '插件未找到'})
        
        config_data = request.get_json()
        plugin.set_config(config_data)
        return jsonify({'success': True, 'message': '配置保存成功'})
    except Exception as e:
        current_app.logger.error(f"保存友链配置失败: {e}")
        return jsonify({'success': False, 'message': str(e)})


@friend_links_bp.route('/plugins/friend_links/api/links', methods=['GET', 'POST'])
def api_links():
    """API：管理链接"""
    try:
        plugin = current_app.plugin_manager.get_plugin('friend_links')
        if not plugin:
            return jsonify({'success': False, 'message': '插件未找到'})
        
        if request.method == 'GET':
            # 获取链接列表（后台不限制数量）
            links = [link.to_dict() for link in FriendLink.get_all_links()]
            return jsonify({'success': True, 'data': links})
        
        elif request.method == 'POST':
            # 添加新链接
            data = request.get_json()
            link = FriendLink(
                name=data.get('name'),
                url=data.get('url'),
                description=data.get('description', ''),
                logo=data.get('logo', ''),
                sort_order=data.get('sort_order', 0)
            )
            
            if link.save():
                return jsonify({'success': True, 'message': '链接添加成功'})
            else:
                return jsonify({'success': False, 'message': '链接添加失败'})
    except Exception as e:
        current_app.logger.error(f"管理友链失败: {e}")
        return jsonify({'success': False, 'message': str(e)})


@friend_links_bp.route('/plugins/friend_links/api/links/<int:link_id>', methods=['PUT', 'DELETE'])
def api_link_detail(link_id):
    """API：管理单个链接"""
    try:
        plugin = current_app.plugin_manager.get_plugin('friend_links')
        if not plugin:
            return jsonify({'success': False, 'message': '插件未找到'})
        
        link = FriendLink.get_by_id(link_id)
        if not link:
            return jsonify({'success': False, 'message': '链接不存在'})
        
        if request.method == 'PUT':
            # 更新链接
            data = request.get_json()
            link.name = data.get('name', link.name)
            link.url = data.get('url', link.url)
            link.description = data.get('description', link.description)
            link.logo = data.get('logo', link.logo)
            link.sort_order = data.get('sort_order', link.sort_order)
            
            if link.save():
                return jsonify({'success': True, 'message': '链接更新成功'})
            else:
                return jsonify({'success': False, 'message': '链接更新失败'})
        
        elif request.method == 'DELETE':
            # 删除链接
            if link.delete():
                return jsonify({'success': True, 'message': '链接删除成功'})
            else:
                return jsonify({'success': False, 'message': '链接删除失败'})
    except Exception as e:
        current_app.logger.error(f"管理友链详情失败: {e}")
        return jsonify({'success': False, 'message': str(e)})
