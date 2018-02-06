# -*- coding: utf-8 -*-
import copy

from PyQt4 import QtSql

from DB.Field import CField
from DB.Tools import CSqlExpression
from Utils.Exceptions import CDatabaseException


class CTable(object):
    def __init__(self, tableName, database, alias=''):
        self.fields = []
        self.fieldsDict = {}
        self.database = database
        self.tableName = unicode(tableName)
        self.aliasName = alias
        self.isQueryTable = True if self.tableName.strip().lower().startswith('select') else False
        # Если имя таблицы начинается с 'SELECT ', то предположить,
        # что это таблица-подзапрос, а она должна иметь псевдоним
        if self.isQueryTable and not alias:
            self.aliasName = 'someSubQueryTable'
            # На момент написания глубокомысленного кода (обработки условия) ниже
            # опытным путем было установленно, что QSqlDatabase.record(tableStatement) пытается выполнить запрос
            # <tableStatement>LIMIT 0,1
            # если <tableStatement> - это запрос на выборку, а не имя таблицы, как ожидает функция согласно
            # документации. И, следовательно, возникает проблема отсутствия пробела перед добавляемым "LIMIT"
            if not self.tableName.endswith(' '):
                self.tableName += u' '
        self._idField = None
        self._idFieldName = None
        record = database.record(self.tableName)
        # TODO: случай, когда таблица задана джойнами и есть поля с одинаковым именем (ибо они без префикса будут)
        for i in xrange(record.count()):
            qtfield = record.field(i)
            field = CField(self.database, self.tableName, qtfield)
            self.fields.append(field)
            fieldName = str(qtfield.name())
            if not self.fieldsDict.has_key(fieldName):
                self.fieldsDict[fieldName] = field

    def name(self, alias=''):
        alias = alias or self.aliasName
        if alias:
            return ' '.join([
                self.tableName if not self.isQueryTable else '(%s)' % self.tableName,
                self.database.aliasSymbol,
                unicode(alias)
            ])
        else:
            return self.tableName

    def alias(self, name):
        # создаем копию объекта (словари/списки копируются как ссылки,
        # т.е. остаются общими, иначе надо использовать deepcopy())
        newTable = copy.copy(self)
        newTable.aliasName = unicode(name)
        return newTable

    def setIdFieldName(self, name):
        self._idField = self.__getitem__(name)
        self._idFieldName = name

    def idField(self):
        if not self._idField:
            self.setIdFieldName('id')
        return self._idField

    def idFieldName(self):
        if not self._idField:
            if self.hasField('id'):
                self.setIdFieldName('id')
            else:
                self.setIdFieldName(self.fields[0].fieldName.replace('`', ''))
        return self._idFieldName

    def __getitem__(self, key):
        key = str(key)
        result = self.fieldsDict.get(key, None)
        if result:
            return result if not self.aliasName else result.toTable(self.aliasName)
        elif key == '*':
            return CSqlExpression(self.database, '{0}.*'.format(self.tableName))
        else:
            raise CDatabaseException(u'В таблице %s не найдено поле "%s"' % (self.tableName, key))

    def hasField(self, fieldName):
        return self.fieldsDict.has_key(fieldName)

    def newRecord(self, fields=None, otherRecord=None):
        record = QtSql.QSqlRecord()
        for field in self.fields:
            if fields and field.field.name() not in fields:
                continue
            record.append(QtSql.QSqlField(field.field))
            if otherRecord and otherRecord.contains(field.field.name()) and field != self._idField:
                record.setValue(field.field.name(), otherRecord.value(field.field.name()))
        return record

    def beforeInsert(self, record):
        return

    def beforeUpdate(self, record):
        return

    def beforeDelete(self, record):
        return

    def join(self, table, onCond):
        return self.database.join(self, table, onCond)

    def leftJoin(self, table, onCond):
        return self.database.leftJoin(self, table, onCond)

    def innerJoin(self, table, onCond):
        return self.database.innerJoin(self, table, onCond)
