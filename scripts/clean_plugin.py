#!/usr/bin/env python3
"""
清理插件数据库记录
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.plugin import Plugin, PluginHook

def clean_plugin(plugin_name):
    """清理指定插件的数据库记录"""
    app = create_app()
    
    with app.app_context():
        # 查找插件
        plugin = Plugin.query.filter_by(name=plugin_name).first()
        if plugin:
            # 删除相关的钩子记录
            PluginHook.query.filter_by(plugin_id=plugin.id).delete()
            
            # 删除插件记录
            db.session.delete(plugin)
            db.session.commit()
            
            print(f"插件 {plugin_name} 已从数据库中删除")
        else:
            print(f"插件 {plugin_name} 在数据库中不存在")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        plugin_name = sys.argv[1]
        clean_plugin(plugin_name)
    else:
        # 默认清理friend_links
        clean_plugin('friend_links')
