from django.conf.urls import url
from django.contrib.staticfiles import utils
from django.core.files.storage import FileSystemStorage
from django.test import TestCase, override_settings
import os.path
import tempfile

from django_FBO import bake
from django_FBO.modules import pages


TEST_BASE_DIR = os.path.join(
    os.path.dirname(__file__),
    'files/pages',
)
TEST_TEMPLATES_DIR = os.path.join(
    os.path.dirname(__file__),
    'templates',
)


class Page(pages.Page):
    path = TEST_BASE_DIR


class TestPageObject(TestCase):
    """Does the (almost) off-the-shelf Page FBO work?"""
    # The only thing we've done is to reconfigure the
    # base directory for the FBO storage, so we can use
    # a test hierarchy for that.

    def test_simple(self):
        pages = Page().objects.all()
        self.assertEqual(1, pages.count())
        page = pages[0]
        self.assertEqual('My little page', page.title)
        self.assertEqual('Just something simple.', page.content.strip())

        _page = Page().objects.get(slug='slug1')
        self.assertEqual(page.slug, _page.slug)
        self.assertEqual(page.path, _page.path)


class PageView(pages.PageView):
    queryset = Page()


urlpatterns = [
    url(r'^$', PageView.as_view(slug='slug1'), name='home'),
    url(r'^(?P<slug>.*)/$', PageView.as_view(), name='page'),
]


@override_settings(
    ROOT_URLCONF='tests.modules.test_pages',
)
class TestPageView(TestCase):
    """Does the (almost) off-the-shelf PageView work?"""
    # As previously, we're just changing the base directory
    # that is searched for FBOs.

    def test_simple(self):
        """Test a couple of common patterns."""

        resp = self.client.get('/')
        self.assertEqual(200, resp.status_code)
        self.assertEqual('text/html; charset=utf-8', resp['Content-Type'])
        self.assertEqual(
            b'My little page: Just something simple.',
            resp.content.strip(),
        )

        resp = self.client.get('/slug1')
        self.assertEqual(301, resp.status_code)
        resp = self.client.get(resp['Location'])
        self.assertEqual(200, resp.status_code)
        self.assertEqual('text/html; charset=utf-8', resp['Content-Type'])
        self.assertEqual(
            b'My little page: Just something simple.',
            resp.content.strip(),
        )

    def test_baking(self):
        """Test that we can bake pages."""


        with tempfile.TemporaryDirectory() as outdir:
            storage = FileSystemStorage(location=outdir)
            bake(outdir)
            # We should have index.html and slug1.html
            EXPECTED_FILES = { 'index.html', 'slug1/index.html' }
            self.assertEqual(
                EXPECTED_FILES,
                set(utils.get_files(storage)),
            )

            for fname in EXPECTED_FILES:
                with open(
                    os.path.join(outdir, fname),
                    'rb',
                ) as fp:
                    self.assertEqual(
                        b'My little page: Just something simple.',
                        fp.read().strip(),
                    )
