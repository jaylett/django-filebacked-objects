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
    slug_suffices = [ '.md' ]


class TestPageObject(TestCase):
    """Does the (almost) off-the-shelf Page FBO work?"""
    # The only thing we've done is to reconfigure the
    # base directory for the FBO storage, so we can use
    # a test hierarchy for that.

    def test_simple(self):
        pages = Page().objects.all().order_by('name')
        self.assertEqual(3, pages.count())
        # about, index, subdir/
        page = pages[0]
        self.assertEqual('About', page.title)
        self.assertEqual('About this.', page.content.strip())
        self.assertEqual('about', page.slug)

        _page = Page().objects.get(slug='about')
        self.assertEqual(page.slug, _page.slug)
        self.assertEqual(page.path, _page.path)

        page = pages[1]
        self.assertEqual('Index that gets trimmed', page.title)
        self.assertEqual('Index.', page.content.strip())
        self.assertEqual('', page.slug)

        page = pages[2]
        self.assertEqual('Subdir!', page.title)
        self.assertEqual('A subdir index.', page.content.strip())
        self.assertEqual('subdir/', page.slug)


class PageView(pages.PageView):
    queryset = Page()


urlpatterns = [
    url(r'^(?P<slug>.*)$', PageView.as_view(), name='page'),
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
            b'slug=',
            resp.content.strip(),
        )

        resp = self.client.get('/about')
        self.assertEqual(200, resp.status_code)
        self.assertEqual('text/html; charset=utf-8', resp['Content-Type'])
        self.assertEqual(
            b'slug=about',
            resp.content.strip(),
        )

    def test_baking(self):
        """Test that we can bake pages."""

        with tempfile.TemporaryDirectory() as outdir:
            storage = FileSystemStorage(location=outdir)
            bake(outdir)
            # We should have index.html, about/index.html, subdir/index.html
            EXPECTED_FILES = [
                'index.html',
                'about.html',
                'subdir/index.html',
            ]
            EXPECTED_SLUGS = [
                '',
                'about',
                'subdir/',
            ]
            self.assertEqual(
                set(EXPECTED_FILES),
                set(utils.get_files(storage)),
            )

            for fname, slug in zip(EXPECTED_FILES, EXPECTED_SLUGS):
                with open(
                    os.path.join(outdir, fname),
                    'rb',
                ) as fp:
                    self.assertEqual(
                        b'slug=' + slug.encode('utf-8'),
                        fp.read().strip(),
                    )
