from setuptools import setup

PACKAGE = 'django_FBO'
VERSION = '3.4.0'

setup(
    name=PACKAGE,
    version=VERSION,
    description="Access file-backed objects in something resembling the ORM.",
    packages=[
        'django_FBO',
        'django_FBO.modules',
        'django_FBO.management',
        'django_FBO.management.commands',
    ],
    package_data={
        'django_FBO': [
            'site_templates/*.py',
            'site_templates/requirements.txt',
            'site_templates/static/css/*.css',
            'site_templates/templates/*.html',
            'site_templates/templates/blog/*.html',
        ],
    },
    license='MIT',
    author='James Aylett',
    author_email='james@tartarus.org',
    entry_points={
        'console_scripts': [
            'django-fbo-newsite = django_FBO.__script__:newsite'
        ],
    },
    install_requires=[
        'Django~=1.10',
        'PyYAML~=3.11',
    ],
    url = 'https://github.com/jaylett/django-filebacked-objects',
    classifiers = [
        'Intended Audience :: Developers',
        'Framework :: Django',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
)
