"""
主要视图
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.post import Post, Category, Tag
from app.models.comment import Comment
from app.models.setting import SettingManager
from app.services.plugin_manager import plugin_manager
from app.services.theme_manager import theme_manager

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """首页"""
    page = request.args.get('page', 1, type=int)
    per_page = SettingManager.get('posts_per_page', 10)
    
    # 获取已发布的文章
    posts = Post.query.filter_by(status='published').order_by(
        Post.is_top.desc(), Post.published_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    # 获取分类和标签
    categories = Category.query.filter_by(is_active=True).all()
    tags = Tag.query.all()
    
    # 触发钩子
    plugin_manager.do_action('before_index_render', posts=posts)
    
    # 准备模板上下文
    context = {
        'posts': posts,
        'categories': categories,
        'tags': tags,
        'site_title': SettingManager.get('site_title', 'Noteblog'),
        'site_description': SettingManager.get('site_description', ''),
        'current_user': current_user
    }
    
    # 应用过滤器
    context = plugin_manager.apply_filters('index_context', context)
    
    # 使用主题模板渲染
    return theme_manager.render_template('index.html', **context)

@bp.route('/post/<slug>')
def post_detail(slug):
    """文章详情"""
    post = Post.query.filter_by(slug=slug, status='published').first_or_404()
    
    # 增加浏览量
    post.increment_view()
    
    # 获取评论
    comments = post.get_approved_comments()
    
    # 触发钩子
    plugin_manager.do_action('before_post_render', post=post)
    
    # 准备模板上下文
    context = {
        'post': post,
        'comments': comments,
        'site_title': f"{post.title} - {SettingManager.get('site_title', 'Noteblog')}",
        'current_user': current_user
    }
    
    # 应用过滤器
    context = plugin_manager.apply_filters('post_context', context, post)
    
    return theme_manager.render_template('post.html', **context)

@bp.route('/category/<slug>')
def category(slug):
    """分类页面"""
    category = Category.query.filter_by(slug=slug, is_active=True).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = SettingManager.get('posts_per_page', 10)
    
    posts = Post.query.filter_by(
        category_id=category.id, status='published'
    ).order_by(Post.published_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    context = {
        'category': category,
        'posts': posts,
        'site_title': f"{category.name} - {SettingManager.get('site_title', 'Noteblog')}",
        'current_user': current_user
    }
    
    return theme_manager.render_template('category.html', **context)

@bp.route('/tag/<slug>')
def tag(slug):
    """标签页面"""
    tag = Tag.query.filter_by(slug=slug).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = SettingManager.get('posts_per_page', 10)
    
    # 获取包含该标签的文章
    posts_query = Post.query.filter(
        Post.tags.contains(tag), Post.status=='published'
    ).order_by(Post.published_at.desc())
    
    posts = posts_query.paginate(page=page, per_page=per_page, error_out=False)
    
    context = {
        'tag': tag,
        'posts': posts,
        'site_title': f"{tag.name} - {SettingManager.get('site_title', 'Noteblog')}",
        'current_user': current_user
    }
    
    return theme_manager.render_template('tag.html', **context)

@bp.route('/search')
def search():
    """搜索页面"""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = SettingManager.get('posts_per_page', 10)
    
    posts = []
    total = 0
    
    if query:
        # 简单的搜索实现
        posts_query = Post.query.filter(
            Post.status=='published',
            db.or_(
                Post.title.contains(query),
                Post.content.contains(query),
                Post.excerpt.contains(query)
            )
        ).order_by(Post.published_at.desc())
        
        posts = posts_query.paginate(page=page, per_page=per_page, error_out=False)
        total = posts.total
    
    context = {
        'query': query,
        'posts': posts,
        'total': total,
        'site_title': f"搜索: {query} - {SettingManager.get('site_title', 'Noteblog')}",
        'current_user': current_user
    }
    
    return theme_manager.render_template('search.html', **context)

@bp.route('/comment', methods=['POST'])
def add_comment():
    """添加评论"""
    if not SettingManager.get('allow_comments', True):
        return jsonify({'error': '评论功能已关闭'}), 403
    
    post_id = request.form.get('post_id', type=int)
    content = request.form.get('content', '').strip()
    parent_id = request.form.get('parent_id', type=int)
    
    if not post_id or not content:
        return jsonify({'error': '参数错误'}), 400
    
    post = Post.query.get_or_404(post_id)
    
    if post.comment_status != 'open':
        return jsonify({'error': '该文章不允许评论'}), 403
    
    # 创建评论
    comment = Comment(
        content=content,
        post_id=post_id,
        parent_id=parent_id,
        author_ip=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')
    )
    
    # 如果用户已登录，设置作者信息
    if current_user.is_authenticated:
        comment.author_id = current_user.id
    else:
        # 游客评论
        comment.author_name = request.form.get('author_name', '').strip()
        comment.author_email = request.form.get('author_email', '').strip()
        comment.author_website = request.form.get('author_website', '').strip()
        
        if not comment.author_name or not comment.author_email:
            return jsonify({'error': '请填写姓名和邮箱'}), 400
    
    # 触发钩子
    plugin_manager.do_action('before_comment_save', comment=comment)
    
    # 保存评论
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
    
    return jsonify({
        'success': True,
        'message': message,
        'comment': comment.to_dict() if comment.is_approved else None
    })

@bp.route('/archives')
def archives():
    """归档页面"""
    posts = Post.query.filter_by(status='published').order_by(
        Post.published_at.desc()
    ).all()
    
    # 按年份分组
    archives = {}
    for post in posts:
        year = post.published_at.year if post.published_at else post.created_at.year
        if year not in archives:
            archives[year] = []
        archives[year].append(post)
    
    context = {
        'archives': archives,
        'site_title': f"归档 - {SettingManager.get('site_title', 'Noteblog')}",
        'current_user': current_user
    }
    
    return theme_manager.render_template('archives.html', **context)


@bp.route('/categories')
def categories_list():
    """分类列表页面"""
    categories = Category.query.filter_by(is_active=True).all()
    context = {
        'categories': categories,
        'site_title': f"分类 - {SettingManager.get('site_title', 'Noteblog')}",
        'current_user': current_user
    }
    return theme_manager.render_template('categories.html', **context)


@bp.route('/tags')
def tags_list():
    """标签列表页面"""
    tags = Tag.query.all()
    context = {
        'tags': tags,
        'site_title': f"标签 - {SettingManager.get('site_title', 'Noteblog')}",
        'current_user': current_user
    }
    return theme_manager.render_template('tags.html', **context)

@bp.route('/page/<slug>')
def page(slug):
    """页面"""
    page = Post.query.filter_by(slug=slug, post_type='page', status='published').first_or_404()
    
    # 增加浏览量
    page.increment_view()
    
    context = {
        'page': page,
        'site_title': f"{page.title} - {SettingManager.get('site_title', 'Noteblog')}",
        'current_user': current_user
    }
    
    return theme_manager.render_template('page.html', **context)

@bp.route('/feed')
def feed():
    """RSS 订阅"""
    from flask import Response
    
    posts = Post.query.filter_by(status='published').order_by(
        Post.published_at.desc()
    ).limit(20).all()
    
    # 生成 RSS XML
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>{SettingManager.get('site_title', 'Noteblog')}</title>
        <description>{SettingManager.get('site_description', '')}</description>
        <link>{SettingManager.get('site_url', '')}</link>
        <language>zh-CN</language>"""
    
    for post in posts:
        xml += f"""
        <item>
            <title>{post.title}</title>
            <description>{post.excerpt or post.content[:200]}...</description>
            <link>{SettingManager.get('site_url', '')}/post/{post.slug}</link>
            <pubDate>{post.published_at or post.created_at}</pubDate>
        </item>"""
    
    xml += """
    </channel>
</rss>"""
    
    return Response(xml, mimetype='application/rss+xml')
