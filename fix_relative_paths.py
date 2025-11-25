#!/usr/bin/env python3
"""
修复程序中的绝对路径问题，改为使用相对路径
"""

import os
import sys
from pathlib import Path

def get_project_root():
    """获取项目根目录"""
    return os.path.dirname(os.path.abspath(__file__))

def get_relative_path(abs_path):
    """将绝对路径转换为相对路径"""
    if not abs_path:
        return abs_path
    
    # 如果已经是相对路径，直接返回
    if not os.path.isabs(abs_path):
        return abs_path
    
    try:
        project_root = get_project_root()
        rel_path = os.path.relpath(abs_path, project_root)
        return rel_path.replace('\\', '/')  # 统一使用正斜杠
    except ValueError:
        return abs_path

def fix_theme_manager():
    """修复主题管理器中的路径问题"""
    print("修复主题管理器中的路径...")
    
    file_path = os.path.join('app', 'services', 'theme_manager.py')
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复 discover_themes 方法中的路径
    old_themes_dir = "themes_dir = os.path.join(current_app.root_path, '..', 'themes')"
    new_themes_dir = "themes_dir = os.path.join(os.getcwd(), 'themes')"
    
    content = content.replace(old_themes_dir, new_themes_dir)
    
    # 修复 create_theme 方法中的路径
    old_create_themes_dir = "themes_dir = os.path.join(current_app.root_path, '..', 'themes')"
    new_create_themes_dir = "themes_dir = os.path.join(os.getcwd(), 'themes')"
    
    content = content.replace(old_create_themes_dir, new_create_themes_dir)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ 主题管理器路径修复完成")

def fix_plugin_manager():
    """修复插件管理器中的路径问题"""
    print("修复插件管理器中的路径...")
    
    file_path = os.path.join('app', 'services', 'plugin_manager.py')
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复 discover_plugins 方法中的路径
    old_plugins_dir = "plugins_dir = os.path.join(current_app.root_path, '..', 'plugins')"
    new_plugins_dir = "plugins_dir = os.path.join(os.getcwd(), 'plugins')"
    
    content = content.replace(old_plugins_dir, new_plugins_dir)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ 插件管理器路径修复完成")

def fix_app_init():
    """修复应用初始化中的路径问题"""
    print("修复应用初始化中的路径...")
    
    file_path = os.path.join('app', '__init__.py')
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复主题静态文件路由中的路径
    old_themes_dir = "themes_dir = os.path.join(app.root_path, '..', 'themes')"
    new_themes_dir = "themes_dir = os.path.join(os.getcwd(), 'themes')"
    
    content = content.replace(old_themes_dir, new_themes_dir)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ 应用初始化路径修复完成")

def update_database_paths():
    """更新数据库中存储的路径为相对路径"""
    print("更新数据库中的路径...")
    
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
                    new_path = get_relative_path(old_path)
                    if new_path != old_path:
                        theme.install_path = new_path
                        print(f"  主题 {theme.name}: {old_path} -> {new_path}")
                
                if theme.screenshot:
                    old_path = theme.screenshot
                    new_path = get_relative_path(old_path)
                    if new_path != old_path:
                        theme.screenshot = new_path
                        print(f"  主题 {theme.name} screenshot: {old_path} -> {new_path}")
            
            # 更新插件路径
            plugins = Plugin.query.all()
            for plugin in plugins:
                if plugin.install_path:
                    old_path = plugin.install_path
                    new_path = get_relative_path(old_path)
                    if new_path != old_path:
                        plugin.install_path = new_path
                        print(f"  插件 {plugin.name}: {old_path} -> {new_path}")
            
            # 更新文章特色图片路径
            posts = Post.query.all()
            for post in posts:
                if post.featured_image:
                    old_path = post.featured_image
                    new_path = get_relative_path(old_path)
                    if new_path != old_path:
                        post.featured_image = new_path
                        print(f"  文章 {post.title}: {old_path} -> {new_path}")
            
            # 更新用户头像路径
            users = User.query.all()
            for user in users:
                if user.avatar:
                    old_path = user.avatar
                    new_path = get_relative_path(old_path)
                    if new_path != old_path:
                        user.avatar = new_path
                        print(f"  用户 {user.username}: {old_path} -> {new_path}")
            
            # 更新设置中的路径
            settings = Setting.query.all()
            for setting in settings:
                if setting.value and ('path' in setting.key.lower() or 'dir' in setting.key.lower() or 'url' in setting.key.lower()):
                    old_value = setting.value
                    new_value = get_relative_path(old_value)
                    if new_value != old_value:
                        setting.value = new_value
                        print(f"  设置 {setting.key}: {old_value} -> {new_value}")
            
            db.session.commit()
            print("✓ 数据库路径更新完成")
            
    except Exception as e:
        print(f"❌ 数据库路径更新失败: {e}")

def main():
    """主函数"""
    print("开始修复程序中的绝对路径问题...")
    print(f"项目根目录: {get_project_root()}")
    print()
    
    # 修复代码中的路径
    fix_theme_manager()
    fix_plugin_manager()
    fix_app_init()
    print()
    
    # 询问是否更新数据库
    response = input("是否要更新数据库中存储的路径？(y/N): ").strip().lower()
    if response in ['y', 'yes']:
        update_database_paths()
    else:
        print("跳过数据库路径更新")
    
    print()
    print("🎉 路径修复完成！")
    print()
    print("修复内容:")
    print("1. 主题管理器中的 themes 目录路径")
    print("2. 插件管理器中的 plugins 目录路径")
    print("3. 应用初始化中的主题静态文件路径")
    print("4. 数据库中存储的绝对路径（可选）")

if __name__ == '__main__':
    main()
