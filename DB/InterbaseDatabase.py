# -*- coding: utf-8 -*-
from PyQt4.QtCore import QVariant

from DB.Database import CDatabase
from DB.Tools import decorateString


class CInterbaseDatabase(CDatabase):
    aliasSymbol = ''

    limit1 = 'FIRST %d'
    limit2 = 'FIRST %d SKIP %d'
    convMethod = {
        QVariant.Int: lambda val: unicode(val.toInt()[0]),
        QVariant.UInt: lambda val: unicode(val.toUInt()[0]),
        QVariant.LongLong: lambda val: unicode(val.toLongLong()[0]),
        QVariant.ULongLong: lambda val: unicode(val.toULongLong()[0]),
        QVariant.Double: lambda val: unicode(val.toDouble()[0]),
        QVariant.Bool: lambda val: u'1' if val.toBool() else u'0',
        QVariant.Char: lambda val: decorateString(val.toString()),
        QVariant.String: lambda val: decorateString(val.toString()),
        QVariant.Date: lambda val: decorateString(val.toDate().toString('dd.MM.yyyy')),
        QVariant.Time: lambda val: decorateString(val.toTime().toString('hh:mm:ss')),
        QVariant.DateTime: lambda val: decorateString(val.toDateTime().toString('dd.MM.yyyy hh:mm:ss')),
        QVariant.ByteArray: lambda val: 'x\'' + str(val.toByteArray().toHex()) + '\'',
    }

    DEFAULT_LC_CTYPE = 'Win_1251'  # may be 'WIN1251', 'windows-1251', 'UNICODE_FSS', etc.

    def __init__(self, serverName, serverPort, databaseName, userName, password, connectionName=None,
                 afterConnectFunc=None, **kwargs):
        CDatabase.__init__(self, afterConnectFunc)
        self.createConnection('QIBASE', connectionName, serverName, serverPort, databaseName, userName, password)

        LC_CTYPE = kwargs.get('LC_CTYPE', '') or CInterbaseDatabase.DEFAULT_LC_CTYPE
        self.db.setConnectOptions('ISC_DPB_LC_CTYPE={0}'.format(LC_CTYPE))
        self.connectUp()

    def escapeFieldName(self, name):
        u = unicode(name)
        if u.startswith('"') and u.endswith('"'):
            return u
        else:
            return '"' + u.replace('"', '""') + '"'

    escapeTableName = escapeFieldName

    def prepareLimit(self, limit):
        if isinstance(limit, (list, tuple)):
            assert len(limit) == 2
            return self.limit2 % (limit[1], limit[0])
        elif isinstance(limit, int):
            return self.limit1 % limit
        else:
            return ''

    def selectStmt(self, table, fields='*', where='', group='', order='', limit=None, isDistinct=False):
        tableName = self.getTableName(table)
        return ' '.join([
            'SELECT',
            self.prepareLimit(limit),
            'DISTINCT' if isDistinct else '',
            self.prepareFieldList(fields),
            'FROM', tableName,
            self.prepareWhere(where),
            self.prepareGroup(group),
            self.prepareOrder(order),
        ])

    def getTestConnectionStmt(self):
        return u'SELECT \'test connection query\' FROM rdb$database;'
