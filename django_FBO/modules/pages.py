"""Pages module for django_FBO.

Looks for things in {{ BASE_DIR }}/pages, by default ignoring *~
backup files. Include in your urlconf as something like:

url(r'^(?P<slug>.*)$', Page.as_view(), name='page'),

See the interspersed module if you want to have (eg) images in the
same URL hierarchy as your pages (instead of putting them in /media/
or similar, which you can do using MEDIA_ROOT and MEDIA_URL).

"""

import os.path
from django.conf import settings
from django.core.urlresolvers import reverse
from django.views.generic import DetailView

from .. import FileObject, FBO, Q, Bakeable


class PageFile(FileObject):

    def get_absolute_url(self):
        return reverse(
            'page',
            kwargs={
                'slug': self.slug,
            }
        )


class Page(FBO):
    path = os.path.join(settings.BASE_DIR, 'pages')
    _filters = [
        ~Q(name__glob='*~'),
    ]
    metadata = FileObject.MetadataInFileHead
    model = PageFile
    slug_suffices = getattr(settings, 'FBO_DEFAULT_SLUG_SUFFICES', None)
    slug_strip_index = True


class PageView(Bakeable, DetailView):
    template_name = 'page.html'
    queryset = Page()
    slug = None

    def get_template_names(self):
        override =  self.get_object().metadata.get('template')
        if override is not None:
            return [ override ]
        else:
            return [ self.template_name ]

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        if self.slug is not None:
            return queryset.get(slug=self.slug)
        else:
            return super(PageView, self).get_object(queryset)

    def get_paths(self):
        # Remember that get_absolute_url() doesn't return
        # an absolute URL, just netloc-relative.
        return [
            p.get_absolute_url()
            for p in self.get_queryset().all()
        ]
