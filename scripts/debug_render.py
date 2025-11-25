from app import create_app
from app.services.theme_manager import theme_manager

app = create_app()

with app.app_context():
    # 测试渲染404模板
    context = {
        'error': 'Test Error',
        'site_title': 'Test - Noteblog',
        'current_user': None
    }
    
    print("测试渲染404模板...")
    result = theme_manager.render_template('404.html', **context)
    
    if result.startswith('<h1>模板未找到</h1>'):
        print("❌ 模板未找到")
    elif result.startswith('<h1>模板渲染错误</h1>'):
        print("❌ 模板渲染错误")
    else:
        print("✅ 模板渲染成功")
        print(f"渲染结果长度: {len(result)} 字符")
        print(f"前100个字符: {result[:100]}...")
