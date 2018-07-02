# -*- coding: utf-8 -*-
import inspect


class SmartDict(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __len__(self):
        return len(self.__dict__)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __delitem__(self, key):
        del self.__dict__[key]

    def __iter__(self):
        return self.__dict__.__iter__()

    def __contain__(self, key):
        return key in self.__dict__

    def clear(self):
        self.__dict__.clear()

    def copy(self):
        return SmartDict(**self.__dict__)

    def get(self, key, default=None):
        return self.__dict__.get(key, default)

    def setdefault(self, key, default=None):
        return self.__dict__.setdefault(key, default)

    def update(self, d, **i):
        return self.__dict__.update(d, **i)

    def items(self):
        return self.__dict__.items()

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def iteritems(self):
        return self.__dict__.iteritems()

    def iterkeys(self):
        return self.__dict__.iterkeys()

    def itervalues(self):
        return self.__dict__.itervalues()


SMART_DICT_METHODS = ['__dict__'] + [name for name, _ in inspect.getmembers(SmartDict)]
