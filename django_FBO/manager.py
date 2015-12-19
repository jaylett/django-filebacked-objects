import collections
import json
from operator import attrgetter
import yaml
from django.contrib.staticfiles import utils
from django.core.files.storage import FileSystemStorage

from .query import Q


class DoesNotExist(Exception):
    pass


class MultipleObjectsReturned(Exception):
    pass


class FileObject:
    DoesNotExist = DoesNotExist
    class _meta:
        verbose_name = 'FileObjects'

    def __init__(self, storage, metadata_location, name):
        self.storage = storage
        self.metadata_location = metadata_location
        self.name = name
        self.path = storage.path(name=name)
        self._metadata = None

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
        if self.metadata_location == FBO.MetadataInFileHead:
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
        return self.metadata[key]

    def __str__(self):
        return self.name


OPTS = [
    'path',
    'metadata',
    'model',
    'storage',
    '_filters',
    '_order_by',
]


class FBO:
    MetadataInFileHead = True
    DoesNotExist = DoesNotExist
    MultipleObjectsReturned = MultipleObjectsReturned

    storage = FileSystemStorage
    path = None
    metadata = None
    glob = None
    model = FileObject

    _filters = None
    _order_by = None

    def __init__(self, **kwargs):
        self._fetched = None
        if self._filters is None:
            self._filters = []
        else:
            self._filters = self._filters[:]
        if self._order_by is None:
            self._order_by = []
        else:
            self._order_by = self._order_by[:]

        for opt in OPTS:
            if opt in kwargs:
                if kwargs[opt] is not None:
                    setattr(self, opt, kwargs[opt])
        if 'glob' in kwargs and kwargs['glob'] is not None:
            self._add_q(
                Q(name__glob=kwargs['glob']),
            )
        elif self.glob is not None:
            self._add_q(
                Q(name__glob=self.glob),
            )
        
        if self.path is None:
            raise TypeError("You must set a path for FBOs.")

        #if isinstance(self.storage, str):
        self._storage = self.storage(
            location=self.path,
        )

    def clone(self, **kwargs):
        # subclass this if your subclass has more attributes
        # rather than just changing defaults
        for opt in OPTS:
            val = getattr(self, opt)
            if val is not None:
                # Lists must be duplicated, not just copied by
                # reference, otherwise if we mutate them in-place
                # in the clone it will affect the parent. This is
                # particularly bad if you reuse FBO objects, which
                # you probably will for instance in generic CBVs.
                if isinstance(val, collections.Iterable):
                    val = val[:]
                kwargs.setdefault(opt, val)
        # cached data
        kwargs['_fetched'] = self._fetched
        return type(self)(**kwargs)

    @property
    def objects(self):
        return self

    def all(self):
        return self.clone()

    def _add_q(self, q_object):
        self._filters.append(q_object)
    
    def filter(self, *args, **kwargs):
        clone = self.clone()
        clone._add_q(Q(*args, **kwargs))
        return clone
    
    def exclude(self, *args, **kwargs):
        clone = self.clone()
        clone._add_q(~Q(*args, **kwargs))
        return clone
    
    def __len__(self):
        return self.count()
    
    def __getitem__(self, idx):
        _iter = iter(self)
        for i in range(0, idx+1):
            obj = next(_iter)
        return obj
    
    def order_by(self, *args):
        return self.clone(_order_by=args)

    def get(self, *args, **kwargs):
        filtered = self.clone().filter(*args, **kwargs)
        _count = filtered.count()
        if _count == 0:
            raise self.DoesNotExist
        elif _count > 1:
            raise self.MultipleObjectsReturned
        else:
            return filtered[0]
    
    def count(self):
        _count = 0
        for _file in iter(self):
            _count += 1
        return _count

    def _prefetch(self):
        if self._fetched is None:
            self._fetched = []
            #print("Starting _prefetch")
            for fname in utils.get_files(self._storage):
                #print("Found %s." % fname)
                _file = self.model(self._storage, self.metadata, fname)
                if self._check_filters(_file):
                    #print("  matches filters")
                    self._fetched.append(_file)
    
    def __iter__(self):
        self._prefetch()
        # apply order_by here because we may have prefetched on a
        # previous copy of this
        _objects = self._fetched
        for _order_by in self._order_by:
            if _order_by[0] == '-':
                _rev = True
                _attr = _order_by[1:]
            else:
                _rev = False
                _attr = _order_by
            _objects = sorted(_objects, key=attrgetter(_attr), reverse=_rev)

        # check filters here as well as so we can copy
        # our cached fetched data around, to avoid hitting
        # the filesystem so much
        #print("__iter__()")
        for _file in _objects:
            #print("Considering %s" % _file)
            if self._check_filters(_file):
                #print("  matches filters.")
                yield _file

    def _check_filters(self, _file):
        for _filter in self._filters:
            if not _filter(_file):
                return False
        return True
