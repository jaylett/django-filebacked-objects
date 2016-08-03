# Django file-backed objects

[![Circle CI](https://circleci.com/gh/jaylett/django-filebacked-objects.svg?style=svg)](https://circleci.com/gh/jaylett/django-filebacked-objects)

Access file-backed objects in something resembling the ORM. You should
be able to use generic views to build on them.

## Why?

[Statically-built sites](https://www.staticgen.com/) are all the rage,
but most of them concentrate on a narrow range of file formats and,
often, require that your output space matches your input space.

Separately,
[django-bakery](https://django-bakery.readthedocs.org/en/latest/)
provides a way of taking a Django-based website and "baking" it to
flat files for serving.

After playing with various static site generators for some fairly
specific needs, I ended up wanting a way of controlling my output
space in the manner of Django (which pointed towards `django-bakery`),
but with a range of flat files as inputs, which required something
new.

## Getting started

```
$ pip install django_FBO
$ django-FBO-newsite --modules=pages,blog <sitename>
$ pip install -r requirements.txt
```

This will create a Django project, pre-configured to run a simple FBO
site, including the pages and blog module configurations. It will
create a Django modern-style `<sitename>` directory containing
`settings.py`, `wsgi.py` and `urls.py`; the settings relies on
defaults provided by `django_FBO`, and allows [12 factor]-style
environment overriding.

You have to install the requirements FBO sets up for you, because
we're opinionated and we pull in a couple of things for you which
aren't needed for everyone using django_FBO.

[12 factor]: http://12factor.net/

## Included module: pages

A really simple FBO configuration that by default looks for files
in `./pages/` and renders them using a `page.html` template.

## Included module: blog

A more complex FBO configuration that looks for files in
`./posts/YYYY/MM/DD/slug` and renders them using a `blog/post.html`
template and `blog/index.html` for _all_ the indexes.

## Bake your site

```
$ ./manage.py bake_site outdir/
```

Note that this isn't compatible with `django-bakery`, which uses a
very different way to figure out what to bake, and (at least when I
looked at it) didn't seem to support pagination.

Baking won't touch media files (generally I'd recommend you `Alias`
them for your website, or `s3sync` them directly or whatever). It
won't do anything about static files, because you can just use
`manage.py collectstatic` (and you should, because it allows you to
use `ManifestStaticFilesStorage`).

Note that only FBO views (or views where you mixin and then implement
`django_FBO.baking.Bakeable.get_paths` yourself) will be baked. You
should also be able to use FBOs with `[django-staticgen]` or
`[django-freeze]`.

It's a bit grotty, and will probably break if you try to push it very
far. It works for me, and will stick around unless I switch to
something else.

[django-staticgen]: https://github.com/mishbahr/django-staticgen
[django-freeze]: https://github.com/fabiocaccamo/django-freeze

## Underlying API

FBO provides something kind of like the ORM. You have to construct an
FBO object, at which point it acts like an ORM model:

    from django_FBO import FBO

    qs = FBO(
        path='path/to/files/',
        glob='*.md',
        metadata='.meta',
    ).objects.all()

    if qs.count() > 0:
        print(
            '\n'.join(
                [str(fbo) for fbo in qs]
            )
        )
    else:
        print("No objects found.")

## TODO

 * metadata from detached file (with auto-detection of format?)
 * tests for .none(), .exists()
 * tests for .datetimes()
 * real documentation!
 * MetadataInFileHead is somewhat ponderous
 * Options/_meta actually overridable etc

## Requirements

Django 1.10, Python 3. A file system.

You probably want python-markdown-deux, to make it easy to render
markdown sources. This is required to run the tests.

## Contact

This is very early days for this; feedback welcome via the [github
project page].

[James Aylett]

[James Aylett]: http://tartarus.org/james/
[github project page]: https://github.com/jaylett/django-filebacked-objects
