# -*- coding: utf-8 -*-

from DB.Database import CDatabase


class CODBCDatabase(CDatabase):
    def __init__(self, serverName, serverPort, databaseName, userName, password, connectionName=None,
                 afterConnectFunc=None, **kwargs):
        CDatabase.__init__(self, afterConnectFunc)
        self.createConnection('QODBC3', connectionName, serverName, serverPort, databaseName, userName, password)
        self.db.setConnectOptions('SQL_ATTR_ACCESS_MODE=SQL_MODE_READ_ONLY')
        self.connectUp()

    def escapeFieldName(self, name):
        u = unicode(name)
        if u.startswith('"') and u.endswith('"'):
            return u
        else:
            return '"' + u.replace('"', '""') + '"'

    escapeTableName = escapeFieldName

    def prepareLimit(self, limit):
        return ''
