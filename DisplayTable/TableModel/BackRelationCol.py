# -*- coding: utf-8 -*-
from PyQt4 import QtGui

from TableModel.Col import CCol
from Utils.Forcing import forceRef


class CBackRelationCol(CCol):
    def __init__(self,
                 interfaceCol,
                 primaryKey,
                 subTableName,
                 subTableForeignKey,
                 subTableCond,
                 alternativeValuesGetter=None
                 ):
        """
        Создает экземпляр класса для обработки поведения столбца в модели.
        Основная задача класса: подгрузка данных из подчиненной таблицы (относительно базовой таблицы модели)
        Для отображения используется объект CCol, переданный в параметрах (interfaceCol).

        :param interfaceCol: экземпляр класса для представления данных столбца (его отображения)
        :param primaryKey: имя поля, хранящего id базовой записи из основной таблицы модели.
        :param subTableName: имя подчиненной таблицы, хранящей непосредственное значение для столбца.
        :param subTableForeignKey: имя поля в подчиненной таблице, по которому происходит связь с основной таблицей
        :param subTableCond: условие для ограничения выборки из подчиненной таблицы.
        :param alternativeValuesGetter: альтернативный способ (функция) получения значений поля на основе значения prinaryKey.
        """
        super(CBackRelationCol, self).__init__(title=interfaceCol.title(),
                                               fields=[primaryKey],
                                               defaultWidth=interfaceCol.defaultWidth(),
                                               alignment=interfaceCol.alignment())

        self._subTable = QtGui.qApp.db.table(subTableName)
        self._cache = {}
        self._subTableForeignKey = subTableForeignKey
        self._subCol = interfaceCol
        self._subTableCond = subTableCond if isinstance(subTableCond, list) else [subTableCond]
        self._alternativeValuesGetter = alternativeValuesGetter

    def getRelativeValues(self, values):
        masterId = forceRef(values[0])
        if callable(self._alternativeValuesGetter):
            values = self._alternativeValuesGetter(masterId)
        else:
            if not self._cache.has_key(masterId):
                subRecord = QtGui.qApp.db.getRecordEx(table=self._subTable,
                                                      cols='*',
                                                      where=[self._subTable[self._subTableForeignKey].eq(masterId)]
                                                            + self._subTableCond,
                                                      order=u'%s DESC' % self._subTable.idField())
                if not subRecord:
                    subRecord = QtGui.qApp.db.record(self._subTable.name())
                subValues = [subRecord.value(fieldName) for fieldName in self._subCol.fields()]
                self._cache[masterId] = subValues
            values = self._cache[masterId]
        return values

    def format(self, values):
        values = self.getRelativeValues(values)
        return self._subCol.format(values)

    def formatNative(self, values):
        values = self.getRelativeValues(values)
        return self._subCol.formatNative(values)

    def invalidateRecordsCache(self):
        self._cache = {}
