# Django file-backed objects

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

## Requirements

Django 1.9, Python 3. A file system.

## Contact

This is very early days for this; feedback welcome.

James Aylett
http://tartarus.org/james/
https://github.com/jaylett/django-filebacked-objects
