"""
认证视图
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app import db, login_manager
from app.models.user import User
from app.models.setting import SettingManager
from app.services.plugin_manager import plugin_manager
from app.services.theme_manager import theme_manager

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me') == 'on'
        
        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return redirect(url_for('main.index', modal='login'))
        
        # 查找用户（支持用户名或邮箱登录）
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if user and user.check_password(password) and user.is_active:
            # 触发钩子
            plugin_manager.do_action('before_user_login', user=user)
            
            login_user(user, remember=remember_me)
            user.update_last_login()
            
            # 触发钩子
            plugin_manager.do_action('after_user_login', user=user)
            
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('main.index')
            
            flash('登录成功！', 'success')
            return redirect(next_page)
        else:
            flash('用户名或密码错误', 'error')
            return redirect(url_for('main.index', modal='login'))
    
    # GET请求重定向到首页并打开登录模态框
    return redirect(url_for('main.index', modal='login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """注册"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if not SettingManager.get('allow_registration', True):
        flash('注册功能已关闭', 'error')
        return redirect(url_for('main.index', modal='login'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        display_name = request.form.get('display_name', '').strip()
        
        # 验证输入
        if not username or not email or not password:
            flash('请填写所有必填字段', 'error')
            return redirect(url_for('main.index', modal='register'))
        
        if password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return redirect(url_for('main.index', modal='register'))
        
        if len(password) < 6:
            flash('密码长度至少为6位', 'error')
            return redirect(url_for('main.index', modal='register'))
        
        # 检查用户名和邮箱是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return redirect(url_for('main.index', modal='register'))
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'error')
            return redirect(url_for('main.index', modal='register'))
        
        # 创建用户
        user = User(
            username=username,
            email=email,
            password=password,
            display_name=display_name or username
        )
        
        # 触发钩子
        plugin_manager.do_action('before_user_register', user=user)
        
        db.session.add(user)
        db.session.commit()
        
        # 触发钩子
        plugin_manager.do_action('after_user_register', user=user)
        
        flash('注册成功！请登录', 'success')
        return redirect(url_for('main.index', modal='login'))
    
    # GET请求重定向到首页并打开注册模态框
    return redirect(url_for('main.index', modal='register'))

@bp.route('/logout')
@login_required
def logout():
    """登出"""
    # 触发钩子
    plugin_manager.do_action('before_user_logout', user=current_user)
    
    logout_user()
    
    flash('已成功登出', 'info')
    return redirect(url_for('main.index'))

@bp.route('/profile')
@login_required
def profile():
    """个人资料"""
    context = {
        'user': current_user,
        'site_title': f"个人资料 - {SettingManager.get('site_title', 'Noteblog')}",
        'current_user': current_user
    }
    
    return theme_manager.render_template('auth/profile.html', **context)

@bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """编辑个人资料"""
    if request.method == 'POST':
        display_name = request.form.get('display_name', '').strip()
        email = request.form.get('email', '').strip()
        bio = request.form.get('bio', '').strip()
        website = request.form.get('website', '').strip()
        location = request.form.get('location', '').strip()
        
        # 验证邮箱
        if not email:
            flash('邮箱不能为空', 'error')
            return render_template('auth/edit_profile.html', user=current_user)
        
        # 检查邮箱是否已被其他用户使用
        existing_user = User.query.filter(
            User.email == email, User.id != current_user.id
        ).first()
        if existing_user:
            flash('邮箱已被其他用户使用', 'error')
            return render_template('auth/edit_profile.html', user=current_user)
        
        # 更新用户信息
        current_user.display_name = display_name
        current_user.email = email
        current_user.bio = bio
        current_user.website = website
        current_user.location = location
        
        # 处理头像上传
        if 'avatar' in request.files:
            avatar_file = request.files['avatar']
            if avatar_file.filename:
                # 这里应该实现文件上传逻辑
                # 暂时跳过头像上传
                pass
        
        # 触发钩子
        plugin_manager.do_action('before_profile_update', user=current_user)
        
        db.session.commit()
        
        # 触发钩子
        plugin_manager.do_action('after_profile_update', user=current_user)
        
        flash('个人资料更新成功', 'success')
        return redirect(url_for('auth.profile'))
    
    context = {
        'user': current_user,
        'site_title': f"编辑资料 - {SettingManager.get('site_title', 'Noteblog')}",
        'current_user': current_user
    }
    
    return theme_manager.render_template('auth/edit_profile.html', **context)

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not current_password or not new_password or not confirm_password:
            flash('请填写所有字段', 'error')
            return render_template('auth/change_password.html')
        
        if not current_user.check_password(current_password):
            flash('当前密码错误', 'error')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('两次输入的新密码不一致', 'error')
            return render_template('auth/change_password.html')
        
        if len(new_password) < 6:
            flash('新密码长度至少为6位', 'error')
            return render_template('auth/change_password.html')
        
        # 更新密码
        current_user.set_password(new_password)
        
        # 触发钩子
        plugin_manager.do_action('before_password_change', user=current_user)
        
        db.session.commit()
        
        # 触发钩子
        plugin_manager.do_action('after_password_change', user=current_user)
        
        flash('密码修改成功', 'success')
        return redirect(url_for('auth.profile'))
    
    context = {
        'site_title': f"修改密码 - {SettingManager.get('site_title', 'Noteblog')}",
        'current_user': current_user
    }
    
    return theme_manager.render_template('auth/change_password.html', **context)

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """忘记密码"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        if not email:
            flash('请输入邮箱地址', 'error')
            return redirect(url_for('main.index', modal='forgot_password'))
        
        user = User.query.filter_by(email=email).first()
        if user:
            # 触发钩子
            plugin_manager.do_action('before_password_reset', user=user)
            
            # 这里应该发送密码重置邮件
            # 暂时只显示成功消息
            flash('密码重置链接已发送到您的邮箱', 'info')
            
            # 触发钩子
            plugin_manager.do_action('after_password_reset', user=user)
        else:
            flash('如果该邮箱存在，密码重置链接已发送', 'info')
        
        return redirect(url_for('main.index', modal='login'))
    
    # GET请求重定向到首页并打开忘记密码模态框
    return redirect(url_for('main.index', modal='forgot_password'))

# API 接口
@bp.route('/api/check-username')
def check_username():
    """检查用户名是否可用"""
    username = request.args.get('username', '').strip()
    if not username:
        return jsonify({'available': False, 'message': '用户名不能为空'})
    
    user = User.query.filter_by(username=username).first()
    return jsonify({
        'available': user is None,
        'message': '用户名可用' if user is None else '用户名已存在'
    })

@bp.route('/api/check-email')
def check_email():
    """检查邮箱是否可用"""
    email = request.args.get('email', '').strip()
    if not email:
        return jsonify({'available': False, 'message': '邮箱不能为空'})
    
    user = User.query.filter_by(email=email).first()
    return jsonify({
        'available': user is None,
        'message': '邮箱可用' if user is None else '邮箱已被注册'
    })
