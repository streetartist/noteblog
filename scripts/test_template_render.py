#!/usr/bin/env python3
"""
测试插件模板渲染
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.plugin import Plugin
from app.services.theme_manager import theme_manager

def test_template_render():
    """测试模板渲染"""
    app = create_app()
    
    with app.app_context():
        print("=== 测试插件模板渲染 ===")
        
        # 获取已安装的插件
        installed_plugins = Plugin.query.order_by(Plugin.name).all()
        installed_names = {p.name for p in installed_plugins}
        
        print(f"已安装插件数量: {len(installed_plugins)}")
        for plugin in installed_plugins:
            print(f"- {plugin.name} (激活: {plugin.is_active})")
        
        # 获取可安装的插件（在plugins目录下但未安装的）
        available_plugins = []
        plugins_dir = 'plugins'
        
        if os.path.exists(plugins_dir):
            for item in os.listdir(plugins_dir):
                plugin_path = os.path.join(plugins_dir, item)
                if os.path.isdir(plugin_path) and item not in installed_names:
                    # 检查是否有plugin.json文件
                    plugin_json_path = os.path.join(plugin_path, 'plugin.json')
                    if os.path.exists(plugin_json_path):
                        try:
                            import json
                            with open(plugin_json_path, 'r', encoding='utf-8') as f:
                                plugin_info = json.load(f)
                            
                            # 创建一个插件对象用于显示
                            class AvailablePlugin:
                                def __init__(self, info, name):
                                    self.name = name
                                    self.display_name = info.get('display_name', name)
                                    self.description = info.get('description', '')
                                    self.version = info.get('version', '1.0.0')
                                    self.author = info.get('author', '')
                                    self.website = info.get('website', '')
                                    self.is_active = False
                                    self.is_installed = False
                            
                            available_plugins.append(AvailablePlugin(plugin_info, item))
                        except Exception as e:
                            print(f"Error reading plugin info for {item}: {e}")
                            continue
        
        # 合并插件列表
        all_plugins = list(installed_plugins) + available_plugins
        
        print(f"\n=== 最终插件列表 ===")
        print(f"总插件数量: {len(all_plugins)}")
        
        for i, plugin in enumerate(all_plugins):
            if hasattr(plugin, 'is_installed') and not plugin.is_installed:
                status = "未安装"
            elif hasattr(plugin, 'is_active') and plugin.is_active:
                status = "已激活"
            else:
                status = "已安装(未激活)"
            
            display_name = getattr(plugin, 'display_name', plugin.name)
            print(f"{i+1}. {display_name} ({plugin.name}) - {status}")
            
            # 检查模板条件
            print(f"   - plugin.is_installed defined: {hasattr(plugin, 'is_installed')}")
            if hasattr(plugin, 'is_installed'):
                print(f"   - plugin.is_installed value: {plugin.is_installed}")
            print(f"   - plugin.is_active: {getattr(plugin, 'is_active', 'N/A')}")
            
            # 模拟模板条件判断
            if hasattr(plugin, 'is_installed') and not plugin.is_installed:
                button_type = "安装"
            elif getattr(plugin, 'is_active', False):
                button_type = "停用"
            else:
                button_type = "激活"
            print(f"   - 应显示按钮: {button_type}")
        
        # 测试模板渲染
        print(f"\n=== 测试模板渲染 ===")
        try:
            context = {
                'plugins': all_plugins,
                'site_title': "插件管理测试",
                'current_user': None
            }
            
            # 尝试渲染模板
            rendered = theme_manager.render_template('admin/plugins.html', **context)
            print("模板渲染成功")
            
            # 检查渲染内容中是否包含插件信息
            if 'friend_links' in rendered:
                print("✓ friend_links插件在渲染结果中")
            else:
                print("✗ friend_links插件不在渲染结果中")
                
            if 'hello_world' in rendered:
                print("✓ hello_world插件在渲染结果中")
            else:
                print("✗ hello_world插件不在渲染结果中")
                
        except Exception as e:
            print(f"模板渲染失败: {e}")

if __name__ == '__main__':
    test_template_render()
