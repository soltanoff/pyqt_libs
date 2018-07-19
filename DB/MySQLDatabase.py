# -*- coding: utf-8 -*-
from PyQt4 import QtSql

from DB.BaseDBRoutine import CDatabaseRoutine
from DB.Database import CDatabase
from DB.MySQLRoutine import CMySqlRoutineMap
from DB.Tools import CSqlExpression
from Utils.Exceptions import CDatabaseException
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

    def escapeFieldName(self, name):
        u = unicode(name)
        if u.startswith('`') and u.endswith('`'):
            return u
        else:
            return '`' + u + '`'

    escapeTableName = escapeFieldName
    escapeSchemaName = escapeFieldName

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

    def prepareLimit(self, limit):
        if isinstance(limit, (list, tuple)):
            assert len(limit) == 2
            return self.limit2 % limit
        elif isinstance(limit, int):
            return self.limit1 % limit
        else:
            return ''

    def nestedTransaction(self):
        QtSql.QSqlQuery(self.db).exec_('SAVEPOINT LEVEL_%d' % (self._openTransactionsCount + 1))
        if self.db.lastError().isValid():
            raise CDatabaseException(CDatabase.errTransactionError, self.db.lastError())

    def nestedCommit(self):
        QtSql.QSqlQuery(self.db).exec_('RELEASE SAVEPOINT LEVEL_%d' % self._openTransactionsCount)
        if self.db.lastError().isValid():
            raise CDatabaseException(CDatabase.errNestedCommitTransactionError, self.db.lastError())

    def nestedRollback(self):
        QtSql.QSqlQuery(self.db).exec_('ROLLBACK TO SAVEPOINT LEVEL_%d' % self._openTransactionsCount)
        if self.db.lastError().isValid():
            raise CDatabaseException(CDatabase.errNestedRollbackTransactionError, self.db.lastError())

    def isConnectionLostError(self, sqlError):
        if sqlError and sqlError.number() in [CMySqlDatabase.CR_SERVER_GONE_ERROR,
                                              CMySqlDatabase.CR_SERVER_LOST]:
            return True
        return CDatabase.isConnectionLostError(self, sqlError)
