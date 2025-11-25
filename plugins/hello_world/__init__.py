"""
Hello World Plugin for Noteblog
一个简单的示例插件，演示插件系统的基本功能
"""

import os
from flask import Blueprint, current_app
from app.services.plugin_manager import PluginBase, hook, filter


class HelloWorldPlugin(PluginBase):
    """Hello World 插件主类"""
    
    def __init__(self):
        super().__init__()
        self.name = "hello_world"
        self.version = "1.0.0"
        self.description = "一个简单的Hello World示例插件"
        self.author = "Noteblog Team"
        
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
        # 创建插件配置
        self.set_config('message', 'Hello from HelloWorld Plugin!')
        self.set_config('show_in_footer', True)
        return True
    
    def uninstall(self):
        """插件卸载时的操作"""
        current_app.logger.info(f"Uninstalling {self.name} plugin")
        # 清理插件配置
        self.remove_config('message')
        self.remove_config('show_in_footer')
        return True
    
    @hook('before_request')
    def before_request_handler(self):
        """在每个请求前执行的钩子"""
        current_app.logger.debug(f"{self.name} plugin: before_request hook called")
    
    @hook('after_request')
    def after_request_handler(self, response):
        """在每个请求后执行的钩子"""
        current_app.logger.debug(f"{self.name} plugin: after_request hook called")
        return response
    
    @hook('template_context')
    def template_context_handler(self, context):
        """在模板渲染前添加上下文变量"""
        context['hello_world_message'] = self.get_config('message', 'Hello World!')
        return context
    
    @hook('admin_navigation')
    def admin_navigation_handler(self, navigation_items):
        """在管理后台导航栏添加项目"""
        navigation_items.append({
            'name': 'hello_world',
            'title': 'Hello World',
            'url': '/admin/hello_world',
            'icon': 'el-icon-chat-dot-round'
        })
        return navigation_items
    
    @filter('post_content')
    def post_content_filter(self, content, post):
        """过滤文章内容"""
        if self.get_config('append_message', False):
            content += f"\n\n<p><em>{self.get_config('message', 'Hello World!')}</em></p>"
        return content
    
    @filter('page_title')
    def page_title_filter(self, title):
        """过滤页面标题"""
        if self.get_config('add_prefix', False):
            title = f"👋 {title}"
        return title


# 插件入口点
def create_plugin():
    """创建插件实例"""
    return HelloWorldPlugin()


# 创建蓝图
hello_world_bp = Blueprint('hello_world', __name__, 
                          template_folder='templates',
                          static_folder='static')


@hello_world_bp.route('/admin/hello_world')
def admin_page():
    """插件的管理页面"""
    from flask import render_template_string
    
    template = """
    <div class="el-container">
        <el-card class="box-card">
            <div slot="header" class="clearfix">
                <span>Hello World 插件设置</span>
            </div>
            <div class="text item">
                <p>这是一个示例插件的管理页面。</p>
                <p>插件版本: {{ version }}</p>
                <p>作者: {{ author }}</p>
                <p>描述: {{ description }}</p>
            </div>
        </el-card>
    </div>
    """
    
    plugin = current_app.plugin_manager.get_plugin('hello_world')
    if plugin:
        info = plugin.get_info()
        return render_template_string(template, **info)
    else:
        return "插件未找到", 404


@hello_world_bp.route('/hello_world')
def hello_world_page():
    """插件的前端页面"""
    from flask import render_template_string
    
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hello World Plugin</title>
        <link rel="stylesheet" href="https://unpkg.com/element-ui/lib/theme-chalk/index.css">
    </head>
    <body>
        <div id="app">
            <el-container>
                <el-header>
                    <h1>{{ message }}</h1>
                </el-header>
                <el-main>
                    <el-card>
                        <p>这是来自 Hello World 插件的问候！</p>
                        <el-button type="primary" @click="showMessage">点击我</el-button>
                    </el-card>
                </el-main>
            </el-container>
        </div>
        
        <script src="https://unpkg.com/vue@2/dist/vue.js"></script>
        <script src="https://unpkg.com/element-ui/lib/index.js"></script>
        <script>
            new Vue({
                el: '#app',
                data: {
                    message: '{{ message }}'
                },
                methods: {
                    showMessage() {
                        this.$message({
                            message: 'Hello from Vue.js!',
                            type: 'success'
                        });
                    }
                }
            });
        </script>
    </body>
    </html>
    """
    
    plugin = current_app.plugin_manager.get_plugin('hello_world')
    message = "Hello World!"
    if plugin:
        message = plugin.get_config('message', 'Hello World!')
    
    return render_template_string(template, message=message)
