from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Role, Setting
from app.auth import auth_bp
from app.auth.ldap_helper import authenticate_ad


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.upload'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if user and not user.is_ad_user:
            # Local auth
            if user.check_password(password):
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('main.upload'))
            else:
                flash('帳號或密碼錯誤。', 'danger')
                return render_template('auth/login.html')

        # Try AD auth
        ad_enabled = Setting.get('AD_SERVER')
        if ad_enabled and authenticate_ad(username, password):
            if not user:
                # Auto-provision AD user
                user_role = Role.query.filter_by(name='user').first()
                user = User(username=username, is_ad_user=True, role=user_role)
                db.session.add(user)
                db.session.commit()
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.upload'))

        flash('帳號或密碼錯誤。', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
