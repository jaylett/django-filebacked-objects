"""
Django settings for @@SITENAME@@ project.

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

# By default, strip .md from slugs (so something.md -> something)
#
# Note that this means that for Pages, having pages/about will
# response to /about (given the default URL configuration), which will
# bake to .../about.html and will require something like Apache's
# Options +MultiViews to serve properly. If you can't set things up
# that way, then use pages/about/index.md and you'll get /about/ and
# .../about/index.html, which only requires Options +Indexes or
# similar.
#
# The default is None, ie don't strip any slug suffices. (index will
# still be stripped though.)
FBO_DEFAULT_SLUG_SUFFICES = [ '.md' ]
# Where do we bake FBO to?
FBO_BUILD_DIR = os.path.join(BASE_DIR, 'build')

@@MODULE_SETTINGS@@
