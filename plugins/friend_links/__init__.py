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
        
        from jinja2 import Template
        template = Template(template_content)
        
        context = {
            'friend_links': {
                'title': config.get('title', '友情链接'),
                'links': self.get_links(),
                'open_new_window': config.get('open_new_window', True),
                'show_description': config.get('show_description', False)
            }
        }
        
        return template.render(**context)
    
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


@friend_links_bp.route('/admin/friend_links')
def admin_page():
    """插件的管理页面"""
    from flask import render_template_string
    
    template = """
    <div class="el-container">
        <el-card class="box-card">
            <div slot="header" class="clearfix">
                <span>友情链接管理</span>
                <el-button style="float: right; padding: 3px 0" type="text" @click="showAddDialog">添加链接</el-button>
            </div>
            
            <!-- 配置选项 -->
            <el-form :model="config" label-width="120px" style="margin-bottom: 20px;">
                <el-form-item label="模块标题">
                    <el-input v-model="config.title" placeholder="友情链接"></el-input>
                </el-form-item>
                <el-form-item label="显示在侧边栏">
                    <el-switch v-model="config.show_in_sidebar"></el-switch>
                </el-form-item>
                <el-form-item label="最大显示数量">
                    <el-input-number v-model="config.max_links" :min="1" :max="50"></el-input-number>
                </el-form-item>
                <el-form-item label="新窗口打开">
                    <el-switch v-model="config.open_new_window"></el-switch>
                </el-form-item>
                <el-form-item label="显示描述">
                    <el-switch v-model="config.show_description"></el-switch>
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="saveConfig">保存配置</el-button>
                </el-form-item>
            </el-form>
            
            <!-- 链接列表 -->
            <el-table :data="links" style="width: 100%">
                <el-table-column prop="name" label="网站名称" width="150"></el-table-column>
                <el-table-column prop="url" label="链接地址">
                    <template #default="scope">
                        <el-link :href="scope.row.url" target="_blank" type="primary">{{ scope.row.url }}</el-link>
                    </template>
                </el-table-column>
                <el-table-column prop="description" label="描述"></el-table-column>
                <el-table-column label="操作" width="150">
                    <template #default="scope">
                        <el-button size="mini" @click="editLink(scope.row)">编辑</el-button>
                        <el-button size="mini" type="danger" @click="deleteLink(scope.row)">删除</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-card>
        
        <!-- 添加/编辑链接对话框 -->
        <el-dialog :title="dialogTitle" v-model="dialogVisible" width="500px">
            <el-form :model="linkForm" label-width="80px">
                <el-form-item label="网站名称" required>
                    <el-input v-model="linkForm.name" placeholder="请输入网站名称"></el-input>
                </el-form-item>
                <el-form-item label="链接地址" required>
                    <el-input v-model="linkForm.url" placeholder="请输入链接地址"></el-input>
                </el-form-item>
                <el-form-item label="描述">
                    <el-input v-model="linkForm.description" placeholder="请输入网站描述"></el-input>
                </el-form-item>
                <el-form-item label="Logo">
                    <el-input v-model="linkForm.logo" placeholder="请输入Logo URL（可选）"></el-input>
                </el-form-item>
                <el-form-item label="排序权重">
                    <el-input-number v-model="linkForm.sort_order" :min="0" :max="999"></el-input-number>
                </el-form-item>
            </el-form>
            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="dialogVisible = false">取消</el-button>
                    <el-button type="primary" @click="saveLink">确定</el-button>
                </span>
            </template>
        </el-dialog>
    </div>
    
    <script>
    new Vue({
        el: '.el-container',
        data: {
            config: {
                title: '{{ config.title or "友情链接" }}',
                show_in_sidebar: {{ 'true' if config.show_in_sidebar != False else 'false' }},
                max_links: {{ config.max_links or 10 }},
                open_new_window: {{ 'true' if config.open_new_window != False else 'false' }},
                show_description: {{ 'true' if config.show_description else 'false' }}
            },
            links: {{ links|tojson }},
            dialogVisible: false,
            dialogTitle: '添加链接',
            linkForm: {
                name: '',
                url: '',
                description: '',
                logo: '',
                sort_order: 0
            },
            editingId: null
        },
        methods: {
            saveConfig() {
                fetch('/friend_links/api/config', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(this.config)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.$message.success('配置保存成功');
                    } else {
                        this.$message.error('配置保存失败');
                    }
                });
            },
            showAddDialog() {
                this.dialogTitle = '添加链接';
                this.linkForm = { name: '', url: '', description: '', logo: '', sort_order: 0 };
                this.editingId = null;
                this.dialogVisible = true;
            },
            editLink(link) {
                this.dialogTitle = '编辑链接';
                this.linkForm = { ...link };
                this.editingId = link.id;
                this.dialogVisible = true;
            },
            saveLink() {
                if (!this.linkForm.name || !this.linkForm.url) {
                    this.$message.error('请填写网站名称和链接地址');
                    return;
                }
                
                const url = this.editingId ? `/friend_links/api/links/${this.editingId}` : '/friend_links/api/links';
                const method = this.editingId ? 'PUT' : 'POST';
                
                fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(this.linkForm)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.$message.success(this.editingId ? '链接更新成功' : '链接添加成功');
                        this.loadLinks();
                        this.dialogVisible = false;
                    } else {
                        this.$message.error(data.message || '操作失败');
                    }
                });
            },
            deleteLink(link) {
                this.$confirm('确定要删除这个链接吗？', '确认删除', {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消',
                    type: 'warning'
                }).then(() => {
                    fetch(`/friend_links/api/links/${link.id}`, {
                        method: 'DELETE'
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            this.$message.success('链接删除成功');
                            this.loadLinks();
                        } else {
                            this.$message.error(data.message || '删除失败');
                        }
                    });
                });
            },
            loadLinks() {
                fetch('/friend_links/api/links')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.links = data.data;
                    }
                });
            }
        }
    });
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


@friend_links_bp.route('/api/config', methods=['POST'])
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


@friend_links_bp.route('/api/links', methods=['GET', 'POST'])
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


@friend_links_bp.route('/api/links/<int:link_id>', methods=['PUT', 'DELETE'])
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
