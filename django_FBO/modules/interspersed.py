"""Interspersed binary & pages module for django_FBO.

Put binary and pages in {{ BASE_DIR }}/pages, and:

urlpatterns += get_interspersed_urls(
    exts=[ 'jpg', 'png', 'pdf' ],
)

which will give you both your page and binary URLs. Alternatively,
if you want to prefix things, you can use:

urlpatterns = [
    url(r'^prefix/', include('django_FBO.modules.interspersed')),
]

and set the following in settings:

FBO_INTERSPERSED_EXTS = [ 'jpg', 'png', 'pdf' ]

(The default list is empty.)
"""

from django.conf import settings
from django.conf.urls import url
from django.http import HttpResponse
from functools import reduce
import mimetypes
import os.path

from .. import Q
from .pages import PageView
from .binary import BinaryFBO, BinaryView


class InterspersedBinaryFBO(BinaryFBO):
    path = os.path.join(settings.BASE_DIR, 'pages')


class InterspersedBinaryView(BinaryView):
    queryset = InterspersedBinaryFBO()
    ext = None

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.ext is None:
            # This is weird; there isn't a good reason to do this,
            # and plenty of reasons not to.
            return self.queryset
        else:
            return self.queryset.filter(name__glob='*.%s' % self.ext)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        mime_type, encoding = mimetypes.guess_type(
            self.object.path,
            strict=False,
        )
        if mime_type is None:
            mime_type = 'application/octet-stream'
        resp = HttpResponse(
            content=self.object.content,
            content_type=mime_type,
        )
        if encoding is not None:
            resp['Content-Encoding'] = encoding
        return resp


class InterspersedPageView(PageView):
    pass


def get_interspersed_urls(exts, binaryview_kwargs=None, pageview_kwargs=None):
    # Note: you can prefix your URLs via existing urlpatterns mechanisms.

    # FIXME: this could be more efficient by making a single FBO with
    # pageview_excludes as a filter, then enumerating it, and passing
    # that to all the binary views. (It should be possible to avoid
    # walking the tree so much this way. At the moment it'll be done
    # once per request, which is tedious.)
    urls = []
    pageview_excludes = []
    if binaryview_kwargs is None:
        binaryview_kwargs = {}
    for ext in exts:
        urls.append(
            url(
                r'^(?P<slug>.*\.%(ext)s)$' % {
                    'ext': ext,
                },
                InterspersedBinaryView.as_view(
                    ext=ext,
                    **binaryview_kwargs
                ),
                name=ext,
            ),
        )
        pageview_excludes.append(
            Q(name__glob='*.%s' % ext),
        )
    if pageview_kwargs is None:
        pageview_kwargs = {}
    if 'queryset' not in pageview_kwargs:
        pageview_kwargs['queryset'] = InterspersedPageView.queryset
    pageview_kwargs['queryset'] = pageview_kwargs['queryset'].exclude(
        reduce(
            lambda x, y: x | y,
            pageview_excludes,
        )
    )
    urls.append(
        url(
            r'^(?P<slug>.*)$',
            InterspersedPageView.as_view(**pageview_kwargs),
            name='page',
        )
    )
    return urls


urlpatterns = get_interspersed_urls(
    getattr(settings, 'FBO_INTERSPERSED_EXTS', []),
)
