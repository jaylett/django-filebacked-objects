try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

PACKAGE = 'django_FBO'
VERSION = '1.0.0'

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
    license='MIT',
    author='James Aylett',
    author_email='james@tartarus.org',
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
