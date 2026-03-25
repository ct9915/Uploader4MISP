import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    flask_env = os.environ.get('FLASK_ENV', 'development')

    if flask_env == 'production':
        # Use gunicorn in production mode
        import subprocess
        import sys
        workers = int(os.environ.get('WEB_CONCURRENCY', 4))
        bind = f'0.0.0.0:{port}'
        cmd = [
            sys.executable, '-m', 'gunicorn',
            '-w', str(workers),
            '-b', bind,
            'wsgi:app'
        ]
        subprocess.run(cmd)
    else:
        # Use Flask dev server in development mode
        debug = os.environ.get('FLASK_DEBUG', 'false').lower() in ('1', 'true', 'yes')
        app.run(host='0.0.0.0', port=port, debug=debug)
