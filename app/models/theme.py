"""
主题模型
"""
from datetime import datetime
import json
from app import db

class Theme(db.Model):
    """主题模型"""
    __tablename__ = 'themes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    version = db.Column(db.String(20), nullable=False)
    author = db.Column(db.String(100), nullable=True)
    author_website = db.Column(db.String(255), nullable=True)
    license = db.Column(db.String(50), nullable=True)
    min_noteblog_version = db.Column(db.String(20), nullable=True)
    max_noteblog_version = db.Column(db.String(20), nullable=True)
    
    # 主题状态
    is_active = db.Column(db.Boolean, default=False)
    is_system = db.Column(db.Boolean, default=False)  # 是否为系统主题
    install_path = db.Column(db.String(255), nullable=False)  # 主题安装路径
    
    # 主题特性
    supports_widgets = db.Column(db.Boolean, default=True)  # 是否支持小工具
    supports_menus = db.Column(db.Boolean, default=True)  # 是否支持菜单
    supports_customizer = db.Column(db.Boolean, default=True)  # 是否支持自定义
    supports_post_formats = db.Column(db.Boolean, default=False)  # 是否支持文章格式
    
    # 配置信息
    config_schema = db.Column(db.Text, nullable=True)  # JSON格式的配置模式
    config_data = db.Column(db.Text, nullable=True)  # JSON格式的配置数据
    
    # 预览信息
    screenshot = db.Column(db.String(255), nullable=True)  # 预览图路径
    demo_url = db.Column(db.String(255), nullable=True)  # 演示URL
    
    # 时间戳
    installed_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    activated_at = db.Column(db.DateTime, nullable=True)
    
    def __init__(self, name, display_name, version, install_path, **kwargs):
        self.name = name
        self.display_name = display_name
        self.version = version
        self.install_path = install_path
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def activate(self):
        """激活主题"""
        # 先停用其他主题
        Theme.query.filter_by(is_active=True).update({'is_active': False, 'activated_at': None})
        
        self.is_active = True
        self.activated_at = datetime.utcnow()
        db.session.commit()
    
    def deactivate(self):
        """停用主题"""
        self.is_active = False
        db.session.commit()
    
    def get_config(self):
        """获取主题配置"""
        if self.config_data:
            try:
                return json.loads(self.config_data)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_config(self, config_dict):
        """设置主题配置"""
        self.config_data = json.dumps(config_dict, ensure_ascii=False, indent=2)
        db.session.commit()
    
    def get_config_schema(self):
        """获取配置模式"""
        if self.config_schema:
            try:
                return json.loads(self.config_schema)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_config_schema(self, schema_dict):
        """设置配置模式"""
        self.config_schema = json.dumps(schema_dict, ensure_ascii=False, indent=2)
        db.session.commit()
    
    def has_config(self):
        """是否有配置"""
        return bool(self.config_schema)
    
    def is_compatible(self, noteblog_version):
        """检查版本兼容性"""
        if not self.min_noteblog_version and not self.max_noteblog_version:
            return True
        
        # 简单的版本比较
        def version_tuple(v):
            return tuple(map(int, (v.split("."))))
        
        current_version = version_tuple(noteblog_version)
        
        if self.min_noteblog_version:
            min_version = version_tuple(self.min_noteblog_version)
            if current_version < min_version:
                return False
        
        if self.max_noteblog_version:
            max_version = version_tuple(self.max_noteblog_version)
            if current_version > max_version:
                return False
        
        return True
    
    def get_template_path(self, template_name):
        """获取模板路径"""
        import os
        return os.path.join(self.install_path, 'templates', template_name)
    
    def get_static_path(self, static_file):
        """获取静态文件路径"""
        import os
        return os.path.join(self.install_path, 'static', static_file)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'version': self.version,
            'author': self.author,
            'author_website': self.author_website,
            'license': self.license,
            'min_noteblog_version': self.min_noteblog_version,
            'max_noteblog_version': self.max_noteblog_version,
            'is_active': self.is_active,
            'is_system': self.is_system,
            'install_path': self.install_path,
            'supports_widgets': self.supports_widgets,
            'supports_menus': self.supports_menus,
            'supports_customizer': self.supports_customizer,
            'supports_post_formats': self.supports_post_formats,
            'has_config': self.has_config(),
            'config': self.get_config(),
            'config_schema': self.get_config_schema(),
            'screenshot': self.screenshot,
            'demo_url': self.demo_url,
            'installed_at': self.installed_at.isoformat() if self.installed_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'activated_at': self.activated_at.isoformat() if self.activated_at else None
        }
    
    def __repr__(self):
        return f'<Theme {self.name}>'

class ThemeHook(db.Model):
    """主题钩子模型"""
    __tablename__ = 'theme_hooks'
    
    id = db.Column(db.Integer, primary_key=True)
    theme_id = db.Column(db.Integer, db.ForeignKey('themes.id'), nullable=False)
    hook_name = db.Column(db.String(100), nullable=False, index=True)
    hook_type = db.Column(db.String(20), nullable=False)  # action, filter, template
    callback_function = db.Column(db.String(255), nullable=False)
    priority = db.Column(db.Integer, default=10)  # 优先级，数字越小优先级越高
    accepted_args = db.Column(db.Integer, default=1)  # 接受的参数数量
    
    # 关系
    theme = db.relationship('Theme', backref='hooks')
    
    def __init__(self, theme_id, hook_name, hook_type, callback_function, **kwargs):
        self.theme_id = theme_id
        self.hook_name = hook_name
        self.hook_type = hook_type
        self.callback_function = callback_function
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'theme_id': self.theme_id,
            'theme_name': self.theme.name if self.theme else None,
            'hook_name': self.hook_name,
            'hook_type': self.hook_type,
            'callback_function': self.callback_function,
            'priority': self.priority,
            'accepted_args': self.accepted_args
        }
    
    def __repr__(self):
        return f'<ThemeHook {self.hook_name} from {self.theme.name}>'
