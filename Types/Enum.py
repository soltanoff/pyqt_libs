# -*- coding: utf-8 -*-


class CEnumMeta(type):
    nameMap = {}

    def getName(cls, item):
        return cls.nameMap.get(item, u'')

    def __getitem__(self, item):
        return self.getName(item)

    def __len__(self):
        return len(self.nameMap)

    def __iter__(self):
        return iter(self.nameMap.itervalues())


class CEnum(object):
    nameMap = {}

    @classmethod
    def getNameList(cls):
        if not hasattr(cls, '_nameList'):
            cls._nameList = map(cls.getName, cls.keys())
        return cls._nameList

    @classmethod
    def keys(cls):
        return sorted(cls.nameMap)

    @classmethod
    def getName(cls, key):
        return cls.nameMap.get(key, u'')

    @classmethod
    def count(cls):
        return len(cls.nameMap)

    @classmethod
    def contains(cls, key):
        return key in cls.nameMap
