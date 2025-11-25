#!/usr/bin/env python3
"""
Vercel 部署测试脚本
用于验证修复后的应用是否能正常运行
"""

import os
import sys
import tempfile
import requests
import time
from contextlib import contextmanager

# 设置测试环境变量
os.environ['FLASK_ENV'] = 'testing'
os.environ['SKIP_PLUGIN_INIT'] = '1'
os.environ['USE_MEMORY_DB'] = 'true'
os.environ['SECRET_KEY'] = 'test-secret-key'

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

@contextmanager
def test_app():
    """创建测试应用上下文"""
    # 导入应用
    from api.index import app
    
    # 设置测试配置
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            yield client

def test_database_connection():
    """测试数据库连接"""
    print("🔍 测试数据库连接...")
    
    try:
        with test_app() as client:
            from api.index import ensure_database_initialized
            result = ensure_database_initialized()
            
            if result:
                print("✅ 数据库连接成功")
                return True
            else:
                print("❌ 数据库连接失败")
                return False
    except Exception as e:
        print(f"❌ 数据库连接异常: {e}")
        return False

def test_setting_manager():
    """测试设置管理器"""
    print("🔍 测试设置管理器...")
    
    try:
        from app.models.setting import SettingManager
        
        # 测试获取设置（应该返回默认值）
        site_title = SettingManager.get('site_title', 'Default Title')
        posts_per_page = SettingManager.get('posts_per_page', 10)
        
        print(f"📝 网站标题: {site_title}")
        print(f"📝 每页文章数: {posts_per_page}")
        
        if site_title and posts_per_page:
            print("✅ 设置管理器工作正常")
            return True
        else:
            print("❌ 设置管理器返回空值")
            return False
    except Exception as e:
        print(f"❌ 设置管理器异常: {e}")
        return False

def test_homepage():
    """测试首页访问"""
    print("🔍 测试首页访问...")
    
    try:
        with test_app() as client:
            response = client.get('/')
            
            if response.status_code == 200:
                print("✅ 首页访问成功")
                print(f"📄 响应状态码: {response.status_code}")
                return True
            else:
                print(f"❌ 首页访问失败，状态码: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ 首页访问异常: {e}")
        return False

def test_login_page():
    """测试登录页面"""
    print("🔍 测试登录页面...")
    
    try:
        with test_app() as client:
            response = client.get('/auth/login')
            
            # 登录页面可能重定向，所以检查 200 或 302
            if response.status_code in [200, 302]:
                print("✅ 登录页面访问成功")
                print(f"📄 响应状态码: {response.status_code}")
                return True
            else:
                print(f"❌ 登录页面访问失败，状态码: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ 登录页面访问异常: {e}")
        return False

def test_admin_page():
    """测试管理后台"""
    print("🔍 测试管理后台...")
    
    try:
        with test_app() as client:
            response = client.get('/admin')
            
            # 管理后台应该重定向到登录页面（302）或直接访问（200）
            # 也可能是 308 永久重定向
            if response.status_code in [302, 200, 308]:
                print("✅ 管理后台响应正常")
                print(f"📄 响应状态码: {response.status_code}")
                return True
            else:
                print(f"❌ 管理后台访问失败，状态码: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ 管理后台访问异常: {e}")
        return False

def test_error_handling():
    """测试错误处理"""
    print("🔍 测试错误处理...")
    
    try:
        with test_app() as client:
            # 访问不存在的页面
            response = client.get('/nonexistent-page')
            
            if response.status_code == 404:
                print("✅ 404 错误处理正常")
                return True
            else:
                print(f"❌ 404 错误处理异常，状态码: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ 错误处理测试异常: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("🚀 开始 Vercel 部署测试")
    print("=" * 50)
    
    tests = [
        ("数据库连接", test_database_connection),
        ("设置管理器", test_setting_manager),
        ("首页访问", test_homepage),
        ("登录页面", test_login_page),
        ("管理后台", test_admin_page),
        ("错误处理", test_error_handling),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 运行测试: {test_name}")
        print("-" * 30)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ 测试 '{test_name}' 发生异常: {e}")
            results.append((test_name, False))
        
        time.sleep(0.5)  # 短暂延迟
    
    # 输出测试结果摘要
    print("\n" + "=" * 50)
    print("📊 测试结果摘要")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！应用已准备好部署到 Vercel")
        return True
    else:
        print("⚠️  部分测试失败，请检查问题后重试")
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
