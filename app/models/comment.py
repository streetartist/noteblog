"""评论模型"""
from datetime import datetime
from app import db
from app.services.markdown_service import markdown_service

class Comment(db.Model):
    """评论模型"""
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_name = db.Column(db.String(100), nullable=True)  # 游客评论时的姓名
    author_email = db.Column(db.String(120), nullable=True)  # 游客评论时的邮箱
    author_website = db.Column(db.String(255), nullable=True)  # 游客评论时的网站
    author_ip = db.Column(db.String(45), nullable=True)  # 评论者IP
    user_agent = db.Column(db.Text, nullable=True)  # 用户代理
    is_approved = db.Column(db.Boolean, default=False)  # 是否已审核
    is_spam = db.Column(db.Boolean, default=False)  # 是否为垃圾评论
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)  # 父评论ID
    like_count = db.Column(db.Integer, default=0)  # 点赞数
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 外键
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 用户评论时的用户ID
    
    # 关系
    parent = db.relationship('Comment', remote_side=[id], backref='replies')
    
    def __init__(self, content, post_id, **kwargs):
        self.content = content
        self.post_id = post_id
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def approve(self):
        """审核通过"""
        self.is_approved = True
        self.is_spam = False
        db.session.commit()
    
    def reject(self):
        """拒绝评论"""
        self.is_approved = False
        db.session.commit()
    
    def mark_as_spam(self):
        """标记为垃圾评论"""
        self.is_spam = True
        self.is_approved = False
        db.session.commit()
    
    def get_reply_count(self):
        """获取回复数量"""
        return Comment.query.filter_by(parent_id=self.id, is_approved=True).count()
    
    def get_replies(self):
        """获取回复"""
        return Comment.query.filter_by(parent_id=self.id, is_approved=True).order_by(db.asc('created_at')).all()
    
    def get_display_name(self):
        """获取显示名称"""
        if self.author_id and self.author:
            return self.author.display_name or self.author.username
        return self.author_name or '匿名用户'
    
    def get_display_email(self):
        """获取显示邮箱"""
        if self.author_id and self.author:
            return self.author.email
        return self.author_email
    
    def get_display_website(self):
        """获取显示网站"""
        if self.author_id and self.author:
            return self.author.website
        return self.author_website

    def get_display_avatar(self):
        """获取显示头像"""
        if self.author_id and self.author:
            return self.author.avatar
        return None
    
    def is_reply(self):
        """是否为回复"""
        return self.parent_id is not None
    
    def can_be_replied(self):
        """是否可以回复"""
        return self.is_approved and not self.is_spam
    
    def get_content_html(self, sanitize=True):
        """获取渲染后的HTML内容"""
        return markdown_service.render(self.content, sanitize)
    
    def is_markdown_content(self):
        """检查内容是否包含Markdown语法"""
        return markdown_service.is_markdown(self.content)
    
    def to_dict(self, include_replies=False, include_html=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'content': self.content,
            'author_name': self.get_display_name(),
            'author_email': self.get_display_email(),
            'author_website': self.get_display_website(),
            'author_avatar': self.get_display_avatar(),
            'is_approved': self.is_approved,
            'is_spam': self.is_spam,
            'parent_id': self.parent_id,
            'like_count': self.like_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'post_id': self.post_id,
            'author_id': self.author_id,
            'is_reply': self.is_reply(),
            'reply_count': self.get_reply_count(),
            'is_markdown': self.is_markdown_content()
        }
        
        if include_html:
            data['content_html'] = self.get_content_html()
        
        if include_replies:
            data['replies'] = [reply.to_dict(include_html=include_html) for reply in self.get_replies()]
        
        return data
    
    def __repr__(self):
        return f'<Comment {self.id} on Post {self.post_id}>'
