"""
MariaDB configuration for news_project.

To switch from SQLite to MariaDB:
1. Install: pip install mysqlclient
2. Replace the DATABASES entry in settings.py with the block below.
3. Run: python manage.py migrate
"""

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'news_db',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}
