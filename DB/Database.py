# -*- coding: utf-8 -*-
import traceback

import itertools
from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import QObject, QVariant, pyqtSignal, Qt
from PyQt4.QtGui import QMessageBox

from DB.Field import CField
from DB.Table import CTable
from DB.Tools import decorateString, CSqlExpression, CSubQueryTable, CJoin, CUnionTable
from Utils.Debug import printQueryTime
from Utils.Exceptions import CDatabaseException, CException
from Utils.Forcing import toVariant, forceString
from Utils.Utils import compareCallStack


class CDatabase(QObject):
    aliasSymbol = 'AS'

    errUndefinedDriver = u'Драйвер базы данных "%s" не зарегистрирован'
    errCannotConnectToDatabase = u'Невозможно подключиться к базе данных "%s"'
    errCannotOpenDatabase = u'Невозможно открыть базу данных "%s"'
    errDatabaseIsNotOpen = u'База данных не открыта'

    errCommitError = u'Ошибка закрытия тразнакции'
    errRollbackError = u'Ошибка отмены тразнакции'
    errTableNotFound = u'Таблица "%s" не найдена'
    errFieldNotFound = u'В таблице %s не найдено поле "%s"'
    errQueryError = u'Ошибка выполнения запроса\n%s'
    errNoIdField = u'В таблице %s не определен первичный ключ'
    errConnectionLost = u'Потеряна связь с сервером.'
    errRestoreConnectionFailed = u'Не удалось восстановить подключение к базе данных.'

    errTransactionError = u'Ошибка открытия тразнакции'
    errNestedCommitTransactionError = u'Ошибка подтверждения вложенной транзакции'
    errNestedRollbackTransactionError = u'Ошибка отмены вложенной транзакции'
    errNestedTransactionCall = u'Попытка открытия вложенной транзакции'
    errUnexpectedTransactionCompletion = u'Неожиданное завершение транзакции'
    errInheritanceTransaction = u'Ошибка нессответствия наследования транзакций и вызвавших их функций'
    errNoRootTransaction = u'Нарушение требования корневой транзакции (уже открыто %s транзакций)'
    errPreviousTransactionCallStack = u'>>>>>> Стек вызовов предыдущей транзакции:\n%s <<<<<<'

    returnedDeadlockErrorText = u'<To be specified for a particular database.>'

    # добавлено для formatQVariant
    convMethod = {
        QVariant.Int: lambda val: unicode(val.toInt()[0]),
        QVariant.UInt: lambda val: unicode(val.toUInt()[0]),
        QVariant.LongLong: lambda val: unicode(val.toLongLong()[0]),
        QVariant.ULongLong: lambda val: unicode(val.toULongLong()[0]),
        QVariant.Double: lambda val: unicode(val.toDouble()[0]),
        QVariant.Bool: lambda val: u'1' if val.toBool() else u'0',
        QVariant.Char: lambda val: decorateString(val.toString()),
        QVariant.String: lambda val: decorateString(val.toString()),
        QVariant.Date: lambda val: decorateString(val.toDate().toString(Qt.ISODate)),
        QVariant.Time: lambda val: decorateString(val.toTime().toString(Qt.ISODate)),
        QVariant.DateTime: lambda val: decorateString(val.toDateTime().toString(Qt.ISODate)),
        QVariant.ByteArray: lambda val: 'x\'' + str(val.toByteArray().toHex()) + '\'',
        QVariant.Color: lambda val: unicode(QtGui.QColor(val).name()),
    }

    connected = pyqtSignal()
    disconnected = pyqtSignal()

    def __init__(self, afterConnectFunc=None):
        QObject.__init__(self)
        self.deadLockRepeat = 3
        self.db = None
        self.tables = {}
        # restoreConnectState:
        # 0 - соединение не было утеряно,
        # 1 - соединение утеряно, пытаться переподключиться
        # 2 - соединение утеряно, переподключение не требуется.
        self.restoreConnectState = 0

        self._transactionCallStackByLevel = []
        self._openTransactionsCount = 0

        self._func = None
        self._proc = None

    def getConnectionId(self):
        return None

    def makeField(self, fromString):
        u""" Raw SQL -> CField-like object
        :rtype: CSqlExpression
        """
        return CSqlExpression(self, fromString)

    def valueField(self, value):
        u""" Py-value (QVariant-convertible) -> CField-like object """
        return self.makeField(self.formatArg(value))

    def forceField(self, value):
        u""" CField instance, raw SQL or Py-value -> CField instance
        :rtype: CField
        """
        if isinstance(value, CField):
            return value
        elif isinstance(value, (str, unicode)):
            return self.makeField(value)
        return self.valueField(value)

    def subQueryTable(self, stmt, alias):
        u""" SELECT stmt -> CTable-like object """
        return CSubQueryTable(self, stmt, alias)

    def escapeIdentifier(self, name, identifierType):
        return unicode(self.driver().escapeIdentifier(name, identifierType))

    def escapeFieldName(self, name):
        return unicode(self.driver().escapeIdentifier(name, QtSql.QSqlDriver.FieldName))

    def escapeTableName(self, name):
        return unicode(self.driver().escapeIdentifier(name, QtSql.QSqlDriver.TableName))

    escapeSchemaName = escapeTableName

    @staticmethod
    def dummyRecord():
        return QtSql.QSqlRecord()

    u"""
    Добавлено из-за обнаруженной ошибки в qt4 v.4.5.3:
    - значения полей типа DOUBLE считываются не как QVariant.Double а как QVariant.String
      поведение в windows не исследовано, а в linux строка записывается с десятичной запятой.
      при этом документированный способ исправить положение
      query.setNumericalPrecisionPolicy(QSql.LowPrecisionDouble)
      не срабатывает из-за того, что driver.hasFeature(QSqlDriver.LowPrecisionNumbers)
      возвращает false
    - при записи значения в запрос формируется значение с запятой, что неприемлемо для MySql сервера
      поэтому принято решение написать свой вариант formatValue
    """

    @classmethod
    def formatQVariant(cls, fieldType, val):
        if val.isNull():
            return 'NULL'
        return cls.convMethod[fieldType](val)

    @classmethod
    def formatValue(cls, field):
        return cls.formatQVariant(field.type(), field.value())

    @classmethod
    def formatValueEx(cls, fieldType, value):
        if isinstance(value, QVariant):
            return cls.formatQVariant(fieldType, value)
        else:
            return cls.formatQVariant(fieldType, toVariant(value))

    @classmethod
    def formatArg(cls, value):
        if isinstance(value, CField):
            return value.name()
        else:
            qValue = toVariant(value)
            return cls.formatValueEx(qValue.type(), qValue)

    def createConnection(self, driverName, connectionName, serverName, serverPort, databaseName, userName, password):
        if connectionName:
            if not QtSql.QSqlDatabase.contains(connectionName):
                db = QtSql.QSqlDatabase.addDatabase(driverName, connectionName)
            else:
                db = QtSql.QSqlDatabase.database(connectionName)
        else:
            db = QtSql.QSqlDatabase.addDatabase(driverName)
        if not db.isValid():
            raise CDatabaseException(CDatabase.errCannotConnectToDatabase % driverName, db.lastError())
        db.setHostName(serverName)
        if serverPort:
            db.setPort(serverPort)
        db.setDatabaseName(databaseName)
        db.setUserName(userName)
        db.setPassword(password)
        self.db = db

    def isConnectionLostError(self, sqlError):
        driverText = forceString(sqlError.driverText()).lower()
        if 'lost connection' in driverText:
            return True
        if 'server has gone away' in driverText:
            return True
        return False

    def connectUp(self):
        if not self.db.open():
            raise CDatabaseException(CDatabase.errCannotOpenDatabase % self.db.databaseName(), self.db.lastError())
        self.restoreConnectState = 0
        self._transactionCallStackByLevel = []
        self._openTransactionsCount = 0
        self.connected.emit()

    def reconnect(self):
        if not (self.db and self.db.isValid):
            return False
        if self.db.isOpen():
            self.db.close()
        if not self.db.open():
            self.connectDown()
            return False
        self.connected.emit()
        return True

    def connectDown(self):
        self.db.close()
        self._transactionCallStackByLevel = []
        self._openTransactionsCount = 0
        self.disconnected.emit()

    def close(self):
        if self.db:
            connectionName = self.db.connectionName()
            self.connectDown()
            QtSql.QSqlDatabase.removeDatabase(connectionName)
            self.driver = None
            self.db = None
        self.tables = {}

    def restoreConnection(self, quiet=False):
        self.restoreConnectState = 1
        isReconnect = quiet or QMessageBox.critical(
            QtGui.qApp.activeWindow(),
            u'Внимание',
            CDatabase.errConnectionLost + u'\nПопробовать восстановить подключение?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        ) == QMessageBox.Yes
        if isReconnect:
            if self.reconnect():
                self.restoreConnectState = 0
                return True
            else:
                QMessageBox.critical(
                    QtGui.qApp.activeWindow(),
                    u'Критическая ошибка',
                    self.errRestoreConnectionFailed,
                    QMessageBox.Ok
                )
        self.restoreConnectState = 2
        return False

    def getTestConnectionStmt(self):
        return u'select \'test connection query\';'

    def checkdb(self):
        if not self.db or not self.db.isValid() or not self.db.isOpen():
            raise CDatabaseException(CDatabase.errDatabaseIsNotOpen)

    def isValid(self):
        return self.db is not None and self.db.isValid() and self.db.isOpen()

    def checkConnect(self, quietRestoreConnection=False):
        self.checkdb()

        testQuery = QtSql.QSqlQuery(self.db)
        stmt = self.getTestConnectionStmt()
        if testQuery.exec_(stmt):
            return
        else:
            sqlError = testQuery.lastError()

        if self.isConnectionLostError(sqlError):
            if self.restoreConnection(quietRestoreConnection):
                return
            else:
                self.connectDown()

        raise self.onError(stmt, sqlError)

    def driver(self):
        return self.db.driver()

    def forceTable(self, table, idFieldName='id'):
        if isinstance(table, (CTable, CJoin, CUnionTable, CSubQueryTable)):
            return table
        elif isinstance(table, basestring):
            return self.table(table, idFieldName=idFieldName)
        else:
            raise AssertionError, u'Недопустимый тип'

    def mainTable(self, tableExpr, idFieldName='id'):
        if isinstance(tableExpr, (CTable, CJoin)):
            return tableExpr
        elif isinstance(tableExpr, basestring):
            name = tableExpr.split(None, 1)[0] if ' ' in tableExpr else tableExpr
            return self.table(name, idFieldName)
        else:
            raise AssertionError, u'Недопустимый тип'

    def getTableName(self, table):
        # soltanoff: проверка на строковость необходима, чтобы избежать рекурсию:
        # forceTable -> CTable.__init__() -> CTable.record() -> selectStmt() -> getTableName()
        # да и нет смысла создавать класс таблицы, для того чтобы получить ее имя из строки
        if isinstance(table, basestring):
            if table.strip().lower().startswith('select '):
                return ' '.join([u'(%s)' % table, self.aliasSymbol, u'someQueryTable'])
            return table
        return self.forceTable(table).name()

    def formatDate(self, val):
        return '\'' + str(val.toString(Qt.ISODate)) + '\''

    def formatTime(self, val):
        return '\'' + str(val.toString(Qt.ISODate)) + '\''

    def coalesce(self, *args):
        return CSqlExpression(self, u'COALESCE({0})'.format(u', '.join(map(self.formatArg, args))))

    def ifnull(self, exp1, exp2):
        return CSqlExpression(self, u'IFNULL({0}, {1})'.format(self.forceField(exp1), self.forceField(exp2)))

    @classmethod
    def joinAnd(cls, itemList):
        return (('((' if len(itemList) > 1 else '(') +
                u') AND ('.join(u'%s' % item for item in itemList) +
                ('))' if len(itemList) > 1 else ')')) if itemList else ''

    @classmethod
    def joinOr(cls, itemList):
        return (('((' if len(itemList) > 1 else '(') +
                u') OR ('.join(u'%s' % item for item in itemList) +
                ('))' if len(itemList) > 1 else ')')) if itemList else ''

    def not_(self, expr):
        return u'NOT ({0})'.format(expr)

    def if_(self, cond, thenPart, elsePart):
        return CSqlExpression(self, u'IF({0}, {1}, {2})'.format(cond,
                                                                self.forceField(thenPart),
                                                                self.forceField(elsePart)), QVariant.Bool)

    def case(self, field, caseDict, elseValue=None):
        parts = [
            u'WHEN {0} THEN {1}'.format(self.forceField(cond), self.forceField(value))
            for cond, value in caseDict.iteritems()
        ]
        if elseValue:
            parts.append(u'ELSE {0}'.format(self.forceField(elseValue)))
        return CSqlExpression(self, u'CASE {0} {1} END'.format(self.forceField(field), u' '.join(parts)))

    def concat(self, *args):
        return CSqlExpression(self, u'CONCAT({0})'.format(u', '.join(map(self.formatArg, args))))

    def concat_ws(self, sep, *args):
        return CSqlExpression(
            self, u'CONCAT_WS({0}, {1})'.format(self.formatArg(sep), u', '.join(map(self.formatArg, args))))

    def group_concat(self, item, distinct=False):
        return CSqlExpression(self, u'GROUP_CONCAT({0}{1})'.format(u'DISTINCT ' if distinct else u'', item))

    def count(self, item, distinct=False):
        return CSqlExpression(
            self, u'COUNT({0}{1})'.format(u'DISTINCT ' if distinct else u'', item if item else '*'), QVariant.Int)

    def countIf(self, cond, item, distinct=False):
        return self.count(self.if_(cond, item, 'NULL'), distinct)

    def datediff(self, dateTo, dateFrom):
        return CSqlExpression(self, u'DATEDIFF({0}, {1})'.format(dateTo, dateFrom), QVariant.Int)

    def addDate(self, date, count, type='DAY'):
        return CSqlExpression(self, u'ADDDATE({0}, INTERVAL {1} {2})'.format(date, count, type), QVariant.Date)

    def subDate(self, date, count, type='DAY'):
        return CSqlExpression(self, u'SUBDATE({0}, INTERVAL {1} {2})'.format(date, count, type), QVariant.Date)

    def date(self, date):
        return CSqlExpression(self, u'DATE({0})'.format(self.forceField(date)))

    def dateYear(self, date):
        return CSqlExpression(self, u'YEAR({0})'.format(date), QVariant.Int)

    def dateQuarter(self, date):
        return CSqlExpression(self, u'QUARTER({0})'.format(date), QVariant.Int)

    def dateMonth(self, date):
        return CSqlExpression(self, u'MONTH({0})'.format(date), QVariant.Int)

    def dateDay(self, date):
        return CSqlExpression(self, u'DAY({0})'.format(date), QVariant.Int)

    def isZeroDate(self, date):
        return self.forceField(date).eq(self.valueField('0000-00-00'))

    def isNullDate(self, date):
        return self.joinOr([self.forceField(date).isNull(),
                            self.isZeroDate(date)])

    def sum(self, item):
        return CSqlExpression(
            self, u'SUM({0})'.format(item), item.fieldType() if isinstance(item, CField) else toVariant(item).type())

    def sumIf(self, cond, item):
        return self.sum(self.if_(cond, item, 0))

    def max(self, item):
        return CSqlExpression(self, u'MAX({0})'.format(item), QVariant.Int)

    def min(self, item):
        return CSqlExpression(self, u'MIN({0})'.format(item), QVariant.Int)

    def least(self, *args):
        return CSqlExpression(self, u'LEAST({0})'.format(u', '.join(map(self.formatArg, args))))

    def greatest(self, *args):
        return CSqlExpression(self, u'GREATEST({0})'.format(u', '.join(map(self.formatArg, args))))

    def left(self, str, len):
        return CSqlExpression(self, u'LEFT({0}, {1})'.format(str, len), QVariant.String)

    def right(self, str, len):
        return CSqlExpression(self, u'RIGHT({0}, {1})'.format(str, len), QVariant.String)

    def curdate(self):
        return CSqlExpression(self, u'CURDATE()', QVariant.Date)

    def now(self):
        return CSqlExpression(self, u'NOW()', QVariant.DateTime)

    def joinOp(self, op, *args):
        return CSqlExpression(self, u'({0})'.format(op.join(map(self.formatArg, args))), QVariant.Int)

    def bitAnd(self, *args):
        return self.joinOp(u'&', *args)

    def bitOr(self, *args):
        return self.joinOp(u'|', *args)

    def bitXor(self, *args):
        return self.joinOp(u'^', *args)

    @classmethod
    def prepareFieldList(cls, fields):
        if isinstance(fields, (list, tuple)):
            return ', '.join([field.name() if isinstance(field, CField) else field for field in fields])
        return fields.name() if isinstance(fields, CField) else fields

    @staticmethod
    def CONCAT_WS(fields, alias='', separator=' '):
        result = 'CONCAT_WS('
        result += ('\'' + separator + '\'')
        result += ', '
        if isinstance(fields, (list, tuple)):
            for field in fields:
                result += field.name() if isinstance(field, CField) else field
                result += ', '
        else:
            result += fields.name() if isinstance(fields, CField) else fields
            result += ', '
        result = result[:len(result) - 2]
        result += ')'
        if alias: result += (' AS ' + '`' + alias + '`')

        return result

    @classmethod
    def dateTimeIntersection(cls, fieldBegDateTime, fieldEndDateTime, begDateTime, endDateTime):
        if fieldBegDateTime is not None and fieldEndDateTime is not None and begDateTime is not None and endDateTime is not None:
            return cls.joinAnd([
                cls.joinOr([fieldBegDateTime.datetimeGe(begDateTime), fieldEndDateTime.datetimeGe(begDateTime),
                            fieldEndDateTime.isNull()]),
                # FIXME: fieldBegDateTime.isNull() у нас такого быть не может, но логически правильно. Возможно, в целях оптимизации, можно и вырезать
                cls.joinOr([fieldBegDateTime.datetimeLe(endDateTime), fieldEndDateTime.datetimeLe(endDateTime),
                            fieldBegDateTime.isNull()])
            ])
        else:
            return ''

    @classmethod
    def prepareWhere(cls, cond):
        if isinstance(cond, (list, tuple)):
            cond = cls.joinAnd(cond)
        return u' WHERE %s' % cond if cond else u''

    @classmethod
    def prepareOrder(cls, orderFields):
        if isinstance(orderFields, (list, tuple)):
            orderFields = ', '.join(
                [orderField.name() if isinstance(orderField, CField) else orderField for orderField in orderFields])
        if orderFields:
            return ' ORDER BY ' + (orderFields.name() if isinstance(orderFields, CField) else orderFields)
        else:
            return ''

    @classmethod
    def prepareGroup(cls, groupFields):
        if isinstance(groupFields, (list, tuple)):
            groupFields = ', '.join(
                [groupField.name() if isinstance(groupField, CField) else groupField for groupField in groupFields])
        if groupFields:
            return ' GROUP BY ' + (groupFields.name() if isinstance(groupFields, CField) else groupFields)
        else:
            return ''

    @classmethod
    def prepareHaving(cls, havingFields):
        if isinstance(havingFields, (list, tuple)):
            havingFields = cls.joinAnd(
                [havingField.name() if isinstance(havingField, CField) else havingField for havingField in
                 havingFields])
        if havingFields:
            return ' HAVING ' + (havingFields.name() if isinstance(havingFields, CField) else havingFields)
        else:
            return ''

    @classmethod
    def prepareLimit(cls, limit):
        raise NotImplementedError

    def selectStmt(
            self,
            table,
            fields='*',
            where='',
            group='',
            order='',
            limit=None,
            isDistinct=False,
            rowNumberFieldName=None,
            having=''
    ):
        tableName = self.getTableName(table)

        beginWord = 'SELECT'
        if isDistinct:
            beginWord += ' DISTINCT'
        if rowNumberFieldName and fields != '*':
            fields.insert(0, '@__rowNumber := @__rowNumber + 1 AS %s' % rowNumberFieldName)
            tableName += ', (select @__rowNumber := 0) as __rowNumberInit'
        return ' '.join([
            beginWord, self.prepareFieldList(fields),
            'FROM', tableName,
            self.prepareWhere(where),
            self.prepareGroup(group),
            self.prepareHaving(having),
            self.prepareOrder(order),
            self.prepareLimit(limit)])

    def selectMax(self, table, col='id', where=''):
        return self.selectStmt(table, self.max(col), where)

    def selectMin(self, table, col='id', where=''):
        return self.selectStmt(table, self.min(col), where)

    def selectExpr(self, fields):
        u"""
        Метод обарачивающий абстракцию подзапроса в python-код.
        :type fields: CField or list of CField
        :rtype: QtSql.QSqlRecord
        """
        stmt = ' '.join(['SELECT', self.prepareFieldList(fields)])
        query = self.query(stmt)
        if query.first():
            record = query.record()
            return record
        return None

    def existsStmt(self, table, where, limit=None):
        field = '*'
        if isinstance(table, CJoin):
            mainTable = table.getMainTable()
            if mainTable.hasField('id'):
                field = mainTable['id'].name()

        return 'EXISTS (%s)' % self.selectStmt(table, field, where, limit=limit)

    def notExistsStmt(self, table, where):
        return 'NOT %s' % self.existsStmt(table, where)

    def _decreaseOpenTransactionCount(self):
        if self._openTransactionsCount > 0 and self._transactionCallStackByLevel:
            self._openTransactionsCount -= 1
            self._transactionCallStackByLevel.pop()
        else:
            raise CException(self.errUnexpectedTransactionCompletion)

    def nestedTransaction(self):
        formatedPrevTransactionStack = '\n'.join(
            traceback.format_list(self._transactionCallStackByLevel[self._openTransactionsCount - 1])
        )
        raise CException('\n'.join([self.errNestedTransactionCall,
                                    self.errPreviousTransactionCallStack % formatedPrevTransactionStack]))

    def checkCallStackInheritance(self, currentCallStack):
        prevCallStack = self._transactionCallStackByLevel[self._openTransactionsCount - 1] \
            if (self._openTransactionsCount - 1) in xrange(len(self._transactionCallStackByLevel)) \
            else []
        compareCallStackResult = compareCallStack(prevCallStack, currentCallStack, 'traceback.extract_stack()')
        if prevCallStack and compareCallStackResult[1] != 1:
            formatedPrevTransactionStack = '\n'.join(traceback.format_list(prevCallStack))
            raise CException('\n'.join([self.errInheritanceTransaction,
                                        self.errPreviousTransactionCallStack % formatedPrevTransactionStack]))

    def transaction(self, checkIsInit=False):
        """
            Открывает транзакцию.
            Если ранее уже была открыта транзакция, то открывает вложенную транзакцию.
        :param checkIsInit: Включить проверку того, что открываемая транзакция должна быть первой\основной.
        """
        self.checkdb()

        currentCallStack = traceback.extract_stack()
        self.checkCallStackInheritance(currentCallStack)

        if self._openTransactionsCount == 0:
            if not self.db.transaction():
                raise CDatabaseException(CDatabase.errTransactionError, self.db.lastError())
        elif checkIsInit:
            raise CException(CDatabase.errNoRootTransaction % self._openTransactionsCount)
        else:
            self.nestedTransaction()

        self._openTransactionsCount += 1
        self._transactionCallStackByLevel.append(currentCallStack)

    def nestedCommit(self):
        pass

    def nestedRollback(self):
        pass

    def commit(self):
        self.checkdb()

        currentCallStack = traceback.extract_stack()
        self.checkCallStackInheritance(currentCallStack)

        if self._openTransactionsCount == 1:
            if not self.db.commit():
                raise CDatabaseException(CDatabase.errCommitError, self.db.lastError())
        else:
            self.nestedCommit()

        self._decreaseOpenTransactionCount()

    def rollback(self):
        self.checkdb()

        currentCallStack = traceback.extract_stack()
        self.checkCallStackInheritance(currentCallStack)

        if (self._openTransactionsCount - 1) == 0:
            if not self.db.rollback():
                raise CDatabaseException(CDatabase.errRollbackError, self.db.lastError())
        else:
            self.nestedRollback()

        self._decreaseOpenTransactionCount()

    def table(self, tableName, idFieldName='id'):
        if self.tables.has_key(tableName):
            return self.tables[tableName]
        else:
            table = CTable(tableName, self)
            if u'id' in [v.fieldName for v in table.fields]:
                table.setIdFieldName(idFieldName)
            self.tables[tableName] = table
            return table

    def join(self, firstTable, secondTable, onCond, stmt='JOIN'):
        if isinstance(onCond, (list, tuple)):
            onCond = self.joinAnd(onCond)
        return CJoin(self.forceTable(firstTable), self.forceTable(secondTable), onCond, stmt)

    def leftJoin(self, firstTable, secondTable, onCond):
        return self.join(firstTable, secondTable, onCond, 'LEFT JOIN')

    def innerJoin(self, firstTable, secondTable, onCond):
        return self.join(firstTable, secondTable, onCond, 'INNER JOIN')

    def record(self, tableName):
        self.checkdb()
        if tableName.strip().lower().startswith('select'):
            res = self.query(tableName + self.prepareLimit(1)).record()
        else:
            parts = tableName.split('.', 1)
            if len(parts) <= 1:
                res = self.db.record(tableName)
                if not res:  # проверка соединения и повторная попытка в случае потери подключения
                    self.checkConnect()
                    res = self.db.record(tableName)
            else:
                currentDatabaseName = self.db.databaseName()
                databaseName = parts[0]
                # проверка подключения производится внутри query
                self.query('USE %s' % self.escapeSchemaName(databaseName))
                res = self.db.record(parts[1])
                self.query('USE %s' % self.escapeSchemaName(currentDatabaseName))

        if res.isEmpty():
            raise CDatabaseException(CDatabase.errTableNotFound % tableName)
        return res

    def recordFromDict(self, tableName, dct):
        table = self.forceTable(tableName)
        rec = table.newRecord(fields=dct.keys())
        for fieldName, value in dct.iteritems():
            rec.setValue(fieldName, toVariant(value))
        return rec

    def insertFromDict(self, tableName, dct):
        return self.insertRecord(tableName, self.recordFromDict(tableName, dct))

    def insertMultipleFromDict(self, tableName, lst):
        for dct in lst:
            self.insertRecord(tableName, self.recordFromDict(tableName, dct))

    @printQueryTime(callStack=True, printQueryFirst=True)
    def query(self, stmt, quietReconnect=False):
        # TODO: Обнаружено интересное поведение при отказе от восстановления разорванного соединения:
        # Все query, ожидающие восстановления узнают, что соединение закрыто и checkdb захламляет error.log.
        self.checkdb()
        result = QtSql.QSqlQuery(self.db)
        result.setForwardOnly(True)
        result.setNumericalPrecisionPolicy(QtSql.QSql.LowPrecisionDouble)
        repeatCounter = 0
        needRepeat = True
        while needRepeat:
            needRepeat = False
            if not result.exec_(stmt):
                lastError = result.lastError()
                if lastError.databaseText().contains(self.returnedDeadlockErrorText):
                    needRepeat = repeatCounter <= self.deadLockRepeat
                elif self.isConnectionLostError(lastError):
                    if self.restoreConnection(quietReconnect or self.restoreConnectState == 1):
                        needRepeat = True
                    else:
                        self.connectDown()
                else:
                    needRepeat = False
                    self.onError(stmt, lastError)
            repeatCounter += 1
        return result

    def onError(self, stmt, sqlError):
        raise CDatabaseException(stmt + u'\n' + CDatabase.errQueryError % stmt, sqlError)

    @staticmethod
    def checkDatabaseError(lastError, stmt=None):
        if lastError.isValid() and lastError.type() != QtSql.QSqlError.NoError:
            message = u'Неизвестная ошибка базы данных'
            if lastError.type() == QtSql.QSqlError.ConnectionError:
                message = u'Ошибка подключения к базе данных'
            elif lastError.type() == QtSql.QSqlError.StatementError:
                message = u'Ошибка SQL-запроса'
            elif lastError.type() == QtSql.QSqlError.TransactionError:
                message = u'Ошибка SQL-запроса'
            if stmt:
                message += u'\n(%s)\n' % stmt
            raise CDatabaseException(message, lastError)

    def getRecordEx(self, table=None, cols=None, where='', order='', stmt=None):
        if stmt is None:
            stmt = self.selectStmt(table, cols, where, order=order, limit=1)
        query = self.query(stmt)
        if query.first():
            record = query.record()
            return record
        else:
            return None

    def getRecord(self, table, cols, itemId):
        idCol = self.mainTable(table).idField()
        return self.getRecordEx(table, cols, idCol.eq(itemId))


    def updateRecord(self, table, record):
        """
        Производит обновление записи record  в таблице table
        :param table: CTable, CJoin, CUnionTable, CSubQueryTable или строка
        :param record:
        :return:
        None если не обновил
        """
        table = self.forceTable(table)
        table.beforeUpdate(record)
        fieldsCount = record.count()
        idFieldName = table.idFieldName()
        values = []
        cond = ''
        itemId = None
        for i in range(fieldsCount):

            # My insertion for 'rbImageMap' table
            if table.name() == 'rbImageMap':
                pair = self.escapeFieldName(record.fieldName(i)) + '=' + self.formatValue(record.field(i))
                if record.fieldName(i) == idFieldName:
                    cond = pair
                    itemId = record.value(i).toInt()[0]
                elif record.fieldName(i) == 'image':
                    pass
                else:
                    values.append(pair)
            else:
                pair = self.escapeFieldName(record.fieldName(i)) + '=' + self.formatValue(record.field(i))
                if record.fieldName(i) == idFieldName:
                    cond = pair
                    itemId = record.value(i).toInt()[0]
                else:
                    values.append(pair)
        stmt = 'UPDATE ' + table.name() + ' SET ' + (', '.join(values)) + ' WHERE ' + cond
        self.query(stmt)
        return itemId

    def insertRecord(self, table, record):
        table = self.forceTable(table)
        table.beforeInsert(record)
        fieldsCount = record.count()
        fields = []
        values = []
        for i in xrange(fieldsCount):
            if not record.value(i).isNull():
                fields.append(self.escapeFieldName(record.fieldName(i)))
                values.append(self.formatValue(record.field(i)))
        stmt = ('INSERT INTO ' + table.name() +
                '(' + (', '.join(fields)) + ') ' +
                'VALUES (' + (', '.join(values)) + ')')
        itemId = self.query(stmt).lastInsertId().toInt()[0]
        idFieldName = table.idFieldName()
        record.setValue(idFieldName, QVariant(itemId))
        return itemId

    def insertMultipleRecords(self, table, records):
        if len(records) == 0: return
        table = self.forceTable(table)
        fields = []
        values = []
        for i in xrange(len(records)):
            tfields = []
            tvalues = []
            for j in xrange(records[i].count()):
                tfields.append(self.escapeFieldName(records[i].fieldName(j)))
                tvalues.append(self.formatValue(records[i].field(j)))
            fields.append(tfields)
            values.append(tvalues)
        stmt = (u'INSERT INTO ' + table.name() + (u'(' + u', '.join(fields[0])) + u') VALUES')
        for value in values:
            stmt += (u'(' + u', '.join(value) + u'),')
        stmt = stmt[:len(stmt) - 1]
        self.query(stmt)

    def insertMultipleRecordsByChunks(self, table, records, chunkSize=None):
        if len(records) == 0: return
        if chunkSize is None: chunkSize = len(records)
        table = self.forceTable(table)
        firstRecord = records[0]
        fields = [self.escapeFieldName(firstRecord.fieldName(i)) for i in xrange(firstRecord.count())]
        stmtInsert = u'INSERT INTO ' + table.name() + (u'(' + u', '.join(fields)) + u') VALUES '
        recordsIterator = iter(records)
        for _ in xrange(len(records) / chunkSize + 1):
            values = []
            for record in itertools.islice(recordsIterator, 0, chunkSize):
                values.append([self.formatValue(record.field(i)) for i in xrange(record.count())])
            if values:
                rows = [u'(' + u', '.join(value) + u')' for value in values]
                stmt = stmtInsert + ','.join(rows)
                self.query(stmt)

    def prepareInsertInto(self, table, fields):
        table = self.forceTable(table)
        return u'INSERT INTO {tableName} ({fields})'.format(
            tableName=table.name(),
            fields=u','.join(map(self.escapeFieldName, fields))
        )

    def prepareOnDuplicateKeyUpdate(self, fields, updateFields=None, keepOldFields=None):
        u"""
        Формирование условий обновления полей в INSERT INTO-запросе
        :param fields: все затрагиваемые поля
        :type fields: list
        :param updateFields: список обновляемых полей (если не задано - все, кроме неизменяемых)
        :type updateFields: list
        :param keepOldFields: список полей, значения которых не изменяются в результате запроса
        :type keepOldFields: list
        :rtype: unicode
        """
        updateMap = {}
        if keepOldFields is not None:
            if updateFields is None:
                updateFields = list(set(fields).difference(set(keepOldFields)))
            else:
                for field in keepOldFields:
                    updateMap[field] = u'{field}={field}'.format(field=self.escapeFieldName(field))
        if updateFields is not None:
            for field in updateFields:
                updateMap[field] = u'{field}=VALUES({field})'.format(field=self.escapeFieldName(field))

        if updateMap:
            return u'ON DUPLICATE KEY UPDATE {0}'.format(u','.join(updateMap.itervalues()))

        return u''

    def insertValues(self, table, fields, values=None, keepOldFields=None, updateFields=None):
        u""" Множественная вставка в таблицу / обновление
        :param table: Имя таблицы
        :param fields:  Поля, затрагиваемые при обновлении/вставки
        :param values: [list of tuple]: Список значениё полей
        :param keepOldFields: Сохраняемые поля
        :param updateFields: Обновляемые поля
        :rtype: int | None """
        if not (fields and values): return

        parts = [
            self.prepareInsertInto(table, fields),
            u'VALUES {0}'.format(u','.join(u'(%s)' % u','.join(map(self.formatArg, v)) for v in values)),
            self.prepareOnDuplicateKeyUpdate(fields, updateFields, keepOldFields)
        ]
        query = self.query(u' '.join(parts))
        lastInsertId = query.lastInsertId().toInt()[0]
        return lastInsertId

    def insertItem(self, table, dct, fields=None, keepOldFields=None, updateFields=None):
        u""" Вставка (обновление) записи
        :type table: CTable | str
        :type dct: dict
        :param fields: список полей записи
        :param keepOldFields: необновляемые поля
        :param updateFields: обновляемые поля """
        if not fields:
            fields = dct.keys()
        values = [tuple(dct.get(field) for field in fields)]
        return self.insertValues(table, fields, values, keepOldFields=keepOldFields, updateFields=updateFields)

    def insertFromDictList(self, table, dctList, fields=None, keepOldFields=None, updateFields=None, chunkSize=None):
        u"""
        Множественная вставка в таблицу / обновление из спика словарей
        :param table: Имя таблицы
        :param dctList: [list of dict]: [ .., { .., 'fieldName': value, .. }, .. ]
        :param fields: Все затрагиваемые поля таблицы (если не задано, берутся из первого словаря)
        :param keepOldFields: Сохраняемые поля
        :param updateFields: Обновляемые поля
        :param chunkSize: Разбиение запроса на группы по chunkSize
        """
        if not dctList: return
        if not fields:
            fields = dctList[0].keys()
        if not chunkSize:
            chunkSize = len(dctList)

        listIterator = iter(dctList)
        for _ in xrange(0, len(dctList), chunkSize):
            values = [
                tuple(dct.get(field) for field in fields)
                for dct in itertools.islice(listIterator, 0, chunkSize)
            ]
            self.insertValues(table, fields, values, keepOldFields=keepOldFields, updateFields=updateFields)

    def insertOrUpdate(self, table, record):
        table = self.forceTable(table)
        idFieldName = table.idFieldName()
        if record.isNull(idFieldName):
            return self.insertRecord(table, record)
        else:
            return self.updateRecord(table, record)
