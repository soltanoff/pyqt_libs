# -*- coding: utf-8 -*-
import re

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import QVariant


class CRecordCache(object):
    def __init__(self, capacity=200, fakeValues=None):
        if fakeValues is None:
            fakeValues = []
        self.map = {}
        self.queue = []
        self.fakeKeys = []
        self.capacity = capacity
        self.fakeValues = fakeValues
        if fakeValues:
            self.loadFakeValues(fakeValues)

    def loadFakeValues(self, fakeValues):
        if fakeValues:
            self.clearFakeValues()
            for fakeKey, fakeRecord in fakeValues:
                self.fakeKeys.append(fakeKey)
                self.map[fakeKey] = fakeRecord
        else:
            self.clearFakeValues()

    def clearFakeValues(self):
        for key in self.fakeKeys:
            if key in self.map:
                del (self.map[key])
        self.fakeKeys = []

    def invalidate(self, keyList=None):
        if not keyList:
            keyList = []
        if keyList:
            for key in keyList:
                if self.map.has_key(key):
                    del self.map[key]
                if key in self.queue:
                    self.queue.remove(key)
        else:
            self.map = {}
            self.queue = []
            self.fakeKeys = []
            if self.fakeValues:
                self.loadFakeValues(self.fakeValues)

    def has_key(self, key):
        return self.map.has_key(key)

    def get(self, key):
        return self.map.get(key, None)

    def put(self, key, record):
        if self.map.has_key(key):
            self.map[key] = record
        else:
            if self.capacity and len(self.queue) >= self.capacity:
                top = self.queue[0]
                del (self.queue[0])
                del (self.map[top])
            self.queue.append(key)
            self.map[key] = record


class CTableRecordCache(CRecordCache):
    def __init__(self, database, table, cols='*', capacity=300, fakeValues=None, idCol=None, deletedCol=False,
                 order=None, idFieldName='id', filter=None):
        if not fakeValues:
            fakeValues = []
        CRecordCache.__init__(self, capacity, fakeValues)
        self.database = database
        self.table = table
        try:
            self.idCol = self.database.mainTable(self.table, idFieldName)[idCol] if idCol else self.database.mainTable(
                self.table, idFieldName).idField()
            orderFieldName = self.database.mainTable(self.table).idField().name()
        except:
            self.idCol = orderFieldName = self.database.mainTable(self.table, idFieldName)[idFieldName]

        self.setCols(cols)
        self.deletedCol = deletedCol
        self._order = order if order else u'%s DESC' % orderFieldName
        self.filter = filter

    # noinspection PyAttributeOutsideInit
    def setCols(self, cols):
        if isinstance(cols, (tuple, list)):
            cols = ', '.join(u'%s' % c for c in cols)
        # Если среди указаных полей нет поля для сравнения (idCol), то добавить его
        if cols.strip() != '*' \
                and not re.search(ur'\b%s\b' % re.escape(unicode(self.idCol)), cols):
            cols = ', '.join([cols, unicode(self.idCol)])
        self.cols = cols

    def strongFetch(self, idList):
        fieldName = self.idCol.field.name()
        records = self.database.getRecordList(self.table,
                                              self.cols if self.cols == '*' else [self.cols, self.idCol],
                                              self.idCol.inlist(idList),
                                              order=self._order,
                                              limit=self.capacity)
        for record in records:
            itemId = record.value(fieldName).toInt()[0]
            self.put(itemId, record)

    def fetch(self, idList):
        filteredIdList = [itemId for itemId in idList if not self.has_key(itemId)]
        if filteredIdList:
            self.strongFetch(idList)

    def weakFetch(self, itemId, idList):
        if not self.has_key(itemId):
            self.fetch(idList)

    def get(self, itemId):
        if type(itemId) == QVariant:
            itemId = itemId.toInt()[0]
        res = CRecordCache.get(self, itemId)

        # atronah: Чтобы избежать ситуации с постоянным обращением к базе, если в кеше есть запись, но она пустая
        # было принято решение разделить понятия
        # None - отсутствие в кэше, используется в CRecordCache.get как результат отстутствия в словаре
        #  и
        # QtSql.QSqlRecord() - есть в кэше, но имеет пустое значение.
        if res is None:
            cond = [self.idCol.eq(itemId)]
            if self.deletedCol:
                cond.append(self.database.mainTable(self.table)['deleted'].eq(0))
            if self.filter:
                tblPerson = self.database.table('Person')
                tblOrgStructJob = self.database.table('OrgStructure_Job')
                tblorgStruct = self.database.table('OrgStructure')
                queryTbl = tblPerson.innerJoin(tblorgStruct, tblPerson['orgStructure_id'].eq(tblorgStruct['id']))
                queryTbl = queryTbl.innerJoin(tblOrgStructJob, tblOrgStructJob['master_id'].eq(tblorgStruct['id']))
                orgStructJobId = self.database.translate(queryTbl, tblPerson['id'], QtGui.qApp.userId,
                                                         tblOrgStructJob['id'])
                if orgStructJobId:
                    cond.append(self.database.mainTable(self.table)['orgStructureJob_id'].eq(orgStructJobId))
            res = self.database.getRecordEx(self.table, self.cols, cond, order=self._order)

            self.put(itemId, res if res else QtSql.QSqlRecord())

        # atronah: для совместимости со старым кодом решено не возвращать QtSql.QSqlRecord(), а как и раньше - None для пустой записи
        return res if res and not res.isEmpty() else None


class CTableFilteredRecordCache(CTableRecordCache):
    def __init__(self, database, table, cols='*', capacity=300, fakeValues=None, idCol=None, deletedCol=False,
                 cond=None):
        CTableRecordCache.__init__(self, database, table, cols, capacity, fakeValues, idCol, deletedCol)
        self._cond = cond

    def strongFetch(self, idList):
        fieldName = self.idCol.field.name()
        whereStmt = self.idCol.inlist(idList)
        cond = self._cond
        if cond is not None:
            if isinstance(cond, basestring):
                cond = [cond]
            if isinstance(cond, list):
                whereStmt = QtGui.qApp.db.joinAnd([whereStmt] + cond)
        records = self.database.getRecordList(self.table,
                                              self.cols if self.cols == '*' else [self.cols, self.idCol],
                                              whereStmt,
                                              order=self._order,
                                              limit=self.capacity)
        for record in records:
            itemId = record.value(fieldName).toInt()[0]
            self.put(itemId, record)
