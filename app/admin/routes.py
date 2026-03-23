from functools import wraps
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import User, Role, Setting
from app.admin import admin_bp


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('需要管理員權限。', 'danger')
            return redirect(url_for('main.upload'))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.username).all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def user_new():
    roles = Role.query.all()
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role_id = request.form.get('role_id')
        is_ad = request.form.get('is_ad_user') == 'on'

        if not username:
            flash('請輸入帳號。', 'warning')
            return render_template('admin/user_edit.html', user=None, roles=roles)
        if User.query.filter_by(username=username).first():
            flash('此帳號已存在。', 'warning')
            return render_template('admin/user_edit.html', user=None, roles=roles)

        u = User(username=username, email=email, role_id=role_id, is_ad_user=is_ad)
        if not is_ad and password:
            u.set_password(password)
        db.session.add(u)
        db.session.commit()
        flash(f'使用者 {username} 已建立。', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/user_edit.html', user=None, roles=roles)


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def user_edit(user_id):
    u = User.query.get_or_404(user_id)
    roles = Role.query.all()
    if request.method == 'POST':
        u.email = request.form.get('email', '').strip()
        u.role_id = request.form.get('role_id')
        u.is_ad_user = request.form.get('is_ad_user') == 'on'
        password = request.form.get('password', '')
        if password and not u.is_ad_user:
            u.set_password(password)
        db.session.commit()
        flash(f'使用者 {u.username} 已更新。', 'success')
        return redirect(url_for('admin.users'))
    return render_template('admin/user_edit.html', user=u, roles=roles)


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def user_delete(user_id):
    u = User.query.get_or_404(user_id)
    if u.username == 'admin':
        flash('無法刪除預設管理員帳號。', 'danger')
        return redirect(url_for('admin.users'))
    db.session.delete(u)
    db.session.commit()
    flash(f'使用者 {u.username} 已刪除。', 'success')
    return redirect(url_for('admin.users'))


# ---------------------------------------------------------------------------
# Settings management
# ---------------------------------------------------------------------------

SETTING_KEYS = [
    ('MISP_URL',       'MISP 伺服器 URL',            'text'),
    ('MISP_KEY',       'MISP API Key',                'password'),
    ('MISP_VERIFYCERT','MISP 驗證 SSL (true/false)',  'text'),
    ('VT_API_KEY',     'VirusTotal API Key',           'password'),
    ('MAIL_SERVER',    'SMTP 伺服器',                  'text'),
    ('MAIL_PORT',      'SMTP 埠 (預設25)',              'text'),
    ('MAIL_USE_TLS',   'SMTP 使用 TLS (true/false)',   'text'),
    ('MAIL_USERNAME',  'SMTP 帳號',                    'text'),
    ('MAIL_PASSWORD',  'SMTP 密碼',                    'password'),
    ('MAIL_SENDER',    '寄件者地址',                    'text'),
    ('AD_SERVER',      'AD 伺服器位址',                 'text'),
    ('AD_BASE_DN',     'AD Base DN',                   'text'),
    ('AD_DOMAIN',      'AD 網域 (NetBIOS)',             'text'),
    ('AD_BIND_DN',     'AD Bind DN (服務帳號)',          'text'),
    ('AD_BIND_PW',     'AD Bind 密碼',                  'password'),
]


@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    if request.method == 'POST':
        for key, label, _ in SETTING_KEYS:
            val = request.form.get(key, '').strip()
            # Save whenever a value is provided or an explicit clear checkbox is checked
            if val or request.form.get(key + '_clear'):
                Setting.set(key, val)
        flash('設定已儲存。', 'success')
        return redirect(url_for('admin.settings'))

    current = {key: Setting.get(key, '') for key, _, _ in SETTING_KEYS}
    return render_template('admin/settings.html', setting_keys=SETTING_KEYS, current=current)
