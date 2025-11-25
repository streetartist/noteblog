from app import create_app, db
from app.models.theme import Theme

app = create_app()

with app.app_context():
    # 查询所有主题
    themes = Theme.query.all()
    for theme in themes:
        print(f"主题名称: {theme.name}")
        print(f"安装路径: {theme.install_path}")
        print(f"路径是否存在: {__import__('os').path.exists(theme.install_path)}")
        print("---")
    
    # 检查当前主题
    from app.services.theme_manager import theme_manager
    if theme_manager.current_theme:
        print(f"当前主题: {theme_manager.current_theme.name}")
        print(f"当前主题路径: {theme_manager.current_theme.install_path}")
        
        # 检查404模板路径
        import os
        template_404 = os.path.join(theme_manager.current_theme.install_path, 'templates', '404.html')
        print(f"404模板路径: {template_404}")
        print(f"404模板是否存在: {os.path.exists(template_404)}")
