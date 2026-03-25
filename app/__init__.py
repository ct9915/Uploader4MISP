from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import ActiveConfig
import os

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(ActiveConfig)

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
