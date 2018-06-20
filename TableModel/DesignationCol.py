# -*- coding: utf-8 -*-
from PyQt4 import QtGui

from DB.Cache import CTableRecordCache
from TableModel.Col import CCol
from Utils.Forcing import forceRef, forceString


class CDesignationCol(CCol):
    u"""
        Ссылка в базу данных с простым разыменованием
    """

    def __init__(self, title, fields, designationChain, defaultWidth, alignment='l', isRTF=False, orgStructFilter=None):
        CCol.__init__(self, title, fields, defaultWidth, alignment, isRTF)
        db = QtGui.qApp.db
        if not isinstance(designationChain, list):
            designationChain = [designationChain]
        self._caches = []
        for info in designationChain:
            tableName = info[0]
            fieldName = info[1]
            idCol = info[2] if len(info) >= 3 else None
            table = db.table(tableName)
            deletedCol = table.hasField('deleted')
            filter = orgStructFilter
            self._caches.append(
                CTableRecordCache(db, table, fieldName, idCol=idCol, deletedCol=deletedCol, filter=filter))

    def getValues(self, values):
        if values[0] is None:
            return [CCol.invalid] * len(values)
        for cache in self._caches:
            itemId = forceRef(values[0])
            record = cache.get(itemId)
            if not record:
                return [CCol.invalid] * len(values)
            else:
                values = [record.value(idx) for idx in xrange(record.count())]
        return values

    def format(self, values):
        return self.getValues(values)[0]

    def formatNative(self, values):
        return forceString(self.getValues(values)[0])

    def invalidateRecordsCache(self):
        for cache in self._caches:
            cache.invalidate()
