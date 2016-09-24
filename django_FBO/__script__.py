# django_FBO newsite script (installed as a console_script entry point)

import argparse
from django.utils.crypto import get_random_string
from os import mkdir
import os.path
import sys

# Default context for all renders.
_context = {}

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

def mkfile(template, prefix=''):
    """
    Create a single file, named after the template, in the directory
    `prefix` (use the empty string to avoid a subdirectory).

    Templates are in `site_templates`.

    Templates are VERY SIMPLISTIC, they just replace variables of the
    form @@VARNAME@@ from _context.  This is done in order,
    non-recursively; we aren't parsing anything "properly".

    Missing template creates an empty file.

    """

    with open(os.path.join(prefix, template), 'wb') as fp:
        try:
            with open(
                os.path.join(THIS_DIR, 'site_templates', template),
                'rb',
            ) as tfp:
                template = tfp.read().decode('utf-8')
                for varname, value in _context.items():
                    template = template.replace('@@%s@@' % varname, value)
            fp.write(template.encode('utf-8'))
        except FileNotFoundError:
            # No template, ie empty file (eg __init__.py)
            pass
    

def newsite(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog='django-FBO-newsite',
        description='Start a new Django FBO site.',
    )
    parser.add_argument(
        'sitedir', nargs=1,
        help='subdirectory for site configuration',
    )
    parser.add_argument(
        'sitename', nargs=1,
        help='name of new site',
    )
    parser.add_argument(
        '--modules', dest='modules', action='store',
        help='modules to enable, comma separated',
    )

    args = parser.parse_args(args)
    if args.modules is None:
        modules = []
    else:
        modules = args.modules.split(',')

    sitedir = args.sitedir[0]
    _context['SITENAME'] = args.sitename[0]
    _context['SITEDIR'] = sitedir
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    _context['SECRET_KEY'] = get_random_string(50, chars)
    URLS = ''
    MODULE_SETTINGS = ''
    URL_IMPORTS = ''

    for module in modules:
        if module == 'pages':
            URL_IMPORTS += """
from django_FBO.modules.pages import PageView
"""
            URLS += """
    url(r'^(?P<slug>.*)$', PageView.as_view(), name='page'),
"""
        if module == 'blog':
            URLS += """
    url(r'^blog/', include('django_FBO.modules.blog')),
"""
            MODULE_SETTINGS += """
# FBO blog settings
FBO_BLOG_TITLE = u'My new blog'
FBO_BLOG_SUBTITLE = u'Some thoughts from someone on the internet'
FBO_BLOG_COPYRIGHT = u'(c) Copyright me, probably'
FBO_BUILD_DIR = os.path.join(BASE_DIR, 'build')
"""

    _context['URLS'] = URLS
    _context['URL_IMPORTS'] = URL_IMPORTS
    _context['MODULE_SETTINGS'] = MODULE_SETTINGS

    # We make a normal Django structure, with some strong decisions.
    # 1. Settings follow 12 Factor, broadly.
    # 2. Use CAPE, via django_cape.
    # 3. Set up very simple templates and styling.
    mkfile('manage.py')
    # FIXME: +x manage.py (within umask)
    mkfile('requirements.txt')
    mkdir(sitedir)
    mkfile('__init__.py', sitedir)
    mkfile('settings.py', sitedir)
    mkfile('urls.py', sitedir)
    mkfile('wsgi.py', sitedir)

    # From here on is broadly 'the theme'.
    mkdir('media')
    mkdir('static')
    mkdir(os.path.join('static', 'css'))
    mkfile(os.path.join('static', 'css', 'style.css'))

    mkdir('templates')
    mkfile(os.path.join('templates', 'home.html'))
    mkfile(os.path.join('templates', 'base.html'))

    for module in modules:
        if module == 'pages':
            mkfile(os.path.join('templates', 'page.html'))
        elif module == 'blog':
            mkdir(os.path.join('templates', 'blog'))
            mkfile(os.path.join('templates', 'blog', 'index.html'))
            mkfile(os.path.join('templates', 'blog', 'post.html'))
            mkfile(os.path.join('templates', 'blog', 'draft.html'))
            mkfile(os.path.join('templates', 'blog', '_pagination.html'))

if __name__ == "__main__":
    newsite()
