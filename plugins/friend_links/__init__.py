"""
友链插件
在侧边栏显示友链
"""
import os
from flask import current_app, render_template_string, Blueprint, request, jsonify
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
    from flask import render_template_string
    
    template = """
    <div class="friend-links-admin" id="friend-links-admin">
        <div class="el-card box-card is-always-shadow">
            <div class="el-card__header">
                <div class="clearfix">
                    <span>友情链接管理</span>
                    <button type="button" class="el-button el-button--text" style="float: right; padding: 3px 0" onclick="showAddDialog()">
                        <span>添加链接</span>
                    </button>
                </div>
            </div>
            <div class="el-card__body">
                <!-- 配置选项 -->
                <form id="config-form" class="el-form" label-width="120px" style="margin-bottom: 20px;">
                    <div class="el-form-item">
                        <label class="el-form-item__label" style="width: 120px;">模块标题</label>
                        <div class="el-form-item__content" style="margin-left: 120px;">
                            <div class="el-input">
                                <input type="text" id="config-title" class="el-input__inner" placeholder="友情链接" value="{{ config.title or '友情链接' }}">
                            </div>
                        </div>
                    </div>
                    <div class="el-form-item">
                        <label class="el-form-item__label" style="width: 120px;">显示在侧边栏</label>
                        <div class="el-form-item__content" style="margin-left: 120px;">
                            <label class="el-switch">
                                <input type="checkbox" id="config-show-in-sidebar" class="el-switch__input" {{ 'checked' if config.show_in_sidebar != False else '' }}>
                                <span class="el-switch__core"></span>
                            </label>
                        </div>
                    </div>
                    <div class="el-form-item">
                        <label class="el-form-item__label" style="width: 120px;">最大显示数量</label>
                        <div class="el-form-item__content" style="margin-left: 120px;">
                            <div class="el-input-number">
                                <input type="number" id="config-max-links" class="el-input__inner" value="{{ config.max_links or 10 }}" min="1" max="50">
                            </div>
                        </div>
                    </div>
                    <div class="el-form-item">
                        <label class="el-form-item__label" style="width: 120px;">新窗口打开</label>
                        <div class="el-form-item__content" style="margin-left: 120px;">
                            <label class="el-switch">
                                <input type="checkbox" id="config-open-new-window" class="el-switch__input" {{ 'checked' if config.open_new_window != False else '' }}>
                                <span class="el-switch__core"></span>
                            </label>
                        </div>
                    </div>
                    <div class="el-form-item">
                        <label class="el-form-item__label" style="width: 120px;">显示描述</label>
                        <div class="el-form-item__content" style="margin-left: 120px;">
                            <label class="el-switch">
                                <input type="checkbox" id="config-show-description" class="el-switch__input" {{ 'checked' if config.show_description else '' }}>
                                <span class="el-switch__core"></span>
                            </label>
                        </div>
                    </div>
                    <div class="el-form-item">
                        <div class="el-form-item__content" style="margin-left: 120px;">
                            <button type="button" class="el-button el-button--primary" onclick="saveConfig()">
                                <span>保存配置</span>
                            </button>
                        </div>
                    </div>
                </form>
                
                <!-- 链接列表 -->
                <div class="el-table el-table--fit el-table--enable-row-hover el-table--enable-row-transition" style="width: 100%;">
                    <div class="el-table__header-wrapper">
                        <table class="el-table__header" cellspacing="0" cellpadding="0" border="0">
                            <thead>
                                <tr>
                                    <th class="el-table_1_column_1 is-leaf"><div class="cell">网站名称</div></th>
                                    <th class="el-table_1_column_2 is-leaf"><div class="cell">链接地址</div></th>
                                    <th class="el-table_1_column_3 is-leaf"><div class="cell">描述</div></th>
                                    <th class="el-table_1_column_4 is-leaf"><div class="cell">操作</div></th>
                                </tr>
                            </thead>
                        </table>
                    </div>
                    <div class="el-table__body-wrapper">
                        <table class="el-table__body" cellspacing="0" cellpadding="0" border="0">
                            <tbody id="links-tbody">
                                <!-- 链接数据将通过JavaScript动态插入 -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 添加/编辑链接对话框 -->
        <div class="el-dialog__wrapper" id="link-dialog" style="display: none;">
            <div class="el-dialog" style="width: 500px; margin-top: 15vh;">
                <div class="el-dialog__header">
                    <span class="el-dialog__title" id="dialog-title">添加链接</span>
                    <button type="button" class="el-dialog__headerbtn" onclick="hideDialog()">
                        <i class="el-dialog__close el-icon el-icon-close"></i>
                    </button>
                </div>
                <div class="el-dialog__body">
                    <form id="link-form" class="el-form" label-width="80px">
                        <div class="el-form-item is-required">
                            <label class="el-form-item__label" style="width: 80px;">网站名称</label>
                            <div class="el-form-item__content" style="margin-left: 80px;">
                                <div class="el-input">
                                    <input type="text" id="link-name" class="el-input__inner" placeholder="请输入网站名称" required>
                                </div>
                            </div>
                        </div>
                        <div class="el-form-item is-required">
                            <label class="el-form-item__label" style="width: 80px;">链接地址</label>
                            <div class="el-form-item__content" style="margin-left: 80px;">
                                <div class="el-input">
                                    <input type="url" id="link-url" class="el-input__inner" placeholder="请输入链接地址" required>
                                </div>
                            </div>
                        </div>
                        <div class="el-form-item">
                            <label class="el-form-item__label" style="width: 80px;">描述</label>
                            <div class="el-form-item__content" style="margin-left: 80px;">
                                <div class="el-input">
                                    <input type="text" id="link-description" class="el-input__inner" placeholder="请输入网站描述">
                                </div>
                            </div>
                        </div>
                        <div class="el-form-item">
                            <label class="el-form-item__label" style="width: 80px;">Logo</label>
                            <div class="el-form-item__content" style="margin-left: 80px;">
                                <div class="el-input">
                                    <input type="url" id="link-logo" class="el-input__inner" placeholder="请输入Logo URL（可选）">
                                </div>
                            </div>
                        </div>
                        <div class="el-form-item">
                            <label class="el-form-item__label" style="width: 80px;">排序权重</label>
                            <div class="el-form-item__content" style="margin-left: 80px;">
                                <div class="el-input-number">
                                    <input type="number" id="link-sort-order" class="el-input__inner" value="0" min="0" max="999">
                                </div>
                            </div>
                        </div>
                    </form>
                </div>
                <div class="el-dialog__footer">
                    <span class="dialog-footer">
                        <button type="button" class="el-button" onclick="hideDialog()">
                            <span>取消</span>
                        </button>
                        <button type="button" class="el-button el-button--primary" onclick="saveLink()">
                            <span>确定</span>
                        </button>
                    </span>
                </div>
            </div>
        </div>
    </div>
    
    <script>
    // 全局变量
    let links = {{ links|tojson }};
    let editingId = null;
    
    // 初始化页面
    document.addEventListener('DOMContentLoaded', function() {
        renderLinksTable();
    });
    
    // 渲染链接表格
    function renderLinksTable() {
        const tbody = document.getElementById('links-tbody');
        tbody.innerHTML = '';
        
        links.forEach(function(link) {
            const tr = document.createElement('tr');
            tr.className = 'el-table__row';
            tr.innerHTML = `
                <td class="el-table_1_column_1"><div class="cell">${link.name}</div></td>
                <td class="el-table_1_column_2">
                    <div class="cell">
                        <a href="${link.url}" target="_blank" class="el-link el-link--primary">${link.url}</a>
                    </div>
                </td>
                <td class="el-table_1_column_3"><div class="cell">${link.description || ''}</div></td>
                <td class="el-table_1_column_4">
                    <div class="cell">
                        <button type="button" class="el-button el-button--mini" onclick="editLink(${link.id})">编辑</button>
                        <button type="button" class="el-button el-button--mini el-button--danger" onclick="deleteLink(${link.id})">删除</button>
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }
    
    // 显示添加对话框
    function showAddDialog() {
        document.getElementById('dialog-title').textContent = '添加链接';
        document.getElementById('link-form').reset();
        document.getElementById('link-sort-order').value = '0';
        editingId = null;
        document.getElementById('link-dialog').style.display = 'block';
    }
    
    // 隐藏对话框
    function hideDialog() {
        document.getElementById('link-dialog').style.display = 'none';
    }
    
    // 编辑链接
    function editLink(id) {
        const link = links.find(l => l.id === id);
        if (link) {
            document.getElementById('dialog-title').textContent = '编辑链接';
            document.getElementById('link-name').value = link.name;
            document.getElementById('link-url').value = link.url;
            document.getElementById('link-description').value = link.description || '';
            document.getElementById('link-logo').value = link.logo || '';
            document.getElementById('link-sort-order').value = link.sort_order || 0;
            editingId = id;
            document.getElementById('link-dialog').style.display = 'block';
        }
    }
    
    // 保存链接
    function saveLink() {
        const name = document.getElementById('link-name').value.trim();
        const url = document.getElementById('link-url').value.trim();
        
        if (!name || !url) {
            showMessage('请填写网站名称和链接地址', 'error');
            return;
        }
        
        const data = {
            name: name,
            url: url,
            description: document.getElementById('link-description').value.trim(),
            logo: document.getElementById('link-logo').value.trim(),
            sort_order: parseInt(document.getElementById('link-sort-order').value) || 0
        };
        
        const apiUrl = editingId ? `/plugins/friend_links/api/links/${editingId}` : '/plugins/friend_links/api/links';
        const method = editingId ? 'PUT' : 'POST';
        
        fetch(apiUrl, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage(editingId ? '链接更新成功' : '链接添加成功', 'success');
                loadLinks();
                hideDialog();
            } else {
                showMessage(data.message || '操作失败', 'error');
            }
        })
        .catch(error => {
            showMessage('网络错误', 'error');
        });
    }
    
    // 删除链接
    function deleteLink(id) {
        if (confirm('确定要删除这个链接吗？')) {
            fetch(`/plugins/friend_links/api/links/${id}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showMessage('链接删除成功', 'success');
                    loadLinks();
                } else {
                    showMessage(data.message || '删除失败', 'error');
                }
            })
            .catch(error => {
                showMessage('网络错误', 'error');
            });
        }
    }
    
    // 保存配置
    function saveConfig() {
        const config = {
            title: document.getElementById('config-title').value.trim(),
            show_in_sidebar: document.getElementById('config-show-in-sidebar').checked,
            max_links: parseInt(document.getElementById('config-max-links').value) || 10,
            open_new_window: document.getElementById('config-open-new-window').checked,
            show_description: document.getElementById('config-show-description').checked
        };
        
        fetch('/plugins/friend_links/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage('配置保存成功', 'success');
            } else {
                showMessage('配置保存失败', 'error');
            }
        })
        .catch(error => {
            showMessage('网络错误', 'error');
        });
    }
    
    // 加载链接列表
    function loadLinks() {
        fetch('/plugins/friend_links/api/links')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                links = data.data;
                renderLinksTable();
            }
        })
        .catch(error => {
            console.error('加载链接失败:', error);
        });
    }
    
    // 显示消息（简单的实现，如果Element UI的message不可用）
    function showMessage(message, type) {
        // 尝试使用Element UI的message
        if (typeof ELEMENT !== 'undefined' && ELEMENT.Message) {
            ELEMENT.Message({
                message: message,
                type: type,
                duration: 3000
            });
        } else {
            // 回退到alert
            alert(message);
        }
    }
    </script>
    """
    
    # 延迟获取插件实例，避免在蓝图注册时访问current_app
    try:
        plugin = current_app.plugin_manager.get_plugin('friend_links')
        if plugin:
            config = plugin.get_config()
            links = [link.to_dict() for link in plugin.get_links()]
            return render_template_string(template, config=config, links=links)
        else:
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
            # 获取链接列表
            links = [link.to_dict() for link in plugin.get_links()]
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
