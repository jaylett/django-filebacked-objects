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
    DateDetailView as _DateDetailView,
    ListView,
)
from markdown_deux import markdown
from .. import FBO, FileObject, Q, Bakeable


def get_drafts_prefix():
    # Note this must function in a regular expression as well.
    return getattr(settings, 'FBO_BLOG_DRAFTS_PREFIX', 'drafts/')


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
        if self.slug.startswith(get_drafts_prefix()):
            return reverse(
                'blog-draft-detail',
                kwargs={
                    'slug': self.slug,
                },
            )
        else:
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
        """
        If we can split the slug into YEAR/MONTH/DAY/SLUG,
        do so; otherwise the slug remains unchanged.
        """

        try:
            slug = super().slug
        except:
            raise KeyError('slug')
        try:
            _, _, _, slug = slug.split('/', 4)
            return slug
        except:
            return slug

    @property
    def date(self):
        # figure out the date from the name, else delegate
        # to published
        try:
            year, month, day, _ = self.name.split('/', 4)
            return timezone.now().replace(
                year=int(year),
                month=int(month),
                day=int(day),
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
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
    _order_by = [ 'date' ]
    metadata = BlogPostFile.MetadataInFileHead
    model = BlogPostFile
    slug_suffices = getattr(settings, 'FBO_DEFAULT_SLUG_SUFFICES', None)
    slug_strip_index = True

    def exclude_drafts(self):
        return self.exclude(
            Q(status='draft') |
            Q(name__startswith=get_drafts_prefix()),
        )

    def find_next(self, obj):
        _iter = iter(self.exclude_drafts())
        try:
            for candidate in _iter:
                if candidate == obj:
                    return next(_iter)
        except StopIteration:
            return None

    def find_previous(self, obj):
        _iter = iter(self.exclude_drafts())
        previous = None
        try:
            for candidate in _iter:
                if candidate == obj:
                    return previous
                else:
                    previous = candidate
        except StopIteration:
            return None


class BakeableBlogMixin(Bakeable):
    template_name = 'blog/index.html'
    queryset = BlogPost().exclude_drafts()
    date_field = 'date'
    uses_datetime_field = True
    paginate_by = 10
    make_object_list = True

    def get_url_name(self):
        return self.url_name

    def _paginate_for_baking(self, qs, date):
        page_size = self.get_paginate_by(qs)
        if page_size:
            self.kwargs = { 'page': 1 }
            paginator, page, queryset, is_paginated = self.paginate_queryset(qs, page_size)
            for page in range(paginator.num_pages):
                yield self.date_to_url(date, page+1)
        else:
            yield self.date_to_url(date)

    def get_date_to_url_kwargs(self, date):
        raise NotImplementedError

    def date_to_url(self, date, page=None):
        kwargs = self.get_date_to_url_kwargs(date)
        if page is None or page == 1:
            return reverse(
                self.get_url_name(),
                kwargs=kwargs,
            )
        else:
            kwargs['page'] = page
            return reverse(
                self.get_url_name() + '-paginated',
                kwargs=kwargs,
            )


class ArchiveIndexView(BakeableBlogMixin, _ArchiveIndexView):
    url_name = 'blog-index'

    def get_paths(self):
        return self._paginate_for_baking(
            self.get_queryset(),
            timezone.now(),
        )

    def get_date_to_url_kwargs(self, date):
        return {}


class BakeableBlogDateMixin(BakeableBlogMixin):
    month_format = '%m'

    def get_date_list_period_for_baking(self):
        period = self.get_url_name()
        if period.startswith('blog-'):
            period = period[5:]
        return period

    def get_paths(self):
        # Marvel at how much duplication there is between this and the
        # CBV date system! All the fun of millions of classes, without
        # the extension hooks you actually need.
        kind = self.get_date_list_period_for_baking()

        for date in self.get_queryset().datetimes(
            field_name=self.get_date_field(),
            kind=kind,
            ordering='ASC',
        ):
            # For each date, paginate!
            date_field = self.get_date_field()
            since = self._make_date_lookup_arg(date)
            # _get_next_year, _get_next_month, _get_next_day
            until = self._make_date_lookup_arg(
                getattr(self, '_get_next_' + kind)(date)
            )
            lookup_kwargs = {
                '%s__gte' % date_field: since,
                '%s__lt' % date_field: until,
            }
            qs = self.get_dated_queryset(**lookup_kwargs)
            for path in self._paginate_for_baking(qs, date):
                yield path


class YearArchiveView(BakeableBlogDateMixin, _YearArchiveView):
    url_name = 'blog-year'

    def get_date_to_url_kwargs(self, date):
        return {
            'year': '%04d' % date.year,
        }


class MonthArchiveView(BakeableBlogDateMixin, _MonthArchiveView):
    url_name = 'blog-month'

    def get_date_to_url_kwargs(self, date):
        return {
            'year': '%04d' % date.year,
            'month': '%02d' % date.month,
        }


class DayArchiveView(BakeableBlogDateMixin, _DayArchiveView):
    url_name = 'blog-day'

    def get_date_to_url_kwargs(self, date):
        return {
            'year': '%04d' % date.year,
            'month': '%02d' % date.month,
            'day': '%02d' % date.day,
        }


class DateDetailView(Bakeable, _DateDetailView):
    template_name = 'blog/post.html'
    queryset = BlogPost()
    date_field = 'date'
    uses_datetime_field = True
    month_format = '%m'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next_object'] = self.queryset.find_next(self.object)
        context['previous_object'] = self.queryset.find_previous(self.object)
        return context

    def get_paths(self):
        # Remember that get_absolute_url() doesn't return
        # an absolute URL, just netloc-relative.
        return [
            p.get_absolute_url()
            for p in self.queryset.all()
        ]


class DraftsList(ListView):
    queryset = BlogPost().filter(
        Q(name__startswith=get_drafts_prefix())
    )
    paginate_by = None

    def get_template_names(self):
        return [ 'blog/drafts_index.html', 'blog/index.html' ]


class DraftDetailView(Bakeable, _DetailView):
    template_name = 'blog/draft.html'
    queryset = BlogPost().filter(
        name__startswith=get_drafts_prefix(),
    )

    def get_paths(self):
        # Remember that get_absolute_url() doesn't return
        # an absolute URL, just netloc-relative.
        return [
            p.get_absolute_url()
            for p in self.queryset.all()
        ]


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
    # First our indexes. Each comes twice, the second URL dealing with
    # pagination. We have: everything, year, month and day.
    url(r'^$', ArchiveIndexView.as_view(), name='blog-index'),
    url(r'^p(?P<page>[0-9]+)/$', ArchiveIndexView.as_view(), name='blog-index-paginated'),
    url(r'^(?P<year>[0-9]{4})/$', YearArchiveView.as_view(), name='blog-year'),
    url(r'^(?P<year>[0-9]{4})/p(?P<page>[0-9]+)/$', YearArchiveView.as_view(), name='blog-year-paginated'),
    url(r'^(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/$', MonthArchiveView.as_view(), name='blog-month'),
    url(r'^(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/p(?P<page>[0-9]+)/$', MonthArchiveView.as_view(), name='blog-month-paginated'),
    url(r'^(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/$', DayArchiveView.as_view(), name='blog-day'),
    url(r'^(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/p(?P<page>[0-9]+)/$', DayArchiveView.as_view(), name='blog-day-paginated'),
    # Then a date-based view of a single blog post.
    url(r'^(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/(?P<slug>.*)$', DateDetailView.as_view(), name='blog-detail'),
    # Now our Atom feed.
    url(r'^index.atom$', BlogFeed.as_view(
        feed_title = settings.FBO_BLOG_TITLE,
        feed_subtitle = settings.FBO_BLOG_SUBTITLE,
        feed_copyright = settings.FBO_BLOG_COPYRIGHT,
    ), name='blog-feed'),
    # Drafts list -- this doesn't get baked, so it won't appear in the
    # live site.
    url(r'^drafts/$', DraftsList.as_view()),
    # And finally our drafts. Note that we include the prefix directly
    # into the regular expression, so the prefix must not contain any
    # RE atoms that aren't literals.
    url(
        r'^(?P<slug>' + get_drafts_prefix() + '.*)$',
        DraftDetailView.as_view(),
        name='blog-draft-detail',
    ),
]
