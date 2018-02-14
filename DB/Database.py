# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import QObject, QVariant, pyqtSignal, Qt

from DB.Field import CField
from DB.Tools import decorateString, CSqlExpression, CSubQueryTable


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
