from django.conf import settings
from django.core.urlresolvers import (
    get_resolver,
    resolve,
    reverse,
    RegexURLPattern,
    RegexURLResolver,
)
from django.template.response import SimpleTemplateResponse
from django.test import RequestFactory
from django.views.generic import TemplateView
import os
import os.path
import sys


class Bakeable:
    """A CBV that can be baked. This is pretty abstract."""

    def bake(self, output_dir=None, paths=None, verbosity=0, stdout=sys.stdout):
        """
        Bake one or more URLs via this view into output_dir
        (defaults to settings.FBO_BUILD_DIR). If paths is
        not None, then provides a list of URL paths to
        bake, otherwise bake all paths possible for this
        view (generally must be implemented by the view).
        """

        if output_dir is None:
            output_dir = settings.FBO_BUILD_DIR
        if paths is None:
            if verbosity > 1:
                stdout.write(" > fetching paths (in %s)\n" % str(self))
            paths = self.get_paths()

        factory = RequestFactory()
        for path in paths:
            if verbosity > 2:
                stdout.write(" * %s\n" % str(path))
            filename = self.get_filename(path)
            out_fname = os.path.join(output_dir, filename)
            os.makedirs(
                os.path.dirname(out_fname),
                exist_ok=True,
            )
            with open(out_fname, 'wb') as f:
                match = resolve(path)
                request = factory.get(path)
                response = match.func(
                    request,
                    *match.args,
                    **match.kwargs
                )
                if isinstance(response, SimpleTemplateResponse):
                    response.render()
                if response.status_code // 100 == 2:
                    if response.streaming:
                        # FIXME: do something with this.
                        f.write(
                            "Unhandled: streaming responses.".encode('utf-8'),
                        )
                        pass
                    else:
                        # FIXME: should inject a meta header into HTML
                        # so that .charset is preserved. There may be
                        # other headers on the response that are worth
                        # preserving in similar ways.
                        f.write(response.content)
                else:
                    # FIXME redirects we could trap and write out
                    # either HTML files with meta refresh, or suitable
                    # configuration for Apache, nginx &c. (Or both.)
                    f.write(
                        (
                            "Unhandled status code %i." % response.status_code
                        ).encode('utf-8'),
                    )

    def get_filename(self, path):
        # FIXME: won't work with non-Unixoid file names.
        if path.startswith('/'):
            # Which should be always!
            path = path[1:]
        elif path!='':
            raise ValueError("Path should start with '/'.")
        components = path.split('/')
        if components[-1] == '':
            components[-1] = 'index'
        if '.' not in components[-1]:
            components[-1] += '.html'

        return '/'.join(components)

    def get_paths(self):
        """
        Returns a sequence of paths, ie netloc-relative URLs, each of
        which will be turned into a ResolverMatch via resolve(), and
        then rendered 'as normal' (using a mock HttpRequest object
        via django.test.client.RequestFactory).

        By default, figures out the URL using reverse().
        This will only work for singleton views.
        """

        return tuple(
            get_resolver().reverse(self)
        )


class BakeableTemplateView(Bakeable, TemplateView):
    # This one just works, so make it simple to use.
    pass


def bake(output_dir=None, resolver=None, verbosity=0, stdout=sys.stdout):
    if resolver is None:
        resolver = get_resolver()
    if verbosity > 1:
        stdout.write("Baking %s\n" % str(resolver))
    if isinstance(resolver, RegexURLResolver):
        for up in resolver.url_patterns:
            bake(output_dir, up, verbosity, stdout)
    elif isinstance(resolver, RegexURLPattern):
        view = resolver.callback
        # `view` is a callable, but it may also be
        # an instance of a CBV, which is all we support.
        # If it's a subclass of our Bakeable then
        # we can bake it, because it provides the support
        # to do so.
        if hasattr(view, 'view_class'):
            view_class = view.view_class
            view_instance = view_class(**view.view_initkwargs)
            if isinstance(view_instance, Bakeable):
                if resolver.regex.groups == 0:
                    # This is unique, so ensure this URL gets baked.
                    # Otherwise (eg) homepages are really hard to
                    # get right. You must provide a name for this
                    # to work; otherwise we SILENTLY do nothing, which
                    # isn't friendly.
                    #
                    # Note this may mean that we write something out
                    # twice. This really shouldn't cause problems,
                    # although it probably will at some point.
                    if resolver.name is not None:
                        view_instance.bake(
                            output_dir,
                            [reverse(resolver.name)],
                            verbosity,
                            stdout,
                        )
                else:
                    view_instance.bake(
                        output_dir,
                        None,
                        verbosity,
                        stdout,
                    )
            else:
                if verbosity > 0:
                    stdout.write(" ! skipping %s\n" % str(view))
