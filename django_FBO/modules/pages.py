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


class PageView(Bakeable, DetailView):
    template_name = 'page.html'
    queryset = Page()
    slug = None
    
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
            for p in self.queryset.all()
        ]
