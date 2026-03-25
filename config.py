import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / 'instance'


class Config:
    """共用基礎設定"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{INSTANCE_DIR / "app.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = str(INSTANCE_DIR / 'uploads')
    TEMP_FOLDER = str(INSTANCE_DIR / 'temp')
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB
    WTF_CSRF_ENABLED = True


class DevelopmentConfig(Config):
    """開發環境設定：啟用 debug、詳細錯誤訊息"""
    DEBUG = True
    FLASK_ENV = 'development'


class ProductionConfig(Config):
    """正式環境設定：關閉 debug、強制安全設定"""
    DEBUG = False
    FLASK_ENV = 'production'

    def __init__(self):
        # 正式環境若仍使用預設密鑰，直接拋出例外阻止啟動
        if self.SECRET_KEY == 'change-me-in-production':
            raise RuntimeError(
                '[ProductionConfig] SECRET_KEY 未設定！'
                '請在 .env 或環境變數中設定強隨機字串後再啟動。'
            )


# ── 依 FLASK_ENV / APP_ENV 自動選擇設定類別 ──────────────────────────────────
_config_map = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'prod':        ProductionConfig,
}

# 環境變數優先順序：FLASK_ENV → APP_ENV → 預設 development
_env = (os.environ.get('FLASK_ENV') or os.environ.get('APP_ENV') or 'development').lower()
ActiveConfig = _config_map.get(_env, DevelopmentConfig)
