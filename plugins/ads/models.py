"""
广告插件数据模型
"""
from app import db
from datetime import datetime, timezone


class AdSlot(db.Model):
    """广告位模型"""
    __tablename__ = 'ad_slots'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, comment='广告位名称')
    ad_code = db.Column(db.Text, nullable=False, comment='广告代码(HTML)')
    slot_type = db.Column(db.String(20), default='sidebar', comment='广告位置: sidebar/header/footer')
    sort_order = db.Column(db.Integer, default=0, comment='排序权重')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<AdSlot {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'ad_code': self.ad_code,
            'slot_type': self.slot_type,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def get_active_by_type(cls, slot_type='sidebar'):
        return cls.query.filter_by(is_active=True, slot_type=slot_type)\
            .order_by(cls.sort_order.desc(), cls.created_at.asc()).all()

    @classmethod
    def get_all(cls):
        return cls.query.order_by(cls.sort_order.desc(), cls.created_at.asc()).all()

    @classmethod
    def get_by_id(cls, slot_id):
        return cls.query.get(slot_id)

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False
