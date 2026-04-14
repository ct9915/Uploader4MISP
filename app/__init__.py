from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from config import ActiveConfig, _DEFAULT_SECRET_KEY
import os

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(ActiveConfig)

    # 當 SECRET_KEY 仍是預設值且非 debug 模式時，拒絕啟動
    if not app.debug and app.config.get('SECRET_KEY') == _DEFAULT_SECRET_KEY:
        raise RuntimeError(
            '[Production] SECRET_KEY 未設定！'
            '請在 .env 或環境變數中設定強隨機字串後再啟動。'
            '產生方式：python -c "import secrets; print(secrets.token_hex(32))"'
        )

    # 支援反向代理（nginx / Traefik 等）：
    # 若未在反向代理後方執行，此設定無害；
    # 若在反向代理後方，缺少此設定會導致 scheme 誤判，造成 session cookie 失效（CSRF token 遺失）。
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)
    os.makedirs('instance', exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '請先登入。'
    login_manager.login_message_category = 'warning'

    from app.auth import auth_bp
    from app.main import main_bp
    from app.admin import admin_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()
        _seed_db()

    return app


def _seed_db():
    from app.models import Role, User
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(name='admin')
        db.session.add(admin_role)
    user_role = Role.query.filter_by(name='user').first()
    if not user_role:
        user_role = Role(name='user')
        db.session.add(user_role)
    db.session.commit()

    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='', role=admin_role, is_ad_user=False)
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()


@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))
