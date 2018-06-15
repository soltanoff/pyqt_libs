# -*- coding: utf-8 -*-
from DB.Database import CDatabase
from DB.InterbaseDatabase import CInterbaseDatabase
from DB.MySQLDatabase import CMySqlDatabase
from DB.ODBSDatabase import CODBCDatabase
from Utils.Exceptions import CDatabaseException


def connectDataBase(driverName, serverName, serverPort, databaseName, userName, password, connectionName=None, compressData=False, afterConnectFunc=None, **kwargs):
    driverName = unicode(driverName).upper()
    if driverName == 'MYSQL':
        return CMySqlDatabase(serverName, serverPort, databaseName, userName, password, connectionName, compressData=compressData, afterConnectFunc=afterConnectFunc, **kwargs)
    elif driverName in ['INTERBASE', 'FIREBIRD']:
        return CInterbaseDatabase(serverName, serverPort, databaseName, userName, password, connectionName, afterConnectFunc=afterConnectFunc, **kwargs)
    elif driverName in ['ODBC']:
        return CODBCDatabase(serverName, serverPort, databaseName, userName, password, connectionName, afterConnectFunc=afterConnectFunc, **kwargs)
    else:
        raise CDatabaseException(CDatabase.errUndefinedDriver % driverName)
