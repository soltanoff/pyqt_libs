# -*- coding: utf-8 -*-
from DB.Tools import CSqlExpression
from Utils.Exceptions import CDatabaseException


class CDatabaseRoutine(object):
    u"""
     cond = [.., db.func.age(tableClient['birthDate'], tableEvent['setDate']) >= 18
    """

    FUNCTION = 1
    PROCEDURE = 2

    def __init__(self, db, name, type):
        self._db = db
        self._name = name
        self._type = type

    def __call__(self, *args, **kwargs):
        nameWithArgs = u'{0}({1})'.format(self._name, u', '.join(self._db.formatArg(it) for it in args))

        if self._type == CDatabaseRoutine.PROCEDURE:
            return self._db.query(u'CALL {0};'.format(nameWithArgs))
        else:
            return CSqlExpression(self._db, nameWithArgs)


class CDatabaseRoutineMap(object):
    def __init__(self, db, routineType):
        self._db = db
        self._routineType = routineType
        self._routineMap = None

    def __getattr__(self, item):
        if item in self._routineMap:
            return self._routineMap[item]
        if item in self.__dict__:
            return self.__dict__[item]
        raise CDatabaseException('Routine \'{0}.{1}\' doesn`t exists'.format(self._db.db.databaseName(), item))

    def _load(self):
        raise NotImplementedError
