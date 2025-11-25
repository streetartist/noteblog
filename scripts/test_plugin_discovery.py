#!/usr/bin/env python3
"""
测试插件发现逻辑
"""
import os
import json

def test_plugin_discovery():
    """测试插件发现逻辑"""
    print("=== 测试插件发现逻辑 ===")
    
    # 模拟已安装插件列表（空）
    installed_names = set()
    
    # 获取可安装的插件
    available_plugins = []
    plugins_dir = 'plugins'
    
    print(f"扫描插件目录: {plugins_dir}")
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
    
    print(f"\n=== 结果 ===")
    print(f"发现的可安装插件数量: {len(available_plugins)}")
    for plugin in available_plugins:
        print(f"- {plugin.display_name} ({plugin.name})")

if __name__ == '__main__':
    test_plugin_discovery()
