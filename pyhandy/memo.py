try:
    from django.core.cache import cache
except ImportError:
    # Obviously without django cache_memo will fail
    pass

import hashlib
from functools import wraps


def _hashargs(args):
    '''Add each arguments's string representation to a md5 hash.'''
    md5 = hashlib.md5()

    for arg in args:
        md5.update(str(arg))

    return md5.hexdigest()


def _default_key(*args):
    return _hashargs(tuple(args))


def cache_memo(timeout=0, cache_key=_default_key):
    '''Memoise a function using the django cache. Beware collisions!'''

    def _outer(fn):

        @wraps(fn)
        def _inner(*args):
            # cache key is function name followed by arg hash
            key = "memo_%s_%s" % (fn.__name__, cache_key(*args))
            val = cache.get(key)
            if val is not None:
                return val
            val = fn(*args)
            cache.set(key, val, timeout)
            return val

        return _inner

    return _outer


class memo(object):
    '''Memoise a function.'''

    def __init__(self, fn):
        self.values = {}
        self.fn = fn
        self.__doc__ = fn.__doc__

    def __call__(self, *args):
        if args in self.values:
            return self.values[args]
        value = self.fn(*args)
        self.values[args] = value
        return value


def memo_method(method):
    '''Memoise a method (per instance).'''
    key = "_memo_%s" % method.__name__

    @wraps(method)
    def _wrapped(self, *args):
        values = getattr(self, key, None)
        if values is None:
            values = {}
            setattr(self, key, values)
        if args in values:
            return values[args]
        value = method(self, *args)
        values[args] = value
        return value

    return _wrapped


def memo_property(method):
    '''Memoise an object property.'''
    key = "_memo_property_%s" % method.__name__

    @wraps(method)
    def _wrapped(self):
        value = getattr(self, key, None)
        if value is not None:
            return value
        value = method(self)
        setattr(self, key, value)
        return value

    return property(_wrapped)
