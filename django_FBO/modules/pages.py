import os.path
from django.conf import settings
from django.views.generic import DetailView

from .. import FileObject, FBO, Q


class Page(FBO):
    path = os.path.join(settings.BASE_DIR, 'pages')
    _filters = [
        ~Q(name__glob='*~'),
    ]
    metadata = FileObject.MetadataInFileHead


class PageView(DetailView):
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
