import os.path
from datetime import datetime
from django.conf import settings
from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.db.models.fields import TextField
from django.views.generic import (
    DetailView as _DetailView,
    ArchiveIndexView as _ArchiveIndexView,
    YearArchiveView as _YearArchiveView,
    MonthArchiveView as _MonthArchiveView,
    DayArchiveView as _DayArchiveView,
)
from django.utils import timezone
from .. import FBO, FileObject, Q


class BlogPostFile(FileObject):

    def get_absolute_url(self):
        return reverse(
            'blog-detail',
            kwargs={
                'year': '%04d' % self.date.year,
                'month': '%02d' % self.date.month,
                'day': '%02d' % self.date.day,
                'slug': self.slug,
            }
        )

    @property
    def slug(self):
        try:
            _, _, _, slug = self.name.split('/', 4)
            return slug
        except:
            raise KeyError('slug')

    @property
    def date(self):
        # figure out the date from the name, else delegate
        # to published
        try:
            year, month, day, _ = self.name.split('/', 4)
            return datetime(
                year=int(year),
                month=int(month),
                day=int(day),
                tzinfo=timezone.utc,
            )
        except:
            return self.published

    @property
    def published(self):
        if 'published' in self.metadata:
            return self.metadata['published']
        else:
            return self.storage.get_created_time(self.name)

class BlogPost(FBO):
    path = os.path.join(settings.BASE_DIR, 'posts')
    _filters = [
        ~Q(name__glob='*~'),
    ]
    metadata = BlogPostFile.MetadataInFileHead
    model = BlogPostFile


class ArchiveIndexView(_ArchiveIndexView):
    template_name = 'blog/index.html'
    queryset = BlogPost()
    date_field = 'date'
    uses_datetime_field = True
    paginate_by = 10


class YearArchiveView(_YearArchiveView):
    template_name = 'blog/index.html'
    queryset = BlogPost()
    date_field = 'date'
    uses_datetime_field = True
    month_format = '%m'
    make_object_list = True
    paginate_by = 10


class MonthArchiveView(_MonthArchiveView):
    template_name = 'blog/index.html'
    queryset = BlogPost()
    date_field = 'date'
    uses_datetime_field = True
    month_format = '%m'
    paginate_by = 10


class DayArchiveView(_DayArchiveView):
    template_name = 'blog/index.html'
    queryset = BlogPost()
    date_field = 'date'
    uses_datetime_field = True
    month_format = '%m'
    paginate_by = 10


class DetailView(_DetailView):
    template_name = 'blog/post.html'
    queryset = BlogPost()

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        name = '%04d/%02d/%02d/%s' % (
            int(self.kwargs.get('year', None)),
            int(self.kwargs.get('month', None)),
            int(self.kwargs.get('day', None)),
            self.kwargs.get('slug', None),
        )
        return queryset.get(name=name)


# Just include this directly, unless you want to customise
# any of the view defaults.
urlpatterns = [
    url(r'^$', ArchiveIndexView.as_view(), name='blog-index'),
    url(r'^(?P<year>[0-9]{4})/$', YearArchiveView.as_view()),
    url(r'^(?P<year>[0-9]{4})/(?P<month>[0-9]+)/$', MonthArchiveView.as_view()),
    url(r'^(?P<year>[0-9]{4})/(?P<month>[0-9]+)/(?P<day>[0-9]+)/$', DayArchiveView.as_view()),
    url(r'^(?P<year>[0-9]{4})/(?P<month>[0-9]+)/(?P<day>[0-9]+)/(?P<slug>.*)/$', DetailView.as_view(), name='blog-detail'),
    ]
