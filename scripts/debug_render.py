#!/usr/bin/env python3
"""
调试模板渲染错误的脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.services.theme_manager import theme_manager
from flask import request

def debug_template_rendering():
    """调试模板渲染"""
    app = create_app()
    
    with app.app_context():
        try:
            # 模拟请求上下文
            with app.test_request_context('/admin/comments'):
                # 测试渲染评论页面
                from app.models.comment import Comment
                from app.models.setting import SettingManager
                
                # 获取评论数据
                comments = Comment.query.order_by(Comment.created_at.desc()).paginate(page=1, per_page=20, error_out=False)
                
                # 构建上下文
                context = {
                    'comments': comments,
                    'status': '',
                    'site_title': '评论管理 - Noteblog 管理后台',
                    'current_user': None
                }
                
                # 尝试渲染模板
                result = theme_manager.render_template('admin/comments.html', **context)
                print('✅ 模板渲染成功！')
                
                # 检查模板内容
                if 'scope.row' in result:
                    print('⚠️  发现scope.row变量使用')
                    # 查找具体的scope.row使用位置
                    lines = result.split('\n')
                    for i, line in enumerate(lines):
                        if 'scope.row' in line:
                            print(f'第{i+1}行: {line.strip()[:100]}...')
                else:
                    print('✅ 未发现scope.row变量使用')
                    
        except Exception as e:
            print('❌ 模板渲染错误:', str(e))
            import traceback
            traceback.print_exc()
            
            # 尝试获取更详细的错误信息
            print('\n🔍 详细错误分析:')
            if "'scope' is undefined" in str(e):
                print("错误原因：模板中使用了未定义的 'scope' 变量")
                print("解决方案：")
                print("1. 检查模板中的 Vue.js 模板语法")
                print("2. 确保在 Jinja2 模板中正确处理 Vue 的 scope 变量")
                print("3. 考虑使用不同的变量名或模板语法")

def test_all_admin_templates():
    """测试所有管理模板"""
    app = create_app()
    
    admin_templates = [
        'admin/dashboard.html',
        'admin/posts.html', 
        'admin/comments.html',
        'admin/users.html',
        'admin/categories.html',
        'admin/plugins.html',
        'admin/themes.html',
        'admin/settings.html'
    ]
    
    with app.app_context():
        with app.test_request_context('/admin'):
            from app.models.post import Post, Category
            from app.models.comment import Comment
            from app.models.user import User
            from app.models.plugin import Plugin
            from app.models.theme import Theme
            from app.models.setting import SettingManager
            
            # 准备测试数据
            posts = Post.query.paginate(page=1, per_page=20, error_out=False)
            comments = Comment.query.paginate(page=1, per_page=20, error_out=False)
            users = User.query.paginate(page=1, per_page=20, error_out=False)
            categories = Category.query.all()
            plugins = Plugin.query.all()
            themes = Theme.query.all()
            settings = SettingManager.get_category('general')
            
            test_contexts = {
                'admin/dashboard.html': {
                    'stats': {
                        'total_posts': 10, 'published_posts': 8, 'draft_posts': 2,
                        'total_users': 5, 'active_users': 4, 'total_comments': 20,
                        'pending_comments': 3, 'total_categories': 3, 'total_tags': 10,
                        'active_plugins': 2, 'total_plugins': 5,
                        'active_theme': Theme.query.filter_by(is_active=True).first()
                    },
                    'latest_posts': posts.items[:5],
                    'latest_comments': comments.items[:5],
                    'site_title': '仪表板 - Noteblog 管理后台',
                    'current_user': None
                },
                'admin/posts.html': {
                    'posts': posts,
                    'status': '',
                    'site_title': '文章管理 - Noteblog 管理后台',
                    'current_user': None
                },
                'admin/comments.html': {
                    'comments': comments,
                    'status': '',
                    'site_title': '评论管理 - Noteblog 管理后台',
                    'current_user': None
                },
                'admin/users.html': {
                    'users': users,
                    'site_title': '用户管理 - Noteblog 管理后台',
                    'current_user': None
                },
                'admin/categories.html': {
                    'categories': categories,
                    'site_title': '分类管理 - Noteblog 管理后台',
                    'current_user': None
                },
                'admin/plugins.html': {
                    'plugins': plugins,
                    'site_title': '插件管理 - Noteblog 管理后台',
                    'current_user': None
                },
                'admin/themes.html': {
                    'themes': themes,
                    'site_title': '主题管理 - Noteblog 管理后台',
                    'current_user': None
                },
                'admin/settings.html': {
                    'settings': settings,
                    'site_title': '系统设置 - Noteblog 管理后台',
                    'current_user': None
                }
            }
            
            for template_name in admin_templates:
                print(f'\n🧪 测试模板: {template_name}')
                try:
                    context = test_contexts.get(template_name, {})
                    result = theme_manager.render_template(template_name, **context)
                    print(f'✅ {template_name} 渲染成功')
                    
                    # 检查scope变量问题
                    if 'scope.row' in result:
                        print(f'⚠️  {template_name} 中发现scope.row变量使用')
                        
                except Exception as e:
                    print(f'❌ {template_name} 渲染失败: {str(e)}')

if __name__ == '__main__':
    print('🔍 开始调试模板渲染问题...')
    debug_template_rendering()
    
    print('\n' + '='*50)
    print('🧪 测试所有管理模板...')
    test_all_admin_templates()
