# Minimal settings to run our tests.

import os.path


SECRET_KEY = 'fake-key'
INSTALLED_APPS = [
    'django_FBO',
]
ALLOWED_HOSTS = ['localhost']
ROOT_DIR = os.path.dirname(__file__)
BASE_DIR = os.path.join(
    ROOT_DIR,
    'modules/files',
)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'testdb',
    }
}
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': False,
        'DIRS': [
            os.path.join(ROOT_DIR, 'templates'),
            os.path.join(ROOT_DIR, 'modules/templates'),
        ],
        'OPTIONS': {
            'context_processors': [],
        },
    },
]
FBO_BLOG_TITLE = 'Blog title'
FBO_BLOG_SUBTITLE = 'Blog subtitle'
FBO_BLOG_COPYRIGHT = 'Blog copyright'
USE_TZ = True
TIME_ZONE = 'UTC'
