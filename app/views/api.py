"""
API 视图
"""
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.post import Post, Category, Tag
from app.models.comment import Comment
from app.models.setting import SettingManager
from app.services.plugin_manager import plugin_manager

bp = Blueprint('api', __name__)

def api_response(data=None, message='', status=200, error=None):
    """统一API响应格式"""
    response = {
        'status': status,
        'message': message,
        'data': data
    }
    if error:
        response['error'] = error
    return jsonify(response), status

# 文章 API
@bp.route('/posts')
def api_posts():
    """获取文章列表"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)
    status = request.args.get('status', 'published')
    category_id = request.args.get('category_id', type=int)
    tag_id = request.args.get('tag_id', type=int)
    
    query = Post.query
    if status:
        query = query.filter_by(status=status)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if tag_id:
        tag = Tag.query.get(tag_id)
        if tag:
            query = query.filter(Post.tags.contains(tag))
    
    posts = query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    data = {
        'posts': [post.to_dict(include_content=False) for post in posts.items],
        'pagination': {
            'page': posts.page,
            'per_page': posts.per_page,
            'total': posts.total,
            'pages': posts.pages,
            'has_prev': posts.has_prev,
            'has_next': posts.has_next
        }
    }
    
    return api_response(data=data)

@bp.route('/posts/<int:post_id>')
def api_post(post_id):
    """获取单篇文章"""
    post = Post.query.get_or_404(post_id)
    
    # 如果是未发布的文章，需要登录且是作者或管理员
    if post.status != 'published':
        if not current_user.is_authenticated or (not current_user.is_admin and post.author_id != current_user.id):
            return api_response(message='无权访问', status=403)
    
    return api_response(data=post.to_dict())

@bp.route('/posts', methods=['POST'])
@login_required
def api_create_post():
    """创建文章"""
    data = request.get_json()
    
    if not data or not data.get('title') or not data.get('content'):
        return api_response(message='标题和内容不能为空', status=400)
    
    # 生成 slug
    import re
    slug = re.sub(r'[^\w\s-]', '', data['title']).strip().lower()
    slug = re.sub(r'[-\s]+', '-', slug)
    
    # 确保 slug 唯一
    original_slug = slug
    counter = 1
    while Post.query.filter_by(slug=slug).first():
        slug = f"{original_slug}-{counter}"
        counter += 1
    
    post = Post(
        title=data['title'],
        slug=slug,
        content=data['content'],
        excerpt=data.get('excerpt', ''),
        author_id=current_user.id,
        category_id=data.get('category_id'),
        status=data.get('status', 'draft'),
        post_type=data.get('post_type', 'post'),
        comment_status=data.get('comment_status', 'open'),
        featured_image=data.get('featured_image', ''),
        seo_title=data.get('seo_title', ''),
        seo_description=data.get('seo_description', ''),
        seo_keywords=data.get('seo_keywords', '')
    )
    
    # 处理标签
    if 'tags' in data and data['tags']:
        for tag_name in data['tags']:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name, slug=tag_name.lower().replace(' ', '-'))
                db.session.add(tag)
            post.tags.append(tag)
    
    # 触发钩子
    plugin_manager.do_action('before_post_save', post=post)
    
    db.session.add(post)
    db.session.commit()
    
    # 触发钩子
    plugin_manager.do_action('after_post_save', post=post)
    
    return api_response(data=post.to_dict(), message='文章创建成功', status=201)

@bp.route('/posts/<int:post_id>', methods=['PUT'])
@login_required
def api_update_post(post_id):
    """更新文章"""
    post = Post.query.get_or_404(post_id)
    
    # 检查权限
    if not current_user.is_admin and post.author_id != current_user.id:
        return api_response(message='无权修改', status=403)
    
    data = request.get_json()
    if not data:
        return api_response(message='无效数据', status=400)
    
    # 更新字段
    if 'title' in data:
        post.title = data['title']
    if 'content' in data:
        post.content = data['content']
    if 'excerpt' in data:
        post.excerpt = data['excerpt']
    if 'category_id' in data:
        post.category_id = data['category_id']
    if 'status' in data:
        post.status = data['status']
    if 'comment_status' in data:
        post.comment_status = data['comment_status']
    if 'featured_image' in data:
        post.featured_image = data['featured_image']
    if 'seo_title' in data:
        post.seo_title = data['seo_title']
    if 'seo_description' in data:
        post.seo_description = data['seo_description']
    if 'seo_keywords' in data:
        post.seo_keywords = data['seo_keywords']
    
    # 处理标签
    if 'tags' in data:
        post.tags.clear()
        for tag_name in data['tags']:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name, slug=tag_name.lower().replace(' ', '-'))
                db.session.add(tag)
            post.tags.append(tag)
    
    # 触发钩子
    plugin_manager.do_action('before_post_update', post=post)
    
    db.session.commit()
    
    # 触发钩子
    plugin_manager.do_action('after_post_update', post=post)
    
    return api_response(data=post.to_dict(), message='文章更新成功')

@bp.route('/posts/<int:post_id>', methods=['DELETE'])
@login_required
def api_delete_post(post_id):
    """删除文章"""
    post = Post.query.get_or_404(post_id)
    
    # 检查权限
    if not current_user.is_admin and post.author_id != current_user.id:
        return api_response(message='无权删除', status=403)
    
    # 触发钩子
    plugin_manager.do_action('before_post_delete', post=post)
    
    db.session.delete(post)
    db.session.commit()
    
    # 触发钩子
    plugin_manager.do_action('after_post_delete', post=post)
    
    return api_response(message='文章删除成功')

# 分类 API
@bp.route('/categories')
def api_categories():
    """获取分类列表"""
    categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order, Category.name).all()
    data = [category.to_dict() for category in categories]
    return api_response(data=data)

@bp.route('/categories', methods=['POST'])
@login_required
def api_create_category():
    """创建分类"""
    if not current_user.is_admin:
        return api_response(message='需要管理员权限', status=403)
    
    data = request.get_json()
    if not data or not data.get('name'):
        return api_response(message='分类名称不能为空', status=400)
    
    # 生成 slug
    import re
    slug = data.get('slug', '')
    if not slug:
        slug = re.sub(r'[^\w\s-]', '', data['name']).strip().lower()
        slug = re.sub(r'[-\s]+', '-', slug)
    
    # 检查 slug 是否已存在
    if Category.query.filter_by(slug=slug).first():
        return api_response(message='分类别名已存在', status=400)
    
    category = Category(
        name=data['name'],
        slug=slug,
        description=data.get('description', ''),
        parent_id=data.get('parent_id'),
        sort_order=data.get('sort_order', 0)
    )
    
    db.session.add(category)
    db.session.commit()
    
    return api_response(data=category.to_dict(), message='分类创建成功', status=201)

# 标签 API
@bp.route('/tags')
def api_tags():
    """获取标签列表"""
    tags = Tag.query.order_by(Tag.name).all()
    data = [tag.to_dict() for tag in tags]
    return api_response(data=data)

# 评论 API
@bp.route('/comments')
def api_comments():
    """获取评论列表"""
    post_id = request.args.get('post_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)
    
    query = Comment.query.filter_by(is_approved=True)
    if post_id:
        query = query.filter_by(post_id=post_id)
    
    comments = query.order_by(Comment.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    data = {
        'comments': [comment.to_dict() for comment in comments.items],
        'pagination': {
            'page': comments.page,
            'per_page': comments.per_page,
            'total': comments.total,
            'pages': comments.pages,
            'has_prev': comments.has_prev,
            'has_next': comments.has_next
        }
    }
    
    return api_response(data=data)

@bp.route('/comments', methods=['POST'])
def api_create_comment():
    """创建评论"""
    if not SettingManager.get('allow_comments', True):
        return api_response(message='评论功能已关闭', status=403)
    
    data = request.get_json()
    if not data or not data.get('content') or not data.get('post_id'):
        return api_response(message='内容不能为空', status=400)
    
    post = Post.query.get(data['post_id'])
    if not post or post.status != 'published':
        return api_response(message='文章不存在', status=404)
    
    if post.comment_status != 'open':
        return api_response(message='该文章不允许评论', status=403)
    
    comment = Comment(
        content=data['content'],
        post_id=data['post_id'],
        parent_id=data.get('parent_id'),
        author_ip=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')
    )
    
    # 如果用户已登录，设置作者信息
    if current_user.is_authenticated:
        comment.author_id = current_user.id
    else:
        # 游客评论
        comment.author_name = data.get('author_name', '')
        comment.author_email = data.get('author_email', '')
        comment.author_website = data.get('author_website', '')
        
        if not comment.author_name or not comment.author_email:
            return api_response(message='请填写姓名和邮箱', status=400)
    
    # 触发钩子
    plugin_manager.do_action('before_comment_save', comment=comment)
    
    db.session.add(comment)
    db.session.commit()
    
    # 如果需要审核
    if SettingManager.get('comment_moderation', True):
        comment.is_approved = False
        db.session.commit()
        message = '评论已提交，等待审核'
    else:
        comment.is_approved = True
        db.session.commit()
        message = '评论发表成功'
    
    # 触发钩子
    plugin_manager.do_action('after_comment_save', comment=comment)
    
    return api_response(
        data=comment.to_dict() if comment.is_approved else None,
        message=message,
        status=201
    )

@bp.route('/comments/<int:comment_id>', methods=['PUT'])
@login_required
def api_update_comment(comment_id):
    """更新评论内容"""
    comment = Comment.query.get_or_404(comment_id)

    if not current_user.is_admin and comment.author_id != current_user.id:
        return api_response(message='没有权限编辑该评论', status=403)

    data = request.get_json() or {}
    content = (data.get('content') or '').strip()

    if not content:
        return api_response(message='内容不能为空', status=400)

    requires_review = not current_user.is_admin

    plugin_manager.do_action('before_comment_update', comment=comment)

    comment.content = content
    comment.updated_at = datetime.utcnow()
    if requires_review:
        comment.is_approved = False
    db.session.commit()

    plugin_manager.do_action('after_comment_update', comment=comment)

    message = '评论已更新'
    if requires_review:
        message = '评论已更新，等待审核'

    return api_response(
        data=comment.to_dict(include_html=True),
        message=message
    )

# 用户 API
@bp.route('/users')
@login_required
def api_users():
    """获取用户列表"""
    if not current_user.is_admin:
        return api_response(message='需要管理员权限', status=403)
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)
    
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    data = {
        'users': [user.to_dict() for user in users.items],
        'pagination': {
            'page': users.page,
            'per_page': users.per_page,
            'total': users.total,
            'pages': users.pages,
            'has_prev': users.has_prev,
            'has_next': users.has_next
        }
    }
    
    return api_response(data=data)

@bp.route('/users/current')
@login_required
def api_current_user():
    """获取当前用户信息"""
    return api_response(data=current_user.to_dict())

# 设置 API
@bp.route('/settings')
def api_settings():
    """获取公开设置"""
    settings = SettingManager.get_public()
    return api_response(data=settings)

@bp.route('/settings/all')
@login_required
def api_all_settings():
    """获取所有设置"""
    if not current_user.is_admin:
        return api_response(message='需要管理员权限', status=403)
    
    settings = {}
    all_settings = SettingManager.query.all()
    for setting in all_settings:
        settings[setting.key] = setting.get_typed_value()
    
    return api_response(data=settings)

# 搜索 API
@bp.route('/search')
def api_search():
    """搜索"""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)
    search_type = request.args.get('type', 'posts')  # posts, users, etc.
    
    if not query:
        return api_response(message='搜索关键词不能为空', status=400)
    
    if search_type == 'posts':
        results = Post.query.filter(
            Post.status=='published',
            db.or_(
                Post.title.contains(query),
                Post.content.contains(query),
                Post.excerpt.contains(query)
            )
        ).order_by(Post.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        data = {
            'results': [post.to_dict(include_content=False) for post in results.items],
            'pagination': {
                'page': results.page,
                'per_page': results.per_page,
                'total': results.total,
                'pages': results.pages,
                'has_prev': results.has_prev,
                'has_next': results.has_next
            }
        }
    else:
        data = {'results': [], 'pagination': {}}
    
    return api_response(data=data)

# 统计 API
@bp.route('/stats')
@login_required
def api_stats():
    """获取统计信息"""
    if not current_user.is_admin:
        return api_response(message='需要管理员权限', status=403)
    
    stats = {
        'posts': {
            'total': Post.query.count(),
            'published': Post.query.filter_by(status='published').count(),
            'draft': Post.query.filter_by(status='draft').count(),
            'private': Post.query.filter_by(status='private').count()
        },
        'users': {
            'total': User.query.count(),
            'active': User.query.filter_by(is_active=True).count(),
            'admin': User.query.filter_by(is_admin=True).count()
        },
        'comments': {
            'total': Comment.query.count(),
            'approved': Comment.query.filter_by(is_approved=True).count(),
            'pending': Comment.query.filter_by(is_approved=False).count(),
            'spam': Comment.query.filter_by(is_spam=True).count()
        },
        'categories': Category.query.count(),
        'tags': Tag.query.count()
    }
    
    return api_response(data=stats)

# 错误处理
@bp.errorhandler(404)
def api_not_found(error):
    return api_response(message='资源未找到', status=404)

@bp.errorhandler(500)
def api_internal_error(error):
    db.session.rollback()
    return api_response(message='服务器内部错误', status=500)
