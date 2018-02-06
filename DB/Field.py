# -*- coding: utf-8 -*-

from PyQt4 import QtSql
from PyQt4.QtCore import QString, QVariant

from DB.Tools import CSqlExpression, undotLikeMask
from Utils.Forcing import forceString


class CField(object):
    # field - либо QtSql.QSqlField для поля таблицы базы либо просто строка для суррагатного поля
    # (в таком случае необходимо указать еще и fieldType)
    # fieldType - для случая создания виртуального/суррогатного поля
    def __init__(self, database, tableName, field, fieldType=None):
        self.database = database  # type: CDatabase
        self.tableName = tableName
        if isinstance(field, QtSql.QSqlField):
            self.fieldName = database.escapeFieldName(field.name())
            self.field = field
            self.isSurrogate = False
        elif isinstance(field, (basestring, QString)):
            self.fieldName = forceString(field)
            self.field = QtSql.QSqlField(field, fieldType if isinstance(fieldType, QVariant.Type) else QVariant.String)
            self.isSurrogate = True

    def __str__(self):
        return self.name()

    def name(self):
        prefix = (self.tableName + '.') if self.tableName else ''
        return prefix + self.fieldName

    def fieldType(self):
        return self.field.type()

    def alias(self, name=''):
        return ' '.join([
            self.name(),
            self.database.aliasSymbol,
            self.database.escapeFieldName(name) if name else self.fieldName
        ])

    def asc(self):
        return u'{0} ASC'.format(self.name())

    def desc(self):
        return u'{0} DESC'.format(self.name())

    def toTable(self, tableName):
        return CField(self.database, tableName, self.field)

    def signEx(self, sign, expr=None, modifierTemplate=None):
        u"""
        Формирует строку для операции над текущим полем вида (<текущее_поле> <оператор> <выражение>)
        с учетом переданного оператора и выражения, а так же шаблона-модификатора, в который подставлюятся текущее
        поле и выражение, если необходимо.

        :param sign: оператор (заданый строкой). Подставляется в результат всегда в неизменном виде.
        :param expr: выражение, над которым производится операция с текущим полем. Может быть None (в таком случае
                     будет опущенно).
        :param modifierTemplate: шаблон-модификатор, в который (если он задан, т.е. не None) помещаются имя текущего
                                 поля и выражение expr. Является строкой-шаблоном (см. python string formatting) для
                                 одного значения. Например, может иметь значение 'DATE(%s)', что приведет к формированию
                                 выражения вида 'DATE(<текущее_поле>) <оператор> DATE(<выражение>)'
        :return:
        """
        # составляющая выражения может быть опущена, если передано значение None
        exprPart = [expr if modifierTemplate is None else (modifierTemplate % expr)] if expr is not None else []
        return ' '.join([self.name() if modifierTemplate is None else (modifierTemplate % self.name()),
                         sign]
                        + exprPart)

    def formatValue(self, value):
        if isinstance(value, CField):
            return value.name()
        else:
            return self.database.formatValueEx(self.fieldType(), value)

    def sign(self, sign, val, modifierTemplate=None):
        return self.signEx(sign, self.formatValue(val), modifierTemplate)

    def eq(self, val):
        return self.isNull() if val is None else self.sign('=', val)

    def eqEx(self, val):
        return self.isNull() if val is None else self.signEx('=', val)

    def __eq__(self, val):
        return CSqlExpression(self.database, self.eq(self.database.forceField(val)))

    def lt(self, val):
        return self.sign('<', val)

    def __lt__(self, val):
        return CSqlExpression(self.database, self.lt(self.database.forceField(val)))

    def le(self, val):
        return self.sign('<=', val)

    def __le__(self, val):
        return CSqlExpression(self.database, self.le(self.database.forceField(val)))

    def gt(self, val):
        return self.sign('>', val)

    def __gt__(self, val):
        return CSqlExpression(self.database, self.gt(self.database.forceField(val)))

    def ge(self, val):
        return self.sign('>=', val)

    def __ge__(self, val):
        return CSqlExpression(self.database, self.ge(self.database.forceField(val)))

    def ne(self, val):
        return self.isNotNull() if val is None else self.sign('!=', val)

    def __ne__(self, val):
        return CSqlExpression(self.database, self.ne(self.database.forceField(val)))

    def isNull(self):
        return self.signEx('IS NULL', None)

    def isNotNull(self):
        return self.signEx('IS NOT NULL', None)

    def setNull(self):
        return self.signEx('=', 'NULL')

    def isZeroDate(self):
        return self.eq(self.database.valueField('0000-00-00'))

    def isNullDate(self):
        return self.database.joinOr([self.isNull(),
                                     self.isZeroDate()])

    def __not__(self):
        return CSqlExpression(self.database, u'NOT {0}'.format(self))

    def __and__(self, other):
        return CSqlExpression(self.database, u'{0} AND {1}'.format(self, other))

    def __or__(self, other):
        return CSqlExpression(self.database, u'{0} OR {1}'.format(self, other))

    def __add__(self, other):
        return CSqlExpression(self.database, u'{0} + {1}'.format(self, other))

    def __sub__(self, other):
        return CSqlExpression(self.database, u'{0} - {1}'.format(self, other))

    def __mul__(self, other):
        return CSqlExpression(self.database, u'{0} * {1}'.format(self, other))

    def __div__(self, other):
        return CSqlExpression(self.database, u'{0} / {1}'.format(self, other))

    def decoratedlist(self, itemList):
        if not itemList:
            return '()'
        else:
            decoratedList = []
            for value in itemList:
                decoratedList.append(self.database.formatValueEx(self.fieldType(), value))
            return unicode('(' + (','.join(decoratedList)) + ')')

    def inlist(self, itemList, *args):
        if not isinstance(itemList, (list, tuple, set)):
            itemList = args + (itemList,)
        return '0' if not itemList else self.signEx('IN', self.decoratedlist(itemList))

    def notInlist(self, itemList):
        if not itemList:
            return '1'  # true
        else:
            return self.signEx('NOT IN', self.decoratedlist(itemList))

    def inInnerStmt(self, stmt):
        if not stmt:
            return '0'
        else:
            return self.signEx('IN', u'(%s)' % stmt)

    def notInInnerStmt(self, stmt):
        if not stmt:
            return '0'
        else:
            return self.signEx('NOT IN', u'(%s)' % stmt)

    def eqStmt(self, stmt):
        if not stmt:
            return '0'
        else:
            return self.signEx('=', u'(%s)' % stmt)

    def like(self, val):
        return self.sign('LIKE', undotLikeMask(val))

    def notlike(self, val):
        return self.sign('NOT LIKE ', undotLikeMask(val))

    def likeBinary(self, val):
        return self.sign('LIKE BINARY', undotLikeMask(val))

    def regexp(self, val):
        return self.sign('REGEXP', val)

    def between(self, low, high):
        return u'(%s BETWEEN %s AND %s)' % (self.name(), self.formatValue(low), self.formatValue(high))

    def compareDatetime(self, otherDatetime, compareOperator, onlyDate=True):
        u"""
        Формирует строку для сравнения текущего поля с датой-временем (или только датой при onlyDate = True),
        переданной в параметрах
        """
        if otherDatetime is None:
            return self.isNull()

        return self.signEx(compareOperator, self.formatValue(otherDatetime),
                           u'DATE(%s)' if onlyDate else u'TIMESTAMP(%s)')

    def dateEq(self, val):
        return self.compareDatetime(val, u'=')

    def dateLe(self, val):
        return self.compareDatetime(val, u'<=')

    def dateLt(self, val):
        return self.compareDatetime(val, u'<')

    def dateGe(self, val):
        return self.compareDatetime(val, u'>=')

    def dateGt(self, val):
        return self.compareDatetime(val, u'>')

    def datetimeEq(self, val):
        return self.compareDatetime(val, u'=', onlyDate=False)

    def datetimeLe(self, val):
        return self.compareDatetime(val, u'<=', onlyDate=False)

    def datetimeLt(self, val):
        return self.compareDatetime(val, u'<', onlyDate=False)

    def datetimeGe(self, val):
        return self.compareDatetime(val, u'>=', onlyDate=False)

    def datetimeGt(self, val):
        return self.compareDatetime(val, u'>', onlyDate=False)

    def datetimeBetween(self, low, high):
        return 'TIMESTAMP(%s) BETWEEN TIMESTAMP(%s) AND TIMESTAMP(%s)' % (
            self.name(), self.formatValue(low), self.formatValue(high))

    def dateBetween(self, low, high):
        return u'(DATE(%s) BETWEEN %s AND %s)' % (self.name(), self.formatValue(low), self.formatValue(high))

    def monthGe(self, val):
        if val is None:
            return self.isNull()
        else:
            return 'MONTH(' + self.name() + ')>=MONTH(' + unicode(self.formatValue(val) + ')')

    def yearGe(self, val):
        if val is None:
            return self.isNull()
        else:
            return 'YEAR(' + self.name() + ')>=YEAR(' + unicode(self.formatValue(val) + ')')

    def yearEq(self, val):
        if val is None:
            return self.isNull()
        else:
            return 'YEAR(' + self.name() + ')=YEAR(' + unicode(self.formatValue(val) + ')')
