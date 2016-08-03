"""
Django settings for @@SITEDIR@@ project.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = os.environ.get('DJANGO_DEBUG', True)
if DEBUG:
    SECRET_KEY = '@@SECRET_KEY@@'
else:
    SECRET_KEY = os.environ['SECRET_KEY']
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(';')

# Application definition

INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'django_cape',
    'django_FBO',
    'markdown_deux',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = '@@SITEDIR@@.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = '@@SITEDIR@@.wsgi.application'

DATABASES = {}
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
LANGUAGE_CODE = 'en-gb'

# Markdown settings
MARKDOWN_DEUX_STYLES = {
    'default': {
        'extras': {
            'smarty-pants': True,
            'code-friendly': None,
            'wiki-tables': True,
        },
        'safe_mode': 'escape',
    },
}

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]
STATIC_ROOT = os.path.join(BASE_DIR, 'build', 'static')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Where do we bake FBO to?
FBO_BUILD_DIR = os.path.join(BASE_DIR, 'build')

@@MODULE_SETTINGS@@
