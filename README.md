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

## Simple usage

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

But a lot of the time you want to use one of the bundled modules,
perhaps with some light overriding, to provide the views needed for
your site.

## TODO

 * metadata from detached file (with auto-detection of format?)
 * tests for metadata from detached file
 * tests for .none(), .exists()
 * tests for .datetimes()
 * tests for blog module
 * real documentation!
 * MetadataInFileHead is somewhat ponderous
 * Options/_meta actually overridable etc

## Requirements

Django 1.9, Python 3. A file system.

## Contact

This is very early days for this; feedback welcome via the [github
project page].

[James Aylett]

[James Aylett]: http://tartarus.org/james/
[github project page]: https://github.com/jaylett/django-filebacked-objects
