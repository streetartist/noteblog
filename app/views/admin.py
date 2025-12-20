"""
管理后台视图
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timezone
import os
import uuid
from app import db
from app.models.user import User
from app.models.post import Post, Category, Tag
from app.models.comment import Comment
from app.models.plugin import Plugin
from app.models.theme import Theme
from app.models.setting import SettingManager
from app.services.plugin_manager import plugin_manager
from app.services.theme_manager import theme_manager
from app.utils import path_utils
from app.services.backup_service import (
    create_backup_archive,
    restore_backup_from_zip,
    BackupError,
)
from werkzeug.utils import secure_filename

bp = Blueprint('admin', __name__)


def _collect_editor_hooks(mode: str, post=None):
    """收集文章编辑页可用的插件钩子内容"""
    hooks = {
        'sidebar_top': [],
        'sidebar_bottom': [],
        'excerpt_tools': [],
        'content_tools': [],
        'after_form': [],
        'scripts': []
    }

    # 在跳过插件初始化时直接返回空钩子，避免无谓查询
    if os.getenv('SKIP_PLUGIN_INIT', '0') == '1':
        return hooks

    try:
        return plugin_manager.apply_filters('admin_post_editor_hooks', hooks, mode, post)
    except Exception as exc:
        current_app.logger.error('收集文章编辑钩子失败: %s', exc)
        return hooks

def _get_base_context(page_title_suffix):
    """获取管理后台页面的基础上下文"""
    site_brand = SettingManager.get('site_title', 'Noteblog')
    
    # 定义基础导航项
    navigation_items = [
        {'name': 'dashboard', 'title': '仪表板', 'url': url_for('admin.dashboard'), 'icon': 'el-icon-s-home'},
        {'name': 'posts', 'title': '文章管理', 'url': url_for('admin.posts'), 'icon': 'el-icon-document'},
        {'name': 'categories', 'title': '分类管理', 'url': url_for('admin.categories'), 'icon': 'el-icon-folder'},
        {'name': 'comments', 'title': '评论管理', 'url': url_for('admin.comments'), 'icon': 'el-icon-chat-dot-round'},
        {'name': 'users', 'title': '用户管理', 'url': url_for('admin.users'), 'icon': 'el-icon-user'},
        {'name': 'themes', 'title': '主题管理', 'url': url_for('admin.themes'), 'icon': 'el-icon-picture-outline'},
        {'name': 'plugins', 'title': '插件管理', 'url': url_for('admin.plugins'), 'icon': 'el-icon-s-cooperation'},
        {'name': 'settings', 'title': '系统设置', 'url': url_for('admin.settings'), 'icon': 'el-icon-s-tools'},
    ]
    
    # 应用 admin_navigation 钩子
    navigation_items = plugin_manager.apply_filters('admin_navigation', navigation_items)

    context = {
        'site_title': site_brand,
        'page_title': f"{page_title_suffix} - {site_brand} 管理后台",
        'current_user': current_user,
        'navigation_items': navigation_items
    }
    return context

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('需要管理员权限', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def dashboard():
    """仪表板"""
    # 统计数据
    stats = {
        'total_posts': Post.query.count(),
        'published_posts': Post.query.filter_by(status='published').count(),
        'draft_posts': Post.query.filter_by(status='draft').count(),
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'total_comments': Comment.query.count(),
        'pending_comments': Comment.query.filter_by(is_approved=False).count(),
        'total_categories': Category.query.count(),
        'total_tags': Tag.query.count(),
        'active_plugins': Plugin.query.filter_by(is_active=True).count(),
        'total_plugins': Plugin.query.count(),
        'active_theme': Theme.query.filter_by(is_active=True).first()
    }
    
    # 最新文章
    latest_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    
    # 最新评论
    latest_comments = Comment.query.order_by(Comment.created_at.desc()).limit(5).all()
    
    context = _get_base_context('仪表板')
    context.update({
        'stats': stats,
        'latest_posts': latest_posts,
        'latest_comments': latest_comments,
    })
    
    return theme_manager.render_template('admin/dashboard.html', **context)

# 文章管理
@bp.route('/posts')
@login_required
@admin_required
def posts():
    """文章列表"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = Post.query
    if status:
        query = query.filter_by(status=status)
    
    posts = query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    context = _get_base_context('文章管理')
    context.update({
        'posts': posts,
        'status': status,
    })
    
    return theme_manager.render_template('admin/posts.html', **context)

@bp.route('/posts/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_post():
    """创建文章"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        excerpt = request.form.get('excerpt', '').strip()
        category_id = request.form.get('category_id', type=int)
        status = request.form.get('status', 'draft')
        post_type = request.form.get('post_type', 'post')
        comment_status = request.form.get('comment_status', 'open')
        featured_image = request.form.get('featured_image', '').strip()
        seo_title = request.form.get('seo_title', '').strip()
        seo_description = request.form.get('seo_description', '').strip()
        seo_keywords = request.form.get('seo_keywords', '').strip()
        
        if not title or not content:
            flash('标题和内容不能为空', 'error')
            return theme_manager.render_template('admin/create_post.html')
        
        # 生成 slug
        import re
        from pypinyin import lazy_pinyin, Style
        
        # 转换为拼音
        pinyin_list = lazy_pinyin(title, style=Style.NORMAL)
        slug = '-'.join(pinyin_list)
        
        # 清理特殊字符
        slug = re.sub(r'[^\w\s-]', '', slug).strip().lower()
        slug = re.sub(r'[-\s]+', '-', slug)
        
        # 确保 slug 唯一
        original_slug = slug
        counter = 1
        while Post.query.filter_by(slug=slug).first():
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        # 创建文章
        post = Post(
            title=title,
            slug=slug,
            content=content,
            excerpt=excerpt,
            author_id=current_user.id,
            category_id=category_id,
            status=status,
            post_type=post_type,
            comment_status=comment_status,
            featured_image=featured_image,
            seo_title=seo_title,
            seo_description=seo_description,
            seo_keywords=seo_keywords
        )
        
        # 处理标签
        tag_names = request.form.get('tags', '').strip()
        if tag_names:
            tag_list = [tag.strip() for tag in tag_names.split(',') if tag.strip()]
            for tag_name in tag_list:
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
        
        flash('文章创建成功', 'success')
        return redirect(url_for('admin.posts'))
    
    categories = Category.query.filter_by(is_active=True).all()
    tags = Tag.query.all()
    
    upload_limit_bytes = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
    upload_limit_mb = max(1, upload_limit_bytes // (1024 * 1024))

    context = _get_base_context('创建文章')
    context.update({
        'categories': categories,
        'tags': tags,
        'upload_limit_mb': upload_limit_mb,
        'editor_plugin_hooks': _collect_editor_hooks('create')
    })
    
    return theme_manager.render_template('admin/create_post.html', **context)

@bp.route('/uploads', methods=['POST'])
@login_required
@admin_required
def upload_media():
    """上传后台文章所需的图片或资源"""
    file = request.files.get('file') or request.files.get('image')
    if not file:
        current_app.logger.warning('上传失败：未收到文件字段')
        return jsonify({'success': 0, 'message': '请选择要上传的文件'}), 400

    original_filename = secure_filename(file.filename or '')
    extension = ''
    if '.' in original_filename:
        extension = original_filename.rsplit('.', 1)[1].lower()

    mime_type = (file.mimetype or '').lower()
    mime_to_ext = {
        'image/jpeg': 'jpg',
        'image/png': 'png',
        'image/gif': 'gif',
        'image/webp': 'webp'
    }

    if not extension:
        extension = mime_to_ext.get(mime_type, '')

    if not extension:
        current_app.logger.warning('上传失败：无法识别扩展名，filename=%s mimetype=%s', original_filename, mime_type)
        return jsonify({'success': 0, 'message': '无法识别文件类型，请使用常见图片格式'}), 400

    allowed_extensions = current_app.config.get('ALLOWED_UPLOAD_EXTENSIONS') or set()
    allowed_mimes = current_app.config.get('ALLOWED_UPLOAD_MIME_TYPES') or set()

    if allowed_extensions and extension not in allowed_extensions:
        current_app.logger.warning('上传失败：扩展名不允许 .%s', extension)
        return jsonify({'success': 0, 'message': f'不支持的文件类型: .{extension}'}), 400

    if allowed_mimes and mime_type and mime_type not in allowed_mimes:
        current_app.logger.warning('上传失败：MIME不允许 %s', mime_type)
        return jsonify({'success': 0, 'message': '不支持的文件类型'}), 400

    upload_root = current_app.config.get('UPLOAD_FOLDER')
    if not upload_root:
        current_app.logger.error('UPLOAD_FOLDER 未配置，无法保存上传文件')
        return jsonify({'success': 0, 'message': '服务器未配置上传目录'}), 500

    # 使用年月分类目录，避免单个目录文件过多
    relative_dir = datetime.now(timezone.utc).strftime('%Y/%m')
    target_dir = os.path.join(upload_root, relative_dir)
    os.makedirs(target_dir, exist_ok=True)

    unique_name = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.{extension}"
    file_path = os.path.join(target_dir, unique_name)

    try:
        file.save(file_path)
    except OSError as exc:
        current_app.logger.exception('保存上传文件失败: %s', exc)
        return jsonify({'success': 0, 'message': '保存文件失败，请稍后再试'}), 500

    relative_path = f"{relative_dir}/{unique_name}".replace('\\', '/')
    file_url = url_for('uploaded_file', filename=relative_path)
    return jsonify({'success': 1, 'url': file_url, 'message': '上传成功'})

@bp.route('/posts/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_post(post_id):
    """编辑文章"""
    post = Post.query.get_or_404(post_id)
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        excerpt = request.form.get('excerpt', '').strip()
        category_id = request.form.get('category_id', type=int)
        status = request.form.get('status', 'draft')
        comment_status = request.form.get('comment_status', 'open')
        featured_image = request.form.get('featured_image', '').strip()
        seo_title = request.form.get('seo_title', '').strip()
        seo_description = request.form.get('seo_description', '').strip()
        seo_keywords = request.form.get('seo_keywords', '').strip()
        
        if not title or not content:
            flash('标题和内容不能为空', 'error')
            return theme_manager.render_template('admin/edit_post.html', post=post)
        
        # 更新文章
        post.title = title
        post.content = content
        post.excerpt = excerpt
        post.category_id = category_id
        post.status = status
        post.comment_status = comment_status
        post.featured_image = featured_image
        post.seo_title = seo_title
        post.seo_description = seo_description
        post.seo_keywords = seo_keywords
        
        # 处理 slug
        slug = request.form.get('slug', '').strip()
        if slug:
            # 确保 slug 唯一（排除当前文章）
            original_slug = slug
            counter = 1
            while Post.query.filter(Post.slug == slug, Post.id != post_id).first():
                slug = f"{original_slug}-{counter}"
                counter += 1
            post.slug = slug
        
        # 处理标签
        post.tags.clear()
        tag_names = request.form.get('tags', '').strip()
        if tag_names:
            tag_list = [tag.strip() for tag in tag_names.split(',') if tag.strip()]
            for tag_name in tag_list:
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
        
        flash('文章更新成功', 'success')
        return redirect(url_for('admin.posts'))
    
    categories = Category.query.filter_by(is_active=True).all()
    tags = Tag.query.all()
    
    upload_limit_bytes = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
    upload_limit_mb = max(1, upload_limit_bytes // (1024 * 1024))

    context = _get_base_context('编辑文章')
    context.update({
        'post': post,
        'categories': categories,
        'tags': tags,
        'upload_limit_mb': upload_limit_mb,
        'editor_plugin_hooks': _collect_editor_hooks('edit', post=post)
    })
    
    return theme_manager.render_template('admin/edit_post.html', **context)

@bp.route('/posts/<int:post_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_post(post_id):
    """删除文章"""
    post = Post.query.get_or_404(post_id)
    
    # 触发钩子
    plugin_manager.do_action('before_post_delete', post=post)
    
    db.session.delete(post)
    db.session.commit()
    
    # 触发钩子
    plugin_manager.do_action('after_post_delete', post=post)
    
    flash('文章删除成功', 'success')
    return redirect(url_for('admin.posts'))

# 分类管理
@bp.route('/categories')
@login_required
@admin_required
def categories():
    """分类列表"""
    categories = Category.query.order_by(Category.sort_order, Category.name).all()
    
    context = _get_base_context('分类管理')
    context.update({
        'categories': categories,
    })
    
    return theme_manager.render_template('admin/categories.html', **context)

@bp.route('/categories/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_category():
    """创建分类"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        slug = request.form.get('slug', '').strip()
        description = request.form.get('description', '').strip()
        parent_id = request.form.get('parent_id', type=int)
        sort_order = request.form.get('sort_order', 0, type=int)
        
        if not name:
            flash('分类名称不能为空', 'error')
            return theme_manager.render_template('admin/create_category.html')
        
        if not slug:
            import re
            from pypinyin import lazy_pinyin, Style
            
            # 转换为拼音
            pinyin_list = lazy_pinyin(name, style=Style.NORMAL)
            slug = '-'.join(pinyin_list)
            
            # 清理特殊字符
            slug = re.sub(r'[^\w\s-]', '', slug).strip().lower()
            slug = re.sub(r'[-\s]+', '-', slug)
        
        # 检查 slug 是否已存在
        if Category.query.filter_by(slug=slug).first():
            flash('分类别名已存在', 'error')
            return theme_manager.render_template('admin/create_category.html')
        
        category = Category(
            name=name,
            slug=slug,
            description=description,
            parent_id=parent_id,
            sort_order=sort_order
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash('分类创建成功', 'success')
        return redirect(url_for('admin.categories'))
    
    categories = Category.query.filter_by(parent_id=None).all()
    
    context = _get_base_context('创建分类')
    context.update({
        'categories': categories,
    })
    
    return theme_manager.render_template('admin/create_category.html', **context)

@bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(category_id):
    """编辑分类"""
    category = Category.query.get_or_404(category_id)
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        slug = request.form.get('slug', '').strip()
        description = request.form.get('description', '').strip()
        parent_id = request.form.get('parent_id', type=int)
        sort_order = request.form.get('sort_order', 0, type=int)
        
        if not name:
            flash('分类名称不能为空', 'error')
            return theme_manager.render_template('admin/edit_category.html', category=category)
        
        if not slug:
            import re
            from pypinyin import lazy_pinyin, Style
            
            # 转换为拼音
            pinyin_list = lazy_pinyin(name, style=Style.NORMAL)
            slug = '-'.join(pinyin_list)
            
            # 清理特殊字符
            slug = re.sub(r'[^\w\s-]', '', slug).strip().lower()
            slug = re.sub(r'[-\s]+', '-', slug)
        
        # 检查 slug 是否已存在（排除当前分类）
        existing_category = Category.query.filter(Category.slug == slug, Category.id != category_id).first()
        if existing_category:
            flash('分类别名已存在', 'error')
            return theme_manager.render_template('admin/edit_category.html', category=category)
        
        # 更新分类
        category.name = name
        category.slug = slug
        category.description = description
        category.parent_id = parent_id
        category.sort_order = sort_order
        
        db.session.commit()
        
        flash('分类更新成功', 'success')
        return redirect(url_for('admin.categories'))
    
    categories = Category.query.filter_by(parent_id=None).all()
    
    context = _get_base_context('编辑分类')
    context.update({
        'category': category,
        'categories': categories,
    })
    
    return theme_manager.render_template('admin/edit_category.html', **context)

@bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(category_id):
    """删除分类"""
    category = Category.query.get_or_404(category_id)
    
    # 将该分类下的文章的分类ID设为空
    Post.query.filter_by(category_id=category_id).update({'category_id': None})
    
    # 将子分类的父级ID设为空
    Category.query.filter_by(parent_id=category_id).update({'parent_id': None})
    
    db.session.delete(category)
    db.session.commit()
    
    flash('分类删除成功', 'success')
    return redirect(url_for('admin.categories'))

# 评论管理
@bp.route('/comments')
@login_required
@admin_required
def comments():
    """评论列表"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = Comment.query
    if status == 'approved':
        query = query.filter_by(is_approved=True, is_spam=False)
    elif status == 'pending':
        query = query.filter_by(is_approved=False, is_spam=False)
    elif status == 'spam':
        query = query.filter_by(is_spam=True)
    
    comments = query.order_by(Comment.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # 获取全局评论开关状态
    allow_comments = SettingManager.get('allow_comments', True)
    
    context = _get_base_context('评论管理')
    context.update({
        'comments': comments,
        'status': status,
        'allow_comments': allow_comments,
    })
    
    return theme_manager.render_template('admin/comments.html', **context)

@bp.route('/comments/toggle_global', methods=['POST'])
@login_required
@admin_required
def toggle_global_comments():
    """切换全局评论功能"""
    enabled = request.form.get('enabled') == 'true'
    SettingManager.set('allow_comments', enabled, value_type='boolean')
    flash('全局评论功能已{}'.format('开启' if enabled else '关闭'), 'success')
    return redirect(url_for('admin.comments'))

@bp.route('/comments/<int:comment_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_comment(comment_id):
    """审核通过评论"""
    comment = Comment.query.get_or_404(comment_id)
    comment.approve()
    flash('评论审核通过', 'success')
    return redirect(url_for('admin.comments'))

@bp.route('/comments/<int:comment_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_comment(comment_id):
    """拒绝评论"""
    comment = Comment.query.get_or_404(comment_id)
    comment.reject()
    flash('评论已拒绝', 'success')
    return redirect(url_for('admin.comments'))

@bp.route('/comments/<int:comment_id>/spam', methods=['POST'])
@login_required
@admin_required
def mark_comment_spam(comment_id):
    """标记评论为垃圾"""
    comment = Comment.query.get_or_404(comment_id)
    comment.mark_as_spam()
    flash('评论已标记为垃圾', 'success')
    return redirect(url_for('admin.comments'))

@bp.route('/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_comment(comment_id):
    """删除评论"""
    comment = Comment.query.get_or_404(comment_id)
    
    # 删除该评论的所有回复
    Comment.query.filter_by(parent_id=comment_id).delete()
    
    # 删除评论本身
    db.session.delete(comment)
    db.session.commit()
    
    flash('评论删除成功', 'success')
    return redirect(url_for('admin.comments'))

# 用户管理
@bp.route('/users')
@login_required
@admin_required
def users():
    """用户列表"""
    page = request.args.get('page', 1, type=int)
    
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    context = _get_base_context('用户管理')
    context.update({
        'users': users,
    })
    
    return theme_manager.render_template('admin/users.html', **context)

@bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """切换用户状态"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('不能禁用自己的账户', 'error')
        return redirect(url_for('admin.users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = '激活' if user.is_active else '禁用'
    flash(f'用户已{status}', 'success')
    return redirect(url_for('admin.users'))

# 插件管理
@bp.route('/plugins')
@login_required
@admin_required
def plugins():
    """插件列表"""
    # 获取已安装的插件
    installed_plugins = Plugin.query.order_by(Plugin.name).all()
    installed_names = {p.name for p in installed_plugins}
    
    # 获取可安装的插件（在plugins目录下但未安装的）
    available_plugins = []
    import os
    plugins_dir = path_utils.project_path('plugins')
    
    if os.path.exists(plugins_dir):
        for item in os.listdir(plugins_dir):
            plugin_path = os.path.join(plugins_dir, item)
            if os.path.isdir(plugin_path) and item not in installed_names:
                # 检查是否有plugin.json文件
                plugin_json_path = os.path.join(plugin_path, 'plugin.json')
                if os.path.exists(plugin_json_path):
                    try:
                        import json
                        with open(plugin_json_path, 'r', encoding='utf-8') as f:
                            plugin_info = json.load(f)
                        
                        # 创建一个插件对象用于显示
                        class AvailablePlugin:
                            def __init__(self, info, name):
                                self.name = name
                                self.display_name = info.get('display_name', name)
                                self.description = info.get('description', '')
                                self.version = info.get('version', '1.0.0')
                                self.author = info.get('author', '')
                                self.website = info.get('website', '')
                                self.is_active = False
                                self.is_installed = False
                        
                        available_plugins.append(AvailablePlugin(plugin_info, item))
                    except Exception as e:
                        print(f"Error reading plugin info for {item}: {e}")
                        continue
    
    # 合并插件列表
    all_plugins = list(installed_plugins) + available_plugins
    
    context = _get_base_context('插件管理')
    context.update({
        'plugins': all_plugins,
    })
    
    return theme_manager.render_template('admin/plugins.html', **context)

@bp.route('/plugins/<plugin_name>/activate', methods=['POST'])
@login_required
@admin_required
def activate_plugin(plugin_name):
    """激活插件"""
    if plugin_manager.activate_plugin(plugin_name):
        flash('插件激活成功', 'success')
    else:
        flash('插件激活失败', 'error')
    
    return redirect(url_for('admin.plugins'))

@bp.route('/plugins/<plugin_name>/deactivate', methods=['POST'])
@login_required
@admin_required
def deactivate_plugin(plugin_name):
    """停用插件"""
    if plugin_manager.deactivate_plugin(plugin_name):
        flash('插件停用成功', 'success')
    else:
        flash('插件停用失败', 'error')
    
    return redirect(url_for('admin.plugins'))

@bp.route('/plugins/<plugin_name>/install', methods=['POST'])
@login_required
@admin_required
def install_plugin(plugin_name):
    """安装插件"""
    if plugin_manager.install_plugin(plugin_name):
        flash('插件安装成功', 'success')
    else:
        flash('插件安装失败', 'error')
    
    return redirect(url_for('admin.plugins'))

@bp.route('/api/plugins/<plugin_name>/install', methods=['POST'])
@login_required
@admin_required
def api_install_plugin(plugin_name):
    """API：安装插件"""
    if plugin_manager.install_plugin(plugin_name):
        return jsonify({'success': True, 'message': '插件安装成功'})
    else:
        return jsonify({'success': False, 'message': '插件安装失败'})

@bp.route('/api/plugins/<plugin_name>/activate', methods=['POST'])
@login_required
@admin_required
def api_activate_plugin(plugin_name):
    """API：激活插件"""
    if plugin_manager.activate_plugin(plugin_name):
        return jsonify({'success': True, 'message': '插件激活成功'})
    else:
        return jsonify({'success': False, 'message': '插件激活失败'})

@bp.route('/api/plugins/<plugin_name>/deactivate', methods=['POST'])
@login_required
@admin_required
def api_deactivate_plugin(plugin_name):
    """API：停用插件"""
    if plugin_manager.deactivate_plugin(plugin_name):
        return jsonify({'success': True, 'message': '插件停用成功'})
    else:
        return jsonify({'success': False, 'message': '插件停用失败'})

@bp.route('/plugins/<plugin_name>/configure')
@login_required
@admin_required
def configure_plugin(plugin_name):
    """插件配置页面"""
    # 获取插件信息
    plugin = Plugin.query.filter_by(name=plugin_name).first()
    if not plugin:
        flash('插件不存在', 'error')
        return redirect(url_for('admin.plugins'))
    
    context = _get_base_context(f"{plugin.display_name or plugin.name} 配置")
    context.update({
        'plugin': plugin,
    })
    
    return theme_manager.render_template('admin/plugin_configure.html', **context)

# 主题管理
@bp.route('/themes')
@login_required
@admin_required
def themes():
    """主题列表"""
    themes = Theme.query.order_by(Theme.name).all()
    
    context = _get_base_context('主题管理')
    context.update({
        'themes': themes,
    })
    
    return theme_manager.render_template('admin/themes.html', **context)

@bp.route('/themes/<theme_name>/activate', methods=['POST'])
@login_required
@admin_required
def activate_theme(theme_name):
    """激活主题"""
    if theme_manager.activate_theme(theme_name):
        flash('主题激活成功', 'success')
    else:
        flash('主题激活失败', 'error')

    return redirect(url_for('admin.themes'))

@bp.route('/themes/<theme_name>/customize', methods=['GET', 'POST'])
@login_required
@admin_required
def customize_theme(theme_name):
    """主题自定义页面"""
    import json

    theme = Theme.query.filter_by(name=theme_name).first()
    if not theme:
        flash('主题不存在', 'error')
        return redirect(url_for('admin.themes'))

    # 始终从 theme.json 文件读取最新配置模式
    config_schema = {}
    theme_json_path = os.path.join(theme.install_path, 'theme.json')
    if os.path.exists(theme_json_path):
        try:
            with open(theme_json_path, 'r', encoding='utf-8') as f:
                theme_info = json.load(f)
            config_schema = theme_info.get('config_schema', {})
        except Exception as e:
            current_app.logger.error(f'读取主题配置模式失败: {e}')
            # 如果读取文件失败，尝试从数据库获取
            config_schema = theme.get_config_schema() or {}

    if request.method == 'POST':
        # 保存配置
        config_data = {}
        for key, schema in config_schema.items():
            field_type = schema.get('type', 'text')

            if field_type == 'checkbox':
                # 复选框：选中为 True，未选中为 False
                config_data[key] = key in request.form
            elif field_type == 'number':
                # 数字类型
                value = request.form.get(key, '')
                if value:
                    try:
                        config_data[key] = int(value)
                    except ValueError:
                        try:
                            config_data[key] = float(value)
                        except ValueError:
                            config_data[key] = schema.get('default', 0)
                else:
                    config_data[key] = schema.get('default', 0)
            elif field_type == 'array':
                # 数组类型（逗号分隔）
                value = request.form.get(key, '')
                if value:
                    config_data[key] = [item.strip() for item in value.split(',') if item.strip()]
                else:
                    config_data[key] = schema.get('default', [])
            else:
                # 文本、颜色、选择框等
                config_data[key] = request.form.get(key, schema.get('default', ''))

        theme.set_config(config_data)
        flash('主题配置保存成功', 'success')
        return redirect(url_for('admin.customize_theme', theme_name=theme_name))

    # 获取当前配置
    current_config = theme.get_config()

    # 合并默认值
    for key, schema in config_schema.items():
        if key not in current_config:
            current_config[key] = schema.get('default', '')

    context = _get_base_context(f'{theme.display_name} 自定义')
    context.update({
        'theme': theme,
        'config_schema': config_schema,
        'current_config': current_config,
    })

    return theme_manager.render_template('admin/theme_customize.html', **context)

# 设置管理
@bp.route('/settings')
@login_required
@admin_required
def settings():
    """系统设置"""
    # 获取所有设置，按分类分组
    general_settings = SettingManager.get_category('general')
    comment_settings = SettingManager.get_category('comment')
    
    # 合并所有设置
    all_settings = {**general_settings, **comment_settings}
    
    # 确保必需的评论设置存在
    if 'comment_registration' not in all_settings:
        all_settings['comment_registration'] = 'false'
    if 'comment_blacklist' not in all_settings:
        all_settings['comment_blacklist'] = ''
    
    context = _get_base_context('系统设置')
    context.update({
        'settings': all_settings,
    })
    
    return theme_manager.render_template('admin/settings.html', **context)

@bp.route('/settings/save', methods=['POST'])
@login_required
@admin_required
def save_settings():
    """保存设置"""
    # 基本设置
    general_settings = [
        'site_title', 'site_description', 'site_keywords',
        'site_url', 'admin_email', 'posts_per_page', 'timezone', 'date_format',
        'footer_text'
    ]
    
    for key in general_settings:
        if key in request.form:
            value = request.form.get(key, '').strip()
            SettingManager.set(key, value)
    
    # 评论设置 - 布尔类型需要指定 value_type='boolean'
    # 复选框选中时提交 value="true"，未选中时不提交
    SettingManager.set(
        'comment_moderation',
        'comment_moderation' in request.form,
        value_type='boolean',
        category='comment'
    )
    SettingManager.set(
        'comment_registration',
        'comment_registration' in request.form,
        value_type='boolean',
        category='comment'
    )
    SettingManager.set(
        'comment_blacklist',
        request.form.get('comment_blacklist', '').strip(),
        category='comment'
    )
    
    flash('设置保存成功', 'success')
    return redirect(url_for('admin.settings'))


@bp.route('/settings/backup/download')
@login_required
@admin_required
def download_backup():
    """下载包含上传文件与数据库的备份包。"""
    include_extensions = request.args.get('include_extensions') == 'true'
    try:
        filename, buffer = create_backup_archive(include_extensions=include_extensions)
        # send_file 会处理流式输出，避免将文件写入磁盘
        return send_file(
            buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )
    except BackupError as exc:
        flash(str(exc), 'error')
    except Exception as exc:
        current_app.logger.exception('生成备份失败: %s', exc)
        flash('生成备份失败，请查看日志获取更多信息。', 'error')

    return redirect(url_for('admin.settings'))


@bp.route('/settings/backup/import', methods=['POST'])
@login_required
@admin_required
def import_backup():
    """导入备份并恢复数据库与上传文件。"""
    backup_file = request.files.get('backup_file')
    restore_extensions = request.form.get('restore_extensions') == 'true'
    overwrite_extensions = request.form.get('overwrite_extensions') == 'true'

    try:
        restore_backup_from_zip(
            backup_file, 
            restore_extensions=restore_extensions, 
            overwrite_extensions=overwrite_extensions
        )
        if restore_extensions:
            flash('备份导入成功！数据已恢复。如果备份包含插件，请重启应用使插件完全生效。', 'success')
        else:
            flash('备份导入成功，系统数据已恢复。', 'success')
    except BackupError as exc:
        flash(str(exc), 'error')
    except Exception as exc:
        current_app.logger.exception('导入备份失败: %s', exc)
        flash('导入备份失败，请查看日志获取更多信息。', 'error')

    return redirect(url_for('admin.settings'))
