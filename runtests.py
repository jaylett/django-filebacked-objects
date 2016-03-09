#!/usr/bin/env python
import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner


if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.test_settings'
    django.setup()
    TestRunner = get_runner(settings)

    class NoDbTestRunner(TestRunner):

        def setup_databases(self, **kwargs):
            return None

        def teardown_databases(self, old_config, **kwargs):
            pass
    
    test_runner = NoDbTestRunner()
    if len(sys.argv) > 1:
        failures = test_runner.run_tests(sys.argv[1:])
    else:
        failures = test_runner.run_tests(['tests'])
    sys.exit(bool(failures))
