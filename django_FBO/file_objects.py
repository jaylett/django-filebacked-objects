from django.core.exceptions import (
    ObjectDoesNotExist,
    MultipleObjectsReturned,
)
from django.db.models.fields import TextField
import json
import yaml


class Options:
    verbose_name = None
    verbose_name_plural = None
    app_label = None
    model_name = None

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_field(self, field_name, many_to_many=None):
        # many_to_many is bc from pre-1.9, so we can
        # ignore it since we really only support 1.10
        # fully (even though it's not out yet ;-).
        return TextField(name=field_name)


class FileObjectMeta(type):

    def __new__(cls, name, bases, namespace, **kwds):
        new_class = type.__new__(cls, name, bases, namespace, **kwds)
        # FIXME we should use a Django-like `cls.Meta` pattern here
        # to allow overriding.
        # Possibly the way we pass them through into Options isn't
        # great, either.
        #
        # FIXME: these really should be generated :-)
        verbose_name = 'thing'
        verbose_name_plural = 'things'
        model_name = 'who'
        app_label = 'whatever'

        new_class._meta = Options(
            verbose_name=verbose_name,
            verbose_name_plural=verbose_name_plural,
            app_label=app_label,
            model_name=model_name,
        )
        return new_class


class FileObject(metaclass=FileObjectMeta):
    MetadataInFileHead = True
    DoesNotExist = ObjectDoesNotExist
    MultipleObjectsReturned = MultipleObjectsReturned

    def __init__(
        self,
        storage,
        metadata_location,
        name,
        slug_suffices=None,
        slug_strip_index=None,
    ):
        self.storage = storage
        self.metadata_location = metadata_location
        self.name = name
        self.path = storage.path(name=name)
        self.slug_suffices = slug_suffices
        self.slug_strip_index = slug_strip_index
        self._metadata = None

    @property
    def slug(self):
        """
        All the Django CBVs work in terms of slug, which is
        a common enough pattern that it's useful to just map
        that to name. You may want to override this if the
        slug is only part of your name (for instance see the
        blog module).

        slug_suffices is passed down from the FBO, and is a
        list of suffices that can be stripped. It's down to
        you to ensure there aren't collisions, or your FBO
        .get() won't always return the one you expect.
        """

        slug = self.name
        try:
            for suffix in self.slug_suffices:
                if slug.endswith(suffix):
                    slug = slug[:-len(suffix)]
                    break
        except TypeError:
            pass

        if self.slug_strip_index:
            # We want to transform .../index -> .../
            # so find the last component and convert
            components = slug.split('/')
            if components[-1] == 'index':
                components[-1] = ''
                slug = '/'.join(components)
            if slug == '/':
                # this is a special case, because we want
                # root indexes to work with a url pattern of:
                # r'^(?P<slug>.*)$' which will be empty at
                # the root.
                slug = ''
        return slug

    @property
    def metadata(self):
        if self._metadata is None:
            self._metadata = self._load_metadata()
        return self._metadata

    def _load_content(self):
        with self.storage.open(self.name) as _file:
            return _file.read().decode('utf-8')

    def _load_metadata(self):
        self.content = self._load_content()
        if self.metadata_location == FileObject.MetadataInFileHead:
            if self.content.startswith('{\n'):
                # JSON!
                end = self.content.find('}\n')
                if end!=-1:
                    blob = self.content[:end+2]
                    self.content = self.content[end+2:]
                    data = json.loads(blob)
                    return data
            elif self.content.startswith('---\n'):
                # YAML!
                # Magic numbers: 4 is skipping the intro ---\n,
                # 8 is skipping both intro and outro ---\n.
                end = self.content[4:].find('---\n')
                if end!=-1:
                    blob = self.content[4:end+4]
                    self.content = self.content[end+8:]
                    data = yaml.load(blob)
                    return data
            else:
                # Implicit YAML if ':' before \n\n
                colon_idx = self.content.find(':')
                sep_idx = self.content.find('\n\n')
                # If sep_idx is -1 or both are, first leg won't pass
                if colon_idx < sep_idx and colon_idx != -1:
                    # YAML!
                    blob = self.content[:sep_idx]
                    self.content = self.content[sep_idx+2:]
                    data = yaml.load(blob)
                    return data
        return {}

    def __getattr__(self, key):
        # if we are asked for content before any metadata,
        # need to load it
        if key == 'content':
            _ = self.metadata
            return self.content
        return self.metadata.get(key, None)

    def __eq__(self, other):
        if other is None or not isinstance(other, FileObject):
            return False
        return self.path == other.path

    def __str__(self):
        return self.name
