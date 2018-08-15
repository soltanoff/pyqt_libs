# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore, QtSql

from EditableTable.InDocTableModel.Col import CInDocTableCol
from Utils.Forcing import forceRef


class CBackRelationInDocTableCol(CInDocTableCol):
    def __init__(self,
                 interfaceCol,
                 primaryKey,
                 surrogateFieldName,
                 subTableName,
                 subTableForeignKey,
                 subTableCond,
                 subTableNewRecord,
                 **params):
        u"""
        Создает экземпляр класса для обработки поведения столбца в модели.
        Основная задача класса: подгрузка и сохранение данных из подчиненной таблицы (относительно базовой таблицы модели)
        Для отображения и редактирования используется объект CInDocTableCol, переданный в параметрах (interfaceCol).

        :param interfaceCol: экземпляр класса для представления данных столбца (его отображения и редактирования)
        :param primaryKey: имя поля, хранящего id базовой записи из основной таблицы модели.
        :param surrogateFieldName: имя поле для временного хранения значения в базовой записи.
        :param subTableName: имя подчиненной таблицы, хранящей непосредственное значение для столбца.
        :param subTableForeignKey: имя поля в подчиненной таблице, по которому происходит связь с основной таблицей
        :param subTableCond: условие для ограничения выборки из подчиненной таблицы.
        :param subTableNewRecord: новая запись для подчиненной таблицы на случай записи ранее отсутствующего значения.
        :param params: дополнительные параметры.
        """
        super(CBackRelationInDocTableCol, self).__init__(title=interfaceCol.title(),
                                                          fieldName=surrogateFieldName,
                                                          width=interfaceCol.width(),
                                                          **params)
        self.setExternal(True)

        self._primaryKey = primaryKey
        self._surrogateFieldName = surrogateFieldName
        self._subTable = QtGui.qApp.db.table(subTableName)
        self._subRecordCache = {}
        self._subTableForeignKey = subTableForeignKey
        self._subTableNewRecord = subTableNewRecord
        self._subCol = interfaceCol
        self._subTableCond = subTableCond if isinstance(subTableCond, list) else [subTableCond]

    def subCol(self):
        return self._subCol

    def createEditor(self, parent):
        return self._subCol.createEditor(parent)

    def flags(self, index=None):
        return self._subCol.flags(index)

    def toString(self, val, record):
        return self._subCol.toString(val, record)

    def toStatusTip(self, val, record):
        return self._subCol.toStatusTip(val, record)

    def toCheckState(self, val, record):
        return self._subCol.toCheckState(val, record)

    def _getSubRecord(self, masterId):
        subRecord = self._subRecordCache.setdefault(masterId, None)
        if subRecord is None:
            subRecord = QtGui.qApp.db.getRecordEx(
                table=self._subTable,
                cols='*',
                where=[self._subTable[self._subTableForeignKey].eq(masterId)] + self._subTableCond,
                order=u'%s DESC' % self._subTable.idField()
            )
            if subRecord is None:
                subRecord = QtSql.QSqlRecord(self._subTableNewRecord)
                subRecord.setValue(self._subTableForeignKey, QtCore.QVariant(masterId))
            self._subRecordCache[masterId] = subRecord
        return subRecord

    def setEditorData(self, editor, value, record):
        masterId = forceRef(record.value(self._primaryKey))
        subRecord = self._getSubRecord(masterId)
        # Если полученное из модели значение пустое
        if not value.isValid():
            # то попытаться вытянуть его из базы
            value = subRecord.value(self._subCol.fieldName())

        self._subCol.setEditorData(editor, value, subRecord)

    def getEditorData(self, editor):
        return self._subCol.getEditorData(editor)

    def saveExternalData(self, rowRecord):
        masterId = forceRef(rowRecord.value(self._primaryKey))
        value = rowRecord.value(self._surrogateFieldName)

        subRecord = self._getSubRecord(masterId)
        subRecord.setValue(self._subCol.fieldName(), value)
        subRecord.setValue(self._subTableForeignKey, QtCore.QVariant(masterId))
        subRecordId = QtGui.qApp.db.insertOrUpdate(self._subTable, subRecord)
        subRecord.setValue(self._subTable.idField(), QtCore.QVariant(subRecordId))

    def setEndDate(self, endDate):
        self._subCol.setEndDate(endDate)
