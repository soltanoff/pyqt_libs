# -*- coding: utf-8 -*-
from PyQt4 import QtGui
from PyQt4.QtCore import QObject, QVariant, pyqtSignal, Qt

from DB.Tools import decorateString


class CDatabase(QObject):
    aliasSymbol = 'AS'

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
