import fnmatch
import json
from operator import attrgetter
import yaml
from django.contrib.staticfiles import utils
from django.core.files.storage import FileSystemStorage


class DoesNotExist(Exception):
    pass


class FileObject:

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


OPTS = [ 'path', 'metadata', '_filters', '_excludes', '_order_by', 'storage' ]


class FBO:
    MetadataInFileHead = True
    DoesNotExist = DoesNotExist

    storage = FileSystemStorage
    path = None
    metadata = None

    _filters = None
    _excludes = None
    _order_by = None

    def __init__(self, **kwargs):
        self._fetched = None
        if self._filters is None:
            self._filters = []
        if self._excludes is None:
            self._excludes = []
        if self._order_by is None:
            self._order_by = []

        for opt in OPTS:
            if opt in kwargs:
                if kwargs[opt] is not None:
                    setattr(self, opt, kwargs[opt])
        if 'glob' in kwargs and kwargs['glob'] is not None:
            self._filters.append(
                ('name__glob', kwargs['glob']),
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
                kwargs.setdefault(opt, val)
        # cached data
        kwargs['_fetched'] = self._fetched
        return type(self)(**kwargs)

    @property
    def objects(self):
        return self

    def all(self):
        return self.clone()

    def filter(self, **kwargs):
        _filters = []
        for k, v in kwargs.items():
            _filters.append(
                (k, v),
            )
        return self.clone(
            _filters=self._filters + _filters,
        )
    
    def exclude(self, **kwargs):
        _excludes = []
        for k, v in kwargs.items():
            _excludes.append(
                (k, v),
            )
        return self.clone(
            _excludes=self._excludes + _excludes,
        )
    
    def __len__(self):
        return self.count()
    
    def __getitem__(self, idx):
        _iter = iter(self)
        for i in range(0, idx+1):
            obj = next(_iter)
        return obj
    
    def order_by(self, *args):
        return self.clone(_order_by=args)

    def get(self, **kwargs):
        filtered = self.clone().filter(**kwargs)
        _count = filtered.count()
        if _count == 0:
            raise DoesNotExist
        elif _count > 1:
            raise Exception("Multiple objects")
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
                _file = FileObject(self._storage, self.metadata, fname)
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
        def _check(filters, invert):
            for _filter, _filter_val in filters:
                if '__' in _filter:
                    _field, _operator = _filter.split('__', 2)
                else:
                    _field, _operator = _filter, 'equals'

                _field_val = getattr(_file, _field)
                op = Operators.get(_operator)
                if op is None:
                    raise Exception(
                        "No such operator '%s' in filter '%s'" % (
                            _operator,
                            _filter,
                        )
                    )

                _op_result = op(_field, _field_val, _filter_val)
                #print(
                #    "Filter %s.%s__%s=%s: %s -> %s" % (
                #        _file,
                #        _field,
                #        _operator,
                #        _filter_val,
                #        _field_val,
                #        _op_result,
                #    )
                #)
                if not invert and not _op_result:
                    return False
                if invert and _op_result:
                    return False
            return True

        if not _check(self._filters, False):
            return False
        if not _check(self._excludes, True):
            return False
        return True


def globerator(field, field_val, filter_val):
    return fnmatch.fnmatch(field_val, filter_val)

def equals(field, field_val, filter_val):
    return field_val == filter_val
    
Operators = {
    'glob': globerator,
    'equals': equals,
}
