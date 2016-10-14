from django.conf.urls import include, url
from django.contrib.staticfiles import utils
from django.core.files.storage import FileSystemStorage
from django.test import TestCase, override_settings
import os.path
import tempfile

from django_FBO import bake
from django_FBO.modules import blog


urlpatterns = [
    url(r'^blog/', include('django_FBO.modules.blog')),
]


class TestBlog(TestCase):

    def test_simple(self):
        # Have to have enough to paginate. They are
        # all within the same year, so archive & year
        # will paginate, but month & day will not.
        self.assertEqual(
            17,
            blog.BlogPost().objects.count(),
        )


@override_settings(
    ROOT_URLCONF='tests.modules.test_blog',
)
class TestBlogView(TestCase):
    """Do the off-the-shelf blog views work?"""

    def test_simple(self):
        """Test a couple of common patterns."""

        resp = self.client.get('/blog/')
        self.assertEqual(200, resp.status_code)
        self.assertEqual('text/html; charset=utf-8', resp['Content-Type'])
        self.assertEqual(
            b'Blog index page. 1 of 2 pages.',
            resp.content.strip(),
        )

        resp = self.client.get('/blog/p2/')
        self.assertEqual(200, resp.status_code)
        self.assertEqual('text/html; charset=utf-8', resp['Content-Type'])
        self.assertEqual(
            b'Blog index page. 2 of 2 pages.',
            resp.content.strip(),
        )

        resp = self.client.get('/blog/2016/')
        self.assertEqual(200, resp.status_code)
        self.assertEqual('text/html; charset=utf-8', resp['Content-Type'])
        self.assertEqual(
            b'Blog index page. 1 of 2 pages.',
            resp.content.strip(),
        )

        resp = self.client.get('/blog/2016/p2/')
        self.assertEqual(200, resp.status_code)
        self.assertEqual('text/html; charset=utf-8', resp['Content-Type'])
        self.assertEqual(
            b'Blog index page. 2 of 2 pages.',
            resp.content.strip(),
        )

        resp = self.client.get('/blog/2016/06/')
        self.assertEqual(200, resp.status_code)
        self.assertEqual('text/html; charset=utf-8', resp['Content-Type'])
        self.assertEqual(
            b'Blog index page. 1 of 1 pages.',
            resp.content.strip(),
        )

        resp = self.client.get('/blog/2016/07/')
        self.assertEqual(200, resp.status_code)
        self.assertEqual('text/html; charset=utf-8', resp['Content-Type'])
        self.assertEqual(
            b'Blog index page. 1 of 1 pages.',
            resp.content.strip(),
        )

        resp = self.client.get('/blog/2016/06/21/')
        self.assertEqual(200, resp.status_code)
        self.assertEqual('text/html; charset=utf-8', resp['Content-Type'])
        self.assertEqual(
            b'Blog index page. 1 of 1 pages.',
            resp.content.strip(),
        )

        resp = self.client.get('/blog/2016/07/21/')
        self.assertEqual(200, resp.status_code)
        self.assertEqual('text/html; charset=utf-8', resp['Content-Type'])
        self.assertEqual(
            b'Blog index page. 1 of 1 pages.',
            resp.content.strip(),
        )

        # Not enough entries for this.
        resp = self.client.get('/blog/2016/07/21/p2/')
        self.assertEqual(404, resp.status_code)

        resp = self.client.get('/blog/2016/06/21/single-post')
        self.assertEqual(200, resp.status_code)
        self.assertEqual('text/html; charset=utf-8', resp['Content-Type'])
        self.assertEqual(
            b'Single post: Single, simple, post.',
            resp.content.strip(),
        )

        resp = self.client.get('/blog/2016/07/21/single-post')
        self.assertEqual(200, resp.status_code)
        self.assertEqual('text/html; charset=utf-8', resp['Content-Type'])
        self.assertEqual(
            b'Single post: Single, simple, post.',
            resp.content.strip(),
        )

        resp = self.client.get('/blog/drafts/')
        self.assertEqual(200, resp.status_code)
        self.assertEqual('text/html; charset=utf-8', resp['Content-Type'])
        self.assertEqual(
            b'Blog drafts page. 2 drafts.',
            resp.content.strip(),
        )

    def test_baking(self):
        """Test that we can bake pages."""

        with tempfile.TemporaryDirectory() as outdir:
            storage = FileSystemStorage(location=outdir)
            bake(outdir)
            # We should have various.
            EXPECTED_FILES = {
                'blog/index.html',
                'blog/p2/index.html',
                'blog/2016/index.html',
                'blog/2016/p2/index.html',
                'blog/2016/05/index.html',
                'blog/2016/06/index.html',
                'blog/2016/07/index.html',
                'blog/2016/05/21/index.html',
                'blog/2016/06/21/index.html',
                'blog/2016/07/21/index.html',
                'blog/2016/05/21/single-post.html',
                'blog/2016/06/21/single-post.html',
                'blog/2016/07/21/single-post.html',
                'blog/2016/05/21/second-post.html',
                'blog/2016/06/21/second-post.html',
                'blog/2016/07/21/second-post.html',
                'blog/2016/05/21/third-post.html',
                'blog/2016/06/21/third-post.html',
                'blog/2016/07/21/third-post.html',
                'blog/2016/05/21/fourth-post.html',
                'blog/2016/06/21/fourth-post.html',
                'blog/2016/07/21/fourth-post.html',
                'blog/2016/05/21/fifth-post.html',
                'blog/2016/06/21/fifth-post.html',
                'blog/2016/07/21/fifth-post.html',
                'blog/index.atom',
                'blog/drafts/draft-post.html',
                'blog/drafts/second-draft-post.html',
            }
            self.assertEqual(
                EXPECTED_FILES,
                set(utils.get_files(storage)),
            )
