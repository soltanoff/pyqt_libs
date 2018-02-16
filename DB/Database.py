# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import QObject, QVariant, pyqtSignal, Qt
from PyQt4.QtGui import QMessageBox

from DB.Field import CField
from DB.Tools import decorateString, CSqlExpression, CSubQueryTable
from Utils.Exceptions import CDatabaseException
from Utils.Forcing import toVariant, forceString


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
