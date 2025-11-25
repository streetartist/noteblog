#!/usr/bin/env python3
"""
测试admin插件页面的逻辑
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.plugin import Plugin

def test_admin_plugins():
    """测试admin插件页面逻辑"""
    app = create_app()
    
    with app.app_context():
        print("=== 测试Admin插件页面逻辑 ===")
        
        # 获取已安装的插件
        installed_plugins = Plugin.query.order_by(Plugin.name).all()
        installed_names = {p.name for p in installed_plugins}
        
        print(f"已安装插件数量: {len(installed_plugins)}")
        for plugin in installed_plugins:
            print(f"- {plugin.name} (激活: {plugin.is_active})")
        
        print(f"已安装插件名称集合: {installed_names}")
        
        # 获取可安装的插件（在plugins目录下但未安装的）
        available_plugins = []
        plugins_dir = 'plugins'
        
        print(f"\n扫描插件目录: {plugins_dir}")
        print(f"目录是否存在: {os.path.exists(plugins_dir)}")
        
        if os.path.exists(plugins_dir):
            items = os.listdir(plugins_dir)
            print(f"目录内容: {items}")
            
            for item in items:
                plugin_path = os.path.join(plugins_dir, item)
                print(f"\n检查项目: {item}")
                print(f"是否为目录: {os.path.isdir(plugin_path)}")
                print(f"是否已安装: {item in installed_names}")
                
                if os.path.isdir(plugin_path) and item not in installed_names:
                    # 检查是否有plugin.json文件
                    plugin_json_path = os.path.join(plugin_path, 'plugin.json')
                    print(f"plugin.json路径: {plugin_json_path}")
                    print(f"plugin.json是否存在: {os.path.exists(plugin_json_path)}")
                    
                    if os.path.exists(plugin_json_path):
                        try:
                            import json
                            with open(plugin_json_path, 'r', encoding='utf-8') as f:
                                plugin_info = json.load(f)
                            
                            print(f"插件信息: {plugin_info}")
                            
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
                            
                            plugin = AvailablePlugin(plugin_info, item)
                            available_plugins.append(plugin)
                            print(f"成功创建插件对象: {plugin.display_name}")
                            
                        except Exception as e:
                            print(f"Error reading plugin info for {item}: {e}")
                            continue
                    else:
                        print("plugin.json文件不存在")
        
        # 合并插件列表
        all_plugins = list(installed_plugins) + available_plugins
        
        print(f"\n=== 最终结果 ===")
        print(f"总插件数量: {len(all_plugins)}")
        print(f"已安装插件: {len(installed_plugins)}")
        print(f"可安装插件: {len(available_plugins)}")
        
        for i, plugin in enumerate(all_plugins):
            if hasattr(plugin, 'is_installed') and not plugin.is_installed:
                status = "未安装"
            elif hasattr(plugin, 'is_active') and plugin.is_active:
                status = "已激活"
            else:
                status = "已安装(未激活)"
            
            display_name = getattr(plugin, 'display_name', plugin.name)
            print(f"{i+1}. {display_name} ({plugin.name}) - {status}")

if __name__ == '__main__':
    test_admin_plugins()
