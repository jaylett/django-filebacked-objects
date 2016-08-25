from django.conf import settings
from django.core.management.base import BaseCommand

from ...baking import bake


class Command(BaseCommand):
    help = """Bake all FBO-based views."""

    def add_arguments(self, parser):
        parser.add_argument(
            'outdir',
            nargs='?',
            help='directory to build to (defaults to %s)' % settings.FBO_BUILD_DIR,
        )

    def handle(self, *args, **options):
        bake(
            output_dir=options['outdir'],
            verbosity=options['verbosity'],
            stdout=self.stdout,
        )
