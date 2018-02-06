# -*- coding: utf-8 -*-
import re

from PyQt4 import QtSql
from PyQt4.QtCore import QVariant

from DB.Field import CField


def undotLikeMask(val):
    if isinstance(val, CSqlExpression): return val
    if val.endswith('...'):
        val = val[:-3] + '%'
    return val.replace('...', '%').replace('%%', '%')


class CSurrogateField(CField):
    def __init__(self, name, fieldType):
        super(CField, self).__init__()
        self.database = None
        self.tableName = ''
        self.fieldName = name
        self.field = QtSql.QSqlField(name, fieldType)


class CSqlExpression(CField):
    def __init__(self, db, name, fieldType=QVariant.String):
        super(CField, self).__init__()
        self.database = db
        self.tableName = ''
        self.fieldName = name
        self._fieldType = fieldType

    def convertUtf8(self):
        return CSqlExpression(self.database, u'CONVERT({0}, CHAR CHARACTER SET utf8)'.format(self.name()))

    def __str__(self):
        return self.fieldName

    def name(self):
        return self.fieldName

    def fieldType(self):
        return self._fieldType

    def alias(self, name=''):
        return ' '.join([
            self.name(),
            self.database.aliasSymbol,
            self.database.escapeFieldName(name) if name else self.fieldName
        ])


class CJoin(object):
    def __init__(self, firstTable, secondTable, onCond, stmt='JOIN'):
        self.firstTable = firstTable
        self.secondTable = secondTable
        self.onCond = onCond
        self.stmt = stmt
        self.database = firstTable.database
        assert firstTable.database == secondTable.database

    def name(self):
        return u'%s %s %s ON %s ' % (self.firstTable.name(), self.stmt, self.secondTable.name(), self.onCond)

    def join(self, table, onCond):
        return self.database.join(self, table, onCond)

    def leftJoin(self, table, onCond):
        return self.database.leftJoin(self, table, onCond)

    def innerJoin(self, table, onCond):
        return self.database.innerJoin(self, table, onCond)

    def getMainTable(self):
        if isinstance(self.firstTable, CJoin):
            return self.firstTable.getMainTable()
        else:
            return self.firstTable

    def getAllTables(self):
        if isinstance(self.firstTable, CJoin):
            return self.firstTable.getAllTables() + [self.secondTable]
        else:
            return [self.secondTable]

    def isTableJoin(self, table):
        return table in self.getAllTables()

    def idField(self):
        return self.firstTable.idField()

    def beforeUpdate(self, record):
        return


class CSubQueryTable(object):
    u"""
    Подзапрос, подключаемый как таблица в основном запросе
    """

    def __init__(self, db, stmt, alias='T'):
        self.stmt = stmt
        self.aliasName = alias
        self.database = db

    def name(self):
        return u'(%s) AS %s' % (self.stmt, self.aliasName)

    def alias(self, aliasName):
        return CSubQueryTable(self.database, self.stmt, aliasName)

    def __getitem__(self, fieldName):
        return CSqlExpression(
            self.database,
            ((self.aliasName + '.') if self.aliasName else '') + self.database.escapeFieldName(fieldName)
        )

    def join(self, table, onCond):
        return self.database.join(self, table, onCond)

    def leftJoin(self, table, onCond):
        return self.database.leftJoin(self, table, onCond)

    def innerJoin(self, table, onCond):
        return self.database.innerJoin(self, table, onCond)


class CUnionTable(object):
    u"""
        Простейшая реализация для использования вложенных таблиц, состоящих из двух подзапросов,
        объединенных с помощью union. На момент написания требуется только для совместимости с CDatabase.join
    """

    def __init__(self, db, firstStmt, secondStmt, alias=''):
        def getColsCount(stmt):
            match = re.search('(<=SELECT ).*(?= FROM)', stmt)
            if match:
                return len(match.group(0).split(','))
            return 0

        self.firstStmt = firstStmt
        self.secondStmt = secondStmt
        self.aliasName = alias
        self.database = db
        assert getColsCount(firstStmt) == getColsCount(secondStmt)

    def __getitem__(self, fieldName):
        return CSqlExpression(
            self.database,
            ((self.aliasName + '.') if self.aliasName else '') + self.database.escapeFieldName(fieldName)
        )

    def name(self):
        return u'((%s) UNION (%s)) %s' % (self.firstStmt, self.secondStmt, self.aliasName)

    def join(self, table, onCond):
        return self.database.join(self, table, onCond)

    def leftJoin(self, table, onCond):
        return self.database.leftJoin(self, table, onCond)

    def innerJoin(self, table, onCond):
        return self.database.innerJoin(self, table, onCond)
