# -*- coding: utf-8 -*-


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
