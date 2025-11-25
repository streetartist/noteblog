from app import create_app

app = create_app()

with app.app_context():
    print(f"current_app.root_path: {app.root_path}")
    print(f"当前工作目录: {app.root_path}")
    print(f"themes目录路径: {app.root_path}/../themes")
    
    import os
    themes_dir = os.path.join(app.root_path, '..', 'themes')
    print(f"计算后的themes路径: {themes_dir}")
    print(f"themes目录是否存在: {os.path.exists(themes_dir)}")
    
    # 检查当前工作目录
    import os
    cwd = os.getcwd()
    print(f"os.getcwd(): {cwd}")
    
    # 检查相对路径
    rel_themes = os.path.join(cwd, 'themes')
    print(f"相对路径themes: {rel_themes}")
    print(f"相对路径themes是否存在: {os.path.exists(rel_themes)}")
