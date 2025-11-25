"""
系统设置模型
"""
from datetime import datetime
import json
from app import db

class Setting(db.Model):
    """系统设置模型"""
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)
    value_type = db.Column(db.String(20), default='string')  # string, integer, boolean, json
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), default='general')  # general, theme, plugin, security, etc.
    is_public = db.Column(db.Boolean, default=False)  # 是否为公开设置（前端可访问）
    is_editable = db.Column(db.Boolean, default=True)  # 是否可编辑
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, key, value=None, **kwargs):
        self.key = key
        self.value = value
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def get_typed_value(self):
        """获取类型化的值"""
        if self.value is None:
            return None
        
        if self.value_type == 'integer':
            try:
                return int(self.value)
            except ValueError:
                return 0
        elif self.value_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.value_type == 'json':
            try:
                return json.loads(self.value)
            except json.JSONDecodeError:
                return {}
        else:
            return self.value
    
    def set_typed_value(self, value):
        """设置类型化的值"""
        if self.value_type == 'json':
            self.value = json.dumps(value, ensure_ascii=False, indent=2)
        else:
            self.value = str(value)
        db.session.commit()
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'key': self.key,
            'value': self.get_typed_value(),
            'value_type': self.value_type,
            'description': self.description,
            'category': self.category,
            'is_public': self.is_public,
            'is_editable': self.is_editable,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Setting {self.key}>'

class SettingManager:
    """设置管理器"""
    
    @staticmethod
    def get(key, default=None):
        """获取设置值"""
        try:
            setting = Setting.query.filter_by(key=key).first()
            if setting:
                return setting.get_typed_value()
            return default
        except Exception:
            # 如果数据库连接失败，返回默认值
            return default
    
    @staticmethod
    def set(key, value, value_type='string', description=None, category='general', 
            is_public=False, is_editable=True):
        """设置值"""
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            setting.value_type = value_type
            if description:
                setting.description = description
            setting.category = category
            setting.is_public = is_public
            setting.is_editable = is_editable
            setting.set_typed_value(value)
        else:
            setting = Setting(
                key=key,
                value_type=value_type,
                description=description,
                category=category,
                is_public=is_public,
                is_editable=is_editable
            )
            setting.set_typed_value(value)
            db.session.add(setting)
            db.session.commit()
    
    @staticmethod
    def get_category(category):
        """获取指定分类的所有设置"""
        settings = Setting.query.filter_by(category=category).all()
        return {setting.key: setting.get_typed_value() for setting in settings}
    
    @staticmethod
    def get_public():
        """获取所有公开设置"""
        settings = Setting.query.filter_by(is_public=True).all()
        return {setting.key: setting.get_typed_value() for setting in settings}
    
    @staticmethod
    def init_default_settings():
        """初始化默认设置"""
        default_settings = [
            # 基本设置
            ('site_title', 'Noteblog', 'string', '网站标题', 'general', True),
            ('site_description', '基于 Flask 的可扩展博客框架', 'string', '网站描述', 'general', True),
            ('site_keywords', 'blog, flask, noteblog', 'string', '网站关键词', 'general', True),
            ('site_url', 'http://localhost:5000', 'string', '网站URL', 'general', True),
            ('admin_email', 'admin@example.com', 'string', '管理员邮箱', 'general', False),
            
            # 文章设置
            ('posts_per_page', '10', 'integer', '每页文章数量', 'general', True),
            ('default_category', '1', 'integer', '默认分类ID', 'general', False),
            ('allow_comments', 'true', 'boolean', '允许评论', 'general', True),
            ('comment_moderation', 'true', 'boolean', '评论需要审核', 'general', False),
            
            # 用户设置
            ('allow_registration', 'true', 'boolean', '允许用户注册', 'general', True),
            ('default_user_role', 'author', 'string', '默认用户角色', 'general', False),
            
            # 安全设置
            ('enable_captcha', 'false', 'boolean', '启用验证码', 'security', False),
            ('session_timeout', '3600', 'integer', '会话超时时间（秒）', 'security', False),
            
            # 主题设置
            ('active_theme', 'default', 'string', '当前激活主题', 'theme', False),
            ('theme_config', '{}', 'json', '主题配置', 'theme', False),
            
            # 插件设置
            ('active_plugins', '[]', 'json', '激活的插件列表', 'plugin', False),
        ]
        
        for setting_data in default_settings:
            key, value, value_type, description, category, is_public = setting_data
            if not Setting.query.filter_by(key=key).first():
                SettingManager.set(key, value, value_type, description, category, is_public)
    
    @staticmethod
    def delete(key):
        """删除设置"""
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            db.session.delete(setting)
            db.session.commit()
            return True
        return False
