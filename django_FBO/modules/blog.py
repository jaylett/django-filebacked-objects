import os.path
from datetime import datetime
from django.conf import settings
from django.conf.urls import url
from django.contrib.syndication.views import Feed as _Feed
from django.core.urlresolvers import reverse
from django.db.models.fields import TextField
from django.utils import timezone
from django.utils.feedgenerator import Atom1Feed
from django.views.generic import (
    DetailView as _DetailView,
    ArchiveIndexView as _ArchiveIndexView,
    YearArchiveView as _YearArchiveView,
    MonthArchiveView as _MonthArchiveView,
    DayArchiveView as _DayArchiveView,
)
from markdown_deux import markdown
from .. import FBO, FileObject, Q


class Author(object):
    # Currently just used for generating the feed, but
    # in theory could be populated automatically for a
    # BlogPostFile and so made more useful.
    #
    # Note that right now we don't actually populate the
    # url at all. This is laziness and not having needed
    # to as yet.
    def __init__(self, name, url=None):
        self.name = name
        self.url = url


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


class BetterAtomFeed(Atom1Feed):
    def add_item_elements(self, handler, item):
        super(BetterAtomFeed, self).add_item_elements(handler, item)
        authors = item.get('authors', [])
        for author in authors:
            if author is None:
                continue
            handler.startElement("author", {})
            handler.addQuickElement("name", author.name)
            if author.url is not None:
                handler.addQuickElement("uri", author.url)
            handler.endElement("author")


class Feed(_Feed):
    feed_type = BetterAtomFeed

    def __init__(self, paginate_by):
        self.paginate_by = paginate_by

    def items(self):
        return self.queryset[:self.paginate_by]

    def item_title(self, item):
        return item.title

    def item_pubdate(self, item):
        return item.date

    def item_updateddate(self, item):
        return item.date

    def item_description(self, item):
        return markdown(item.content)

    def item_extra_kwargs(self, item):
        extra = {}
        if hasattr(item, 'author'):
            # FIXME: pull url if it exists
            author_obj = Author(item.author, None)
            extra['authors'] = [ author_obj ]
        return extra


class FeedMixin(object):
    """
    Mixin to a ListView to output an Atom feed instead of HTML.
    """

    # empty Atom feeds are empty, not 404 (ListView behaviour)
    allow_empty = True
    # conventionally, feeds have 10 items
    paginate_by = 10

    # Defaults for feed-level properties.
    feed_title = None
    feed_subtitle = None
    feed_link = None
    feed_copyright = None

    # Feed class itself
    feed_class = Feed

    def get_title(self):
        return self.feed_title

    def get_subtitle(self):
        return self.feed_subtitle

    def get_link(self):
        return self.feed_link

    def get_copyright(self):
        return self.feed_copyright

    def render_to_response(self, context):
        feedview = self.feed_class(self.paginate_by)
        feedview.title = self.get_title()
        feedview.subtitle = self.get_subtitle()
        feedview.link = self.get_link()
        feedview.queryset = self.get_queryset()
        feedview.feed_copyright = self.get_copyright()
        feedview.item_copyright = self.get_copyright()
        return feedview(self.request, *self.args, **self.kwargs)


class BlogFeed(FeedMixin, ArchiveIndexView):
    blog_index_url_name = 'blog-index'

    def get_link(self):
        return reverse('blog-index')



# Just include this directly, unless you want to customise
# any of the view defaults.
urlpatterns = [
    url(r'^$', ArchiveIndexView.as_view(), name='blog-index'),
    url(r'^(?P<year>[0-9]{4})/$', YearArchiveView.as_view()),
    url(r'^(?P<year>[0-9]{4})/(?P<month>[0-9]+)/$', MonthArchiveView.as_view()),
    url(r'^(?P<year>[0-9]{4})/(?P<month>[0-9]+)/(?P<day>[0-9]+)/$', DayArchiveView.as_view()),
    url(r'^(?P<year>[0-9]{4})/(?P<month>[0-9]+)/(?P<day>[0-9]+)/(?P<slug>.*)/$', DetailView.as_view(), name='blog-detail'),
    url(r'^index.atom$', BlogFeed.as_view(
        feed_title = settings.FBO_BLOG_TITLE,
        feed_subtitle = settings.FBO_BLOG_SUBTITLE,
        feed_copyright = settings.FBO_BLOG_COPYRIGHT,
    ), name='blog-feed'),
]
