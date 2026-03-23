import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / 'instance'


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{INSTANCE_DIR / "app.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = str(INSTANCE_DIR / 'uploads')
    TEMP_FOLDER = str(INSTANCE_DIR / 'temp')
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB
    WTF_CSRF_ENABLED = True
