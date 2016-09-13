"""Binary module for django_FBO.

Drop this into your urlconf, perhaps as:

url(r'^binary/(?P<slug>.*)$', ObjectView.as_view(), name='binary'),

and drop things into {{ BASE_DIR }}/binaries. However that's unusual,
because you can use MEDIA_ROOT and MEDIA_URL for that. More likely is
that you want pages and binary objects interspersed, in which case you
want to use the interspersed module.

This isn't bootstrappable via django-fbo-newsite, because it's
somewhat niche. I use it to migrate existing sites in, but I'd be
unlikely to use it for brand new ones. Either way, there's usually
going to be some jockeying to make things work.
"""

from django.conf import settings
from django.core.urlresolvers import reverse
import os.path

from .. import FileObject
from .pages import Page, PageView


class BinaryFileObject(FileObject):

    def get_absolute_url(self):
        # [1] to get the ext, then strip a leading '.'
        ext = os.path.splitext(self.name)[1].lstrip('.')
        return reverse(
            ext,
            kwargs={
                'slug': self.slug,
            }
        )

    def _load_content(self):
        with self.storage.open(self.name) as _file:
            return _file.read()


class BinaryFBO(Page):
    metadata = None
    model = BinaryFileObject
    path = os.path.join(settings.BASE_DIR, 'binaries')


class BinaryView(PageView):
    queryset = BinaryFBO()
