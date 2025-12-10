"""
友链插件数据模型
"""
from app import db
from datetime import datetime, timezone


class FriendLink(db.Model):
    """友链模型"""
    __tablename__ = 'friend_links'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, comment='友链名称')
    url = db.Column(db.String(255), nullable=False, comment='友链URL')
    description = db.Column(db.Text, comment='友链描述')
    logo = db.Column(db.String(255), comment='友链Logo URL')
    email = db.Column(db.String(100), comment='联系邮箱')
    sort_order = db.Column(db.Integer, default=0, comment='排序权重')
    is_active = db.Column(db.Boolean, default=True, comment='是否激活')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment='更新时间')
    
    def __repr__(self):
        return f'<FriendLink {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'description': self.description,
            'logo': self.logo,
            'email': self.email,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_active_links(cls):
        """获取激活的友链，按排序权重排序"""
        return cls.query.filter_by(is_active=True).order_by(cls.sort_order.desc(), cls.created_at.asc()).all()
    
    @classmethod
    def get_all_links(cls):
        """获取所有友链"""
        return cls.query.order_by(cls.sort_order.desc(), cls.created_at.asc()).all()
    
    @classmethod
    def get_by_id(cls, link_id):
        """根据ID获取友链"""
        return cls.query.get(link_id)
    
    def save(self):
        """保存友链"""
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False
    
    def delete(self):
        """删除友链"""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False
