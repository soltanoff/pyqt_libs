# -*- coding: utf-8 -*-
from PyQt4 import QtGui

from DB.Cache import CTableRecordCache
from EditableTable.InDocTableModel.Col import CInDocTableCol
from Types.ComboBox import CComboBox
from Utils.Forcing import forceRef, toVariant, forceString


class CDesignationInDocTableCol(CInDocTableCol):
    # аналогично CDesignationCol
    def __init__(self, title, fieldName, designationChain, defaultWidth, **params):
        CInDocTableCol.__init__(self, title, fieldName, defaultWidth, **params)
        self._addNone = params.get('addNone', False)
        # Получение фильтра, по которому будут формироваться доступные для выбора значения при редактировании поля.
        # Фильтр будет применяться к таблице, указанной первой в designationChain.
        # Если в качестве фильтра будет передан кортеж из двух строк, то он будет восприниматься, как фильтр
        # <Таблица_модели>.<первое_имя_из_кортежа> = <Первая_таблица_поля>.<второе_имя_из_кортежа>
        # или
        # masterRecord[self._editorValueFilter[0]] = self._caches[0].table[self._editorValueFilter[0]]
        self._editorValueFilter = params.get('editorValueFilter', u'')
        db = QtGui.qApp.db
        if not isinstance(designationChain, list):
            designationChain = [designationChain]
        self._caches = []
        for tableName, fieldName in designationChain:
            self._caches.append(CTableRecordCache(db, db.table(tableName), fieldName))

        # словарь, хранящий для каждого условия фильтрации, список id, доступных для выбора для текущего столбца
        self._mapMasterIdToItemIdList = {}
        self.setReadOnly(True)

    def setReadOnly(self, readOnly):
        if not self._caches:
            readOnly = True
        super(CDesignationInDocTableCol, self).setReadOnly(readOnly)
        return self

    def createEditor(self, parent):
        return CComboBox(parent)

    def setEditorData(self, editor, value, record):
        subTable = self._caches[0].table
        cond = self._editorValueFilter
        if isinstance(cond, tuple) and len(cond) == 2:
            masterFieldName, slaveFieldName = self._editorValueFilter
            masterValue = record.value(masterFieldName)
            cond = subTable[slaveFieldName].eq(masterValue)

        if not self._mapMasterIdToItemIdList.has_key(cond):
            self._mapMasterIdToItemIdList[cond] = QtGui.qApp.db.getIdList(table=subTable,
                                                                          where=cond)
        editor.clear()
        if self._addNone:
            editor.addItem(u'Не выбрано', userData=toVariant(None))

        for itemId in self._mapMasterIdToItemIdList[cond]:
            itemText = forceString(self.toString(itemId, record))
            editor.addItem(itemText, userData=toVariant(itemId))

    def getEditorData(self, editor):
        itemIndex = editor.currentIndex()
        return editor.itemData(itemIndex)

    def toString(self, val, record):
        for cache in self._caches:
            itemId = forceRef(val)
            record = cache.get(itemId)
            if not record:
                return toVariant('')
            else:
                val = record.value(0)
                # На случай, когда нет ссылки на id в следующей таблицы цепочки
                # Но для текущей таблицы указаны резервные поля (нужно для полей вида freeInput)
                if val.isNull() and record.count() > 1:
                    for fieldIdx in xrange(1, record.count()):
                        val = record.value(fieldIdx)
                        if not val.isNull():
                            return toVariant(val)
        return val
