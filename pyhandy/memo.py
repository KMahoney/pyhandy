try:
    from django.core.cache import cache
except ImportError:
    # Obviously without django cache_memo will fail
    pass

import hashlib


def _hashargs(args):
    '''
    Add each arguments's python hash to a md5 hash.
    Reduces collision chance over simply hash(args), which is
    only a 32bit value. Collisions in a hash table are ok,
    collisions in a cache_memo lookup are not ok!
    '''

    md5 = hashlib.md5()

    for arg in args:
        # if argument is a string, add it to the hash verbatium
        if type(arg) is str:
            md5.update(arg)
        else:
            md5.update(str(hash(arg)))

    return md5.hexdigest()


def cache_memo(fn, timeout=0):
    '''
    Memoise a function using the django cache. Beware collisions!
    Do not use for sensitive data. Do not use unless you are
    sure this is what you want, the other memo functions are safer.
    There is a small but not insignificant chance this
    can make a function return the answer for the wrong arguments.
    Caveat emptor.
    '''

    def _wrapped(*args):
        # cache key is function name followed by arg hash
        key = "memo_%s_%s" % (fn.__name__, _hashargs(args))
        val = cache.get(key)
        if val is not None:
            return val
        val = fn(*args)
        cache.set(key, val, timeout)
        return val
    return _wrapped


class memo(object):
    '''Memoise a function.'''

    def __init__(self, fn):
        self.values = {}
        self.fn = fn

    def __call__(self, *args):
        if args in self.values:
            return self.values[args]
        value = self.fn(*args)
        self.values[args] = value
        return value


def memo_method(method):
    '''Memoise a method (per instance).'''
    key = "_memo_%s" % method.__name__

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

    def _wrapped(self):
        value = getattr(self, key, None)
        if value is not None:
            return value
        value = method(self)
        setattr(self, key, value)
        return value
    return property(_wrapped)
