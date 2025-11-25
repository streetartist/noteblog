#!/usr/bin/env python3
"""
Noteblog项目设置测试脚本
验证所有组件是否正确配置
"""

import os
import sys
import importlib
from pathlib import Path

def test_imports():
    """测试所有必要的模块是否可以导入"""
    print("🔍 测试模块导入...")
    
    try:
        # 测试Flask相关
        import flask
        from flask import Flask, render_template, request
        print("✓ Flask导入成功")
        
        # 测试SQLAlchemy
        import sqlalchemy
        from flask_sqlalchemy import SQLAlchemy
        print("✓ SQLAlchemy导入成功")
        
        # 测试Flask扩展
        from flask_login import LoginManager
        from flask_migrate import Migrate
        from flask_wtf import FlaskForm
        print("✓ Flask扩展导入成功")
        
        # 测试应用模块
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from app import create_app
        print("✓ 应用模块导入成功")
        
        # 测试模型
        from app.models import User, Post, Comment, Category, Tag, Plugin, Theme, Setting
        print("✓ 数据模型导入成功")
        
        # 测试服务
        from app.services import PluginManager, ThemeManager
        print("✓ 服务模块导入成功")
        
        # 测试视图
        from app.views import main, auth, admin, api
        print("✓ 视图模块导入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_app_creation():
    """测试应用创建"""
    print("\n🏗️ 测试应用创建...")
    
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            # 测试应用配置
            assert app.config['SECRET_KEY'] is not None
            print("✓ 应用配置正确")
            
            # 测试数据库初始化
            from app import db
            assert db is not None
            print("✓ 数据库初始化成功")
            
            # 测试插件管理器
            assert hasattr(app, 'plugin_manager')
            print("✓ 插件管理器初始化成功")
            
            # 测试主题管理器
            assert hasattr(app, 'theme_manager')
            print("✓ 主题管理器初始化成功")
            
        return True
        
    except Exception as e:
        print(f"❌ 应用创建失败: {e}")
        return False


def test_directory_structure():
    """测试目录结构"""
    print("\n📁 测试目录结构...")
    
    required_dirs = [
        'app',
        'app/models',
        'app/views',
        'app/services',
        'plugins',
        'themes',
        'themes/default',
        'themes/default/templates',
        'themes/default/static',
        'migrations',
        'docker',
        'docker/nginx',
        'docker/mysql'
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print(f"❌ 缺少目录: {', '.join(missing_dirs)}")
        return False
    else:
        print("✓ 目录结构正确")
        return True


def test_required_files():
    """测试必需文件是否存在"""
    print("\n📄 测试必需文件...")
    
    required_files = [
        'app.py',
        'run.py',
        'requirements.txt',
        'README.md',
        '.env.example',
        'Dockerfile',
        'docker-compose.yml',
        'alembic.ini',
        'app/__init__.py',
        'app/models/__init__.py',
        'app/views/__init__.py',
        'app/services/__init__.py',
        'themes/default/theme.json',
        'themes/default/templates/base.html',
        'themes/default/static/css/style.css',
        'plugins/hello_world/__init__.py',
        'plugins/hello_world/plugin.json'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ 缺少文件: {', '.join(missing_files)}")
        return False
    else:
        print("✓ 必需文件完整")
        return True


def test_plugin_system():
    """测试插件系统"""
    print("\n🔌 测试插件系统...")
    
    try:
        from app.services.plugin_manager import PluginManager
        from app import create_app
        
        app = create_app()
        with app.app_context():
            plugin_manager = PluginManager()
            
            # 测试插件发现
            plugins = plugin_manager.discover_plugins()
            print(f"✓ 发现 {len(plugins)} 个插件")
            
            # 测试Hello World插件
            hello_world_path = Path('plugins/hello_world')
            if hello_world_path.exists():
                plugin_info = plugin_manager.load_plugin_info(hello_world_path)
                if plugin_info:
                    print(f"✓ Hello World插件信息加载成功: {plugin_info.get('name')}")
                else:
                    print("❌ Hello World插件信息加载失败")
                    return False
            
        return True
        
    except Exception as e:
        print(f"❌ 插件系统测试失败: {e}")
        return False


def test_theme_system():
    """测试主题系统"""
    print("\n🎨 测试主题系统...")
    
    try:
        from app.services.theme_manager import ThemeManager
        from app import create_app
        
        app = create_app()
        with app.app_context():
            theme_manager = ThemeManager()
            
            # 测试主题发现
            themes = theme_manager.discover_themes()
            print(f"✓ 发现 {len(themes)} 个主题")
            
            # 测试默认主题
            default_theme_path = Path('themes/default')
            if default_theme_path.exists():
                theme_info = theme_manager.load_theme_info(default_theme_path)
                if theme_info:
                    print(f"✓ 默认主题信息加载成功: {theme_info.get('name')}")
                else:
                    print("❌ 默认主题信息加载失败")
                    return False
            
        return True
        
    except Exception as e:
        print(f"❌ 主题系统测试失败: {e}")
        return False


def test_database_models():
    """测试数据库模型"""
    print("\n🗄️ 测试数据库模型...")
    
    try:
        from app.models import User, Post, Comment, Category, Tag, Plugin, Theme, Setting
        
        # 测试模型关系
        user = User(username='test', email='test@example.com', password='test123')
        post = Post(title='Test Post', content='Test content', author_id=1)
        comment = Comment(content='Test comment', post=post, author=user)
        
        # 测试模型方法
        assert hasattr(user, 'set_password')
        assert hasattr(user, 'check_password')
        assert hasattr(post, 'generate_slug')
        
        print("✓ 数据库模型测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 数据库模型测试失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("🚀 开始Noteblog项目设置测试\n")
    
    tests = [
        test_directory_structure,
        test_required_files,
        test_imports,
        test_app_creation,
        test_plugin_system,
        test_theme_system,
        test_database_models
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！Noteblog项目设置完成。")
        print("\n📋 下一步操作:")
        print("1. 复制 .env.example 到 .env 并配置环境变量")
        print("2. 运行 'python run.py init' 初始化数据库")
        print("3. 运行 'python run.py run' 启动开发服务器")
        print("4. 访问 http://localhost:5000 查看应用")
        return True
    else:
        print("❌ 部分测试失败，请检查配置。")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
