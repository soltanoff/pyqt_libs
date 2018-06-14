# -*- coding: utf-8 -*-
from DB.BaseDBRoutine import CDatabaseRoutine
from DB.Database import CDatabase
from DB.MySQLRoutine import CMySqlRoutineMap
from DB.Tools import CSqlExpression
from Utils.Forcing import forceRef


class CMySqlDatabase(CDatabase):
    limit1 = 'LIMIT 0, %d'
    limit2 = 'LIMIT %d, %d'
    CR_SERVER_GONE_ERROR = 2006
    CR_SERVER_LOST = 2013

    returnedDeadlockErrorText = u'Deadlock found when trying to get lock;'

    def __init__(
            self,
            serverName,
            serverPort,
            databaseName,
            userName,
            password,
            connectionName=None,
            compressData=False,
            **kwargs
    ):
        CDatabase.__init__(self)
        self.createConnection('QMYSQL', connectionName, serverName, serverPort, databaseName, userName, password)
        options = []
        if compressData:
            options.append('CLIENT_COMPRESS=1')
        if options:
            self.db.setConnectOptions(';'.join(options))
        self.connectUp()
        self.query('SET NAMES \'utf8\' COLLATE \'utf8_general_ci\';')
        self.query('SET SQL_AUTO_IS_NULL=0;')
        self.query('SET SQL_MODE=\'\';')

        self._func = None
        self._proc = None

    NULL = property(lambda self: CSqlExpression(self, 'NULL'))
    func = property(lambda self: self.loadFunctions()._func)
    proc = property(lambda self: self.loadFunctions()._proc)

    def loadFunctions(self):
        if self._func is None:
            self._func = CMySqlRoutineMap(self, CDatabaseRoutine.FUNCTION)
        if self._proc is None:
            self._proc = CMySqlRoutineMap(self, CDatabaseRoutine.PROCEDURE)
        return self

    def getConnectionId(self):
        query = self.query('SELECT CONNECTION_ID();')
        return forceRef(query.record().value(0)) if query.first() else None
