import fnmatch
from django.db.models.query_utils import Q as ORM_Q


class Q(ORM_Q):
    """Encapsulates filters as objects that can then be combined logically."""
    # Connection types
    AND = all
    OR = any
    default = AND

    # Most of the mechanics (the tree, operations, cloning) is taken
    # from Django's ORM Q object. This means we need to remove a couple
    # of methods from the public API.
    #
    # The exception we use isn't strictly accurate, but gives
    # equivalent behaviour to deleting the methods entirely (which we
    # can't do because they come via inheritance).

    def resolve_expression(self, *args, **kwargs):
        raise AttributeError(
            "'django_FBO.Q' object has no attribute 'resolve_expression'",
        )

    def refs_aggregate(self, *args, **kwargs):
        raise AttributeError(
            "'django_FBO.Q' object has no attribute 'refs_aggregate'",
        )

    # And we don't contribute to a SQL query; the tree acts as a
    # functor, applied as a filter on the incoming stream of all
    # files.
    
    def __call__(self, _file):
        def _check_one(child):
            # child is a node (one of us) or a tuple
            if isinstance(child, Q):
                return child(_file)
            else:
                _filter, _filter_val = child
                if '__' in _filter:
                    _field, _operator = _filter.split('__', 2)
                else:
                    _field, _operator = _filter, 'equals'

                _field_val = getattr(_file, _field)
                op = Operators.get(_operator)
                if op is None:
                    raise ValueError(
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
                return _op_result

        _check_results = [
            _check_one(c) for c in self.children
        ]
        if self.negated:
            return not self.connector(_check_results)
        else:
            return self.connector(_check_results)


def globerator(field, field_val, filter_val):
    return fnmatch.fnmatch(field_val, filter_val)

def equals(field, field_val, filter_val):
    return field_val == filter_val

def lte(field, field_val, filter_val):
    return field_val <= filter_val

def gte(field, field_val, filter_val):
    return field_val >= filter_val

def lt(field, field_val, filter_val):
    return field_val < filter_val

def gt(field, field_val, filter_val):
    return field_val > filter_val

def contains(field, field_val, filter_val):
    return filter_val in field_val

def startswith(field, field_val, filter_val):
    return str(field_val).startswith(filter_val)

def endswith(field, field_val, filter_val):
    return str(field_val).endswith(filter_val)

def in_operator(field, field_val, filter_val):
    return field_val in filter_val

Operators = {
    'glob': globerator,
    'equals': equals,
    'lte': lte,
    'gte': gte,
    'lt': lt,
    'gt': gt,
    'contains': contains,
    'startswith': startswith,
    'endswith': endswith,
    'in': in_operator,
}
