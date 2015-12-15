import sys

import django
from django.conf import settings
from django.test.runner import DiscoverRunner


def runtests():
    django.setup()
    settings.configure(
        DEBUG=True,
        INSTALLED_APPS = [
            'django_FBO',
        ],
        DATABASES = {
        },
    )

    test_runner = DiscoverRunner(
        verbosity=1,
        failfast=False,
    )
    failures = test_runner.run_tests(['django_FBO', ])
    if failures:
        sys.exit(failures)


if __name__ == "__main__":
    runtests()
