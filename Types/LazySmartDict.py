# -*- coding: utf-8 -*-
from Types import SmartDict
from Types.SmartDict import SMART_DICT_METHODS


class LazySmartDict(SmartDict, object):
    def __getattribute__(self, name):
        # NOTE: we need to exclude special methods,
        # otherwise they will be called (twice)
        if name in SMART_DICT_METHODS:
            return object.__getattribute__(self, name)
        v = object.__getattribute__(self, name)()
        # aint no method will be called for the second time
        if not name.startswith('__'):
            setattr(self, name, lambda: v)
        return v

    def __getitem__(self, key):
        # values are assumed to be lazy, so they are
        # called when upon dict-style access
        return self.__dict__[key]()

    def values(self):
        return [v() for v in self.__dict__.values()]

    def items(self):
        return [(k, v()) for k, v in self.__dict__.items()]

    def iteritems(self):
        for k, v in self.__dict__.iteritems():
            yield k, v()

    def itervalues(self):
        for v in self.__dict__.itervalues():
            yield v()

    def get(self, key, default=None):
        return self.__dict__.get(key, lambda: default)()

    def setdefault(self, key, default=None):
        return self.__dict__.setdefault(key, lambda: default)
