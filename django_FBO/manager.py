import collections
from operator import attrgetter
from django.conf import settings
from django.contrib.staticfiles import utils
from django.core.files.storage import FileSystemStorage
from django.utils import timezone

from .file_objects import FileObject
from .query import Q


OPTS = [
    'path',
    'metadata',
    'model',
    'slug_suffices',
    'slug_strip_index',
    'storage',
    '_filters',
    '_order_by',
    '_slice',
    '_fetched',
]


class FBO:
    storage = FileSystemStorage
    path = None
    metadata = None
    glob = None
    slug_suffices = None
    slug_strip_index = False
    model = FileObject

    _filters = None
    _order_by = None
    _slice = None

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

        self._storage = self.storage(
            location=self.path,
        )

    def clone(self, **kwargs):
        # subclass this if your subclass has more attributes
        # rather than just changing defaults
        for opt in OPTS:
            val = getattr(self, opt)
            if val is not None:
                if opt == '_slice':
                    if kwargs['_slice'] is None:
                        kwargs['_slice'].setdfeault(val)
                    else:
                        # merge with existing slice
                        def _combine_start(one, two):
                            if one.start is None:
                                s1 = 0
                            else:
                                s1 = one.start
                            if two.start is None:
                                s2 = 0
                            else:
                                s2 = two.start
                            return s1 + s2

                        def _combine_stop(one, two):
                            # stop is an index, not an offset
                            # so we have to take start into account
                            if one.stop is None and two.stop is None:
                                return None
                            elif two.stop is None:
                                # it's one.stop, adjusted for start
                                # change if there was one
                                if two.start is None:
                                    return one.stop
                                else:
                                    return one.stop + two.start
                            elif one.stop is None:
                                # it's two.stop, adjusted as above
                                if one.start is None:
                                    return two.stop
                                else:
                                    return two.stop + one.start
                            else:
                                # both have stop, so adjust and take
                                # the minimum
                                if two.start is None:
                                    s1 = one.stop
                                else:
                                    s1 = one.stop + two.start
                                if one.start is None:
                                    s2 = two.stop
                                else:
                                    s2 = two.stop + one.start
                                return min(s1, s2)

                        def _combine_step(one, two):
                            if one.step is None:
                                s1 = 1
                            else:
                                s1 = one.step
                            if two.step is None:
                                s2 = 1
                            else:
                                s2 = two.step
                            return s1 * s2

                        #print(val, 'merge', kwargs['_slice'])
                        kwargs['_slice'] = slice(
                            _combine_start(val, kwargs['_slice']),
                            _combine_stop(val, kwargs['_slice']),
                            _combine_step(val, kwargs['_slice']),
                        )
                        #print('now', kwargs['_slice'])
                # Lists must be duplicated, not just copied by
                # reference, otherwise if we mutate them in-place
                # in the clone it will affect the parent. This is
                # particularly bad if you reuse FBO objects, which
                # you probably will for instance in generic CBVs.
                elif isinstance(val, collections.Iterable):
                    kwargs.setdefault(opt, val[:])
                else:
                    kwargs.setdefault(opt, val)
        # cached data
        kwargs['_fetched'] = self._fetched
        return type(self)(**kwargs)

    @property
    def objects(self):
        return self

    def all(self):
        return self.clone()

    def none(self):
        return self.filter(name=False)

    def exists(self):
        return self.count() > 0

    def datetimes(self, field_name, kind, ordering, tzinfo=None):
        if settings.USE_TZ:
            if tzinfo is None:
                tzinfo = timezone.get_current_timezone()
        else:
            tzinfo = None

        datetimes = set()
        for obj in iter(self):
            dt = getattr(obj, field_name)
            reset = {
                'month': 1,
                'day': 1,
                'hour': 0,
                'minute': 0,
                'second': 0,
                'microsecond': 0,
            }
            for _kind in 'year', 'month', 'day', 'hour', 'minute', 'second':
                if _kind in reset.keys():
                    del reset[_kind]
                if _kind == kind:
                    break
            datetimes.add(dt.replace(**reset))

        if ordering == 'ASC':
            return sorted(datetimes)
        else:
            return sorted(datetimes, reverse=True)

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
        if isinstance(idx, slice):
            if (
                idx.start is not None and idx.start < 0
            ) or (
                idx.stop is not None and idx.stop < 0
            ):
                raise ValueError("Cannot use negative indexes with FBO.")
            return self.clone(_slice=idx)
        _iter = iter(self)
        try:
            for i in range(0, idx+1):
                obj = next(_iter)
        except StopIteration:
            raise IndexError(idx)
        return obj
    
    def order_by(self, *args):
        return self.clone(_order_by=args)

    def get(self, *args, **kwargs):
        filtered = self.clone().filter(*args, **kwargs)
        _count = filtered.count()
        if _count == 0:
            raise self.model.DoesNotExist
        elif _count > 1:
            raise self.model.MultipleObjectsReturned
        else:
            return filtered[0]
    
    def count(self):
        _count = 0
        for _file in iter(self):
            _count += 1
        return _count

    def _prefetch(self):
        if self._fetched is None or settings.DEBUG:
            self._fetched = []
            #print("Starting _prefetch")
            for fname in utils.get_files(self._storage):
                #print("Found %s." % fname)
                _file = self.model(
                    self._storage,
                    self.metadata,
                    fname,
                    self.slug_suffices,
                    self.slug_strip_index,
                )
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
        _filtered = []
        for _file in _objects:
            #print("Considering %s" % _file)
            if self._check_filters(_file):
                #print("  matches filters.")
                _filtered.append(_file)
        if self._slice is not None:
            #print('sliced', self._slice, [o.name for o in _filtered])
            _filtered = _filtered.__getitem__(self._slice)
            #print('now', [o.name for o in _filtered])
        return iter(_filtered)

    def _check_filters(self, _file):
        for _filter in self._filters:
            if not _filter(_file):
                return False
        return True
