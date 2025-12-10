"""文章相关模型"""
from datetime import datetime, timezone
from app import db
from app.services.markdown_service import markdown_service

# 文章标签关联表
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)

class Category(db.Model):
    """分类模型"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # 自引用关系
    parent = db.relationship('Category', remote_side=[id], backref='children')
    # 与文章的关系
    posts = db.relationship('Post', backref='category', lazy='dynamic')
    
    def __init__(self, name, slug, **kwargs):
        self.name = name
        self.slug = slug
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def get_post_count(self):
        """获取该分类下的文章数量"""
        return self.posts.filter_by(status='published').count()

    @property
    def post_count(self):
        """Template helper for published post count."""
        return self.get_post_count()
    
    def get_children_count(self):
        """获取子分类数量"""
        return Category.query.filter_by(parent_id=self.id).count()
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'parent_id': self.parent_id,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'post_count': self.get_post_count(),
            'children_count': self.get_children_count()
        }
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Tag(db.Model):
    """标签模型"""
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    color = db.Column(db.String(7), nullable=True)  # 十六进制颜色值
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __init__(self, name, slug, **kwargs):
        self.name = name
        self.slug = slug
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def get_post_count(self):
        """获取该标签下已发布文章数量"""
        return (
            db.session.query(db.func.count(Post.id))
            .join(post_tags, Post.id == post_tags.c.post_id)
            .filter(
                post_tags.c.tag_id == self.id,
                Post.status == 'published'
            )
            .scalar()
        ) or 0

    @property
    def post_count(self):
        """模板辅助属性，允许缓存结果"""
        if hasattr(self, '_post_count_cache') and self._post_count_cache is not None:
            return self._post_count_cache
        return self.get_post_count()

    @post_count.setter
    def post_count(self, value):
        self._post_count_cache = value
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'color': self.color,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'post_count': self.post_count
        }
    
    def __repr__(self):
        return f'<Tag {self.name}>'

class Post(db.Model):
    """文章模型"""
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text, nullable=True)
    featured_image = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='draft', index=True)  # draft, published, private, trash
    post_type = db.Column(db.String(20), default='post')  # post, page
    comment_status = db.Column(db.String(20), default='open')  # open, closed
    password = db.Column(db.String(255), nullable=True)  # 文章密码保护
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    is_top = db.Column(db.Boolean, default=False)
    seo_title = db.Column(db.String(200), nullable=True)
    seo_description = db.Column(db.String(300), nullable=True)
    seo_keywords = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    published_at = db.Column(db.DateTime, nullable=True)
    
    # 外键
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    
    # 关系
    tags = db.relationship('Tag', secondary=post_tags, lazy='subquery',
                          backref=db.backref('posts', lazy=True))
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, title, content, author_id, **kwargs):
        self.title = title
        self.content = content
        self.author_id = author_id
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def publish(self):
        """发布文章"""
        self.status = 'published'
        self.published_at = datetime.now(timezone.utc)
        db.session.commit()
    
    def unpublish(self):
        """取消发布"""
        self.status = 'draft'
        db.session.commit()
    
    def increment_view(self):
        """增加浏览量"""
        self.view_count += 1
        db.session.commit()
    
    def get_comment_count(self):
        """获取评论数量"""
        return self.comments.filter_by(is_approved=True).count()

    @property
    def comment_count(self):
        """Template helper for approved comment count."""
        return self.get_comment_count()
    
    def get_approved_comments(self):
        """获取已审核的评论"""
        return self.comments.filter_by(is_approved=True).order_by(db.desc('created_at')).all()
    
    def get_content_html(self, sanitize=True):
        """获取渲染后的HTML内容"""
        return markdown_service.render(self.content, sanitize)
    
    def get_excerpt_html(self, length=150, sanitize=True):
        """获取渲染后的HTML摘要"""
        if self.excerpt:
            return markdown_service.render(self.excerpt, sanitize)
        return markdown_service.render_excerpt(self.content, length, sanitize)
    
    def get_toc(self):
        """获取文章目录"""
        return markdown_service.get_toc(self.content)
    
    def is_markdown_content(self):
        """检查内容是否包含Markdown语法"""
        return markdown_service.is_markdown(self.content)
    
    def to_dict(self, include_content=True, include_html=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'excerpt': self.excerpt,
            'featured_image': self.featured_image,
            'status': self.status,
            'post_type': self.post_type,
            'comment_status': self.comment_status,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'is_featured': self.is_featured,
            'is_top': self.is_top,
            'seo_title': self.seo_title,
            'seo_description': self.seo_description,
            'seo_keywords': self.seo_keywords,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'author': self.author.to_dict() if self.author else None,
            'category': self.category.to_dict() if self.category else None,
            'tags': [tag.to_dict() for tag in self.tags],
            'comment_count': self.get_comment_count(),
            'is_markdown': self.is_markdown_content()
        }
        if include_content:
            data['content'] = self.content
        if include_html:
            data['content_html'] = self.get_content_html()
            data['excerpt_html'] = self.get_excerpt_html()
            data['toc'] = self.get_toc()
        return data
    
    def __repr__(self):
        return f'<Post {self.title}>'
