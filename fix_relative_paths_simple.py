#!/usr/bin/env python3
"""
修复数据库中的路径，使用简洁的相对路径格式
"""

import os
import sys

def get_simple_path(abs_path):
    """将绝对路径转换为简洁的相对路径"""
    if not abs_path:
        return abs_path
    
    # 如果已经是简洁格式，直接返回
    if abs_path.startswith('themes/') or abs_path.startswith('plugins/'):
        return abs_path
    
    # 如果已经是相对路径，转换为简洁格式
    if not os.path.isabs(abs_path):
        # 处理类似 ../Noteblog/plugins/hello_world 的情况
        if 'themes/' in abs_path:
            parts = abs_path.split('themes/')
            if len(parts) > 1:
                return 'themes/' + parts[1]
        elif 'plugins/' in abs_path:
            parts = abs_path.split('plugins/')
            if len(parts) > 1:
                return 'plugins/' + parts[1]
        return abs_path
    
    try:
        # 处理绝对路径
        if 'themes\\' in abs_path or '/themes/' in abs_path:
            if 'themes\\' in abs_path:
                parts = abs_path.split('themes\\')
            else:
                parts = abs_path.split('/themes/')
            if len(parts) > 1:
                return 'themes/' + parts[1].replace('\\', '/')
        
        elif 'plugins\\' in abs_path or '/plugins/' in abs_path:
            if 'plugins\\' in abs_path:
                parts = abs_path.split('plugins\\')
            else:
                parts = abs_path.split('/plugins/')
            if len(parts) > 1:
                return 'plugins/' + parts[1].replace('\\', '/')
        
        return abs_path
    except Exception:
        return abs_path

def update_database_paths():
    """更新数据库中存储的路径为简洁的相对路径"""
    print("更新数据库中的路径为简洁格式...")
    
    # 添加项目根目录到Python路径
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from app import create_app, db
        from app.models import Theme, Plugin, Post, User, Setting
        
        app = create_app()
        
        with app.app_context():
            # 更新主题路径
            themes = Theme.query.all()
            for theme in themes:
                if theme.install_path:
                    old_path = theme.install_path
                    new_path = get_simple_path(old_path)
                    if new_path != old_path:
                        theme.install_path = new_path
                        print(f"  主题 {theme.name}: {old_path} -> {new_path}")
                
                if theme.screenshot:
                    old_path = theme.screenshot
                    new_path = get_simple_path(old_path)
                    if new_path != old_path:
                        theme.screenshot = new_path
                        print(f"  主题 {theme.name} screenshot: {old_path} -> {new_path}")
            
            # 更新插件路径
            plugins = Plugin.query.all()
            for plugin in plugins:
                if plugin.install_path:
                    old_path = plugin.install_path
                    new_path = get_simple_path(old_path)
                    if new_path != old_path:
                        plugin.install_path = new_path
                        print(f"  插件 {plugin.name}: {old_path} -> {new_path}")
            
            # 更新文章特色图片路径
            posts = Post.query.all()
            for post in posts:
                if post.featured_image:
                    old_path = post.featured_image
                    new_path = get_simple_path(old_path)
                    if new_path != old_path:
                        post.featured_image = new_path
                        print(f"  文章 {post.title}: {old_path} -> {new_path}")
            
            # 更新用户头像路径
            users = User.query.all()
            for user in users:
                if user.avatar:
                    old_path = user.avatar
                    new_path = get_simple_path(old_path)
                    if new_path != old_path:
                        user.avatar = new_path
                        print(f"  用户 {user.username}: {old_path} -> {new_path}")
            
            # 更新设置中的路径
            settings = Setting.query.all()
            for setting in settings:
                if setting.value and ('path' in setting.key.lower() or 'dir' in setting.key.lower() or 'url' in setting.key.lower()):
                    old_value = setting.value
                    new_value = get_simple_path(old_value)
                    if new_value != old_value:
                        setting.value = new_value
                        print(f"  设置 {setting.key}: {old_value} -> {new_value}")
            
            db.session.commit()
            print("✓ 数据库路径更新完成")
            
    except Exception as e:
        print(f"❌ 数据库路径更新失败: {e}")

def main():
    """主函数"""
    print("开始修复数据库中的路径格式...")
    print()
    
    update_database_paths()
    
    print()
    print("🎉 路径格式修复完成！")
    print()
    print("修复内容:")
    print("- 将绝对路径转换为简洁的相对路径格式")
    print("- 主题路径格式: themes/default")
    print("- 插件路径格式: plugins/hello_world")

if __name__ == '__main__':
    main()
