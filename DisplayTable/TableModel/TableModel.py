# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QAbstractTableModel, Qt, QVariant, QModelIndex
from PyQt4.QtGui import QMessageBox

from DB.Cache import CTableRecordCache
from Utils.Exceptions import CException, CDatabaseException


class CTableModel(QAbstractTableModel, object):
    u"""Модель для хранения содержимого таблицы БД"""
    __pyqtSignals__ = ('itemsCountChanged(int)',
                       )
    idFieldName = 'id'
    fetchSize = 20

    def __init__(self, parent, cols=None, tableName='', allowColumnsHiding=False):
        u"""
        :param parent:
        :type cols: list of CCol
        :param tableName:
        :param allowColumnsHiding:
        """
        if not cols:
            cols = []
        QAbstractTableModel.__init__(self, parent)
        self._cols = []
        self._recordsCache = None
        self._table = None
        self._allowColumnsHiding = allowColumnsHiding
        self._loadFields = []
        self._isSorted = False
        self._sortColumn = 0
        self._sortOrder = QtCore.Qt.AscendingOrder

        self.setIdList([])
        self._cols.extend(col for col in cols if col.isEnabled())
        if tableName:
            self.setTable(tableName)

    def addColumn(self, col):
        u"""
        :type col: CCol
        """
        if col.isEnabled() and not self.isHiddenCol(col.fields()):
            self._cols.append(col)
        return col

    def cols(self):
        u"""
        :rtype: list of CCol
        """
        if not self.hasHiddenCols() or not self._allowColumnsHiding:
            return self._cols

        cols = []
        for col in self._cols:
            if col.isVisible():
                cols.append(col)
        return cols

    def hasHiddenCols(self):
        for col in self._cols:
            if col.isVisible() == False:
                return True
        return False

    def loadField(self, field):
        self._loadFields.append(field)

    def setTable(self, tableName, recordCacheCapacity=300, deletedCol=False):
        db = QtGui.qApp.db
        self._table = db.table(tableName, self.idFieldName)
        loadFields = [self.idFieldName]
        loadFields.extend(self._loadFields)
        for col in self._cols:
            loadFields.extend(col.fields())
        loadFields = set(loadFields)
        if '*' in loadFields:
            loadFields = '*'
        else:
            loadFields = ', '.join([self._table[fieldName].name() for fieldName in loadFields])
        self._recordsCache = CTableRecordCache(db, self._table, loadFields, recordCacheCapacity,
                                               idFieldName=self.idFieldName, deletedCol=deletedCol)

    def table(self):
        return self._table

    def recordCache(self):
        return self._recordsCache

    def invalidateRecordsCache(self):
        if self._recordsCache:
            self._recordsCache.invalidate()
        for col in self._cols:
            col.invalidateRecordsCache()

    def setIdList(self, idList, realItemCount=None, resetCache=True):
        self._idList = idList
        self._realItemCount = realItemCount
        self._prevColumn = None
        self._prevRow = None
        self._prevData = None
        if resetCache:
            self.invalidateRecordsCache()
        self._isSorted = False
        self.reset()
        self.emitItemsCountChanged()

    def idList(self):
        return self._idList

    def getRealItemCount(self):
        return self._realItemCount

    def getRecordByRow(self, row):
        id = self._idList[row]
        self._recordsCache.weakFetch(id, self._idList[max(0, row - self.fetchSize):(row + self.fetchSize)])
        return self._recordsCache.get(id)

    def getRecordById(self, id):
        return self._recordsCache.get(id)

    def findItemIdIndex(self, id):
        if id in self._idList:
            return self._idList.index(id)
        else:
            return -1

    def getRecordValues(self, column, row):
        u""" :rtype: (CCol, list[QtCore.QVariant]) """
        col = self._cols[column]
        if self._prevColumn != column or self._prevRow != row or self._prevData is None:
            id = self._idList[row]
            self._recordsCache.weakFetch(id, self._idList[max(0, row - self.fetchSize):(row + self.fetchSize)])
            record = self._recordsCache.get(id)
            self._prevData = col.extractValuesFromRecord(record)
            self._prevColumn = column
            self._prevRow = row
        return col, self._prevData

    def sort(self, column, order=QtCore.Qt.AscendingOrder):
        def sortHelper(row):
            col, values = self.getRecordValues(column, row)
            val = col.formatNative(values)
            return val

        if column != self._sortColumn:
            self._sortColumn = column
            self._isSorted = False
        if order != self._sortOrder:
            self._sortOrder = order
            self._isSorted = False
        if self._idList and not self._isSorted:
            self.setIdList(map(lambda x: self._idList[x],
                               sorted(range(len(self._idList)),
                                      key=lambda x: sortHelper(x),
                                      reverse=order == QtCore.Qt.DescendingOrder)),
                           resetCache=False)
            self._isSorted = True

    def columnCount(self, index=QtCore.QModelIndex()):
        return len(self._cols)

    def rowCount(self, index=QtCore.QModelIndex()):
        return len(self._idList)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:  ### or role == Qt.EditRole:
            (col, values) = self.getRecordValues(column, row)
            return col.format(values)
        elif role == Qt.UserRole:
            (col, values) = self.getRecordValues(column, row)
            return values[0]
        elif role == Qt.TextAlignmentRole:
            col = self._cols[column]
            return col.alignment()
        elif role == Qt.CheckStateRole:
            (col, values) = self.getRecordValues(column, row)
            return col.checked(values)
        elif role == Qt.ForegroundRole:
            (col, values) = self.getRecordValues(column, row)
            return col.getForegroundColor(values)
        elif role == Qt.BackgroundRole:
            (col, values) = self.getRecordValues(column, row)
            return col.getBackgroundColor(values)
        elif role == Qt.DecorationRole:
            (col, values) = self.getRecordValues(column, row)
            return col.getDecoration(values)
        elif role == Qt.ToolTipRole:
            (col, values) = self.getRecordValues(column, row)
            return col.toolTipValue(values)
        return QVariant()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self._cols[section].title()
            if role == Qt.ToolTipRole:
                return self._cols[section].toolTip()
            if role == Qt.WhatsThisRole:
                return self._cols[section].whatsThis()
        return QVariant()

    def canRemoveRow(self, row):
        return self.canRemoveItem(self._idList[row])

    def canRemoveItem(self, itemId):
        return True

    def confirmRemoveRow(self, view, row, multiple=False):
        return self.confirmRemoveItem(view, self._idList[row], multiple)

    def confirmRemoveItem(self, view, itemId, multiple=False):
        # multiple: запрос относительно одного элемента из множества, нужно предусмотреть досрочный выход из серии вопросов
        # результат: True: можно удалять
        #            False: нельзя удалять
        #            None: удаление прервано
        buttons = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
        if multiple:
            buttons |= QtGui.QMessageBox.Cancel
        mbResult = QtGui.QMessageBox.question(view, u'Внимание!', u'Действительно удалить?', buttons,
                                              QtGui.QMessageBox.No)
        return {QtGui.QMessageBox.Yes: True,
                QtGui.QMessageBox.No: False}.get(mbResult, None)

    def beforeRemoveItem(self, itemId):
        pass

    def afterRemoveItem(self, itemId):
        pass

    def removeRow(self, row, parent=QModelIndex(), *args, **kwargs):
        if self._idList and 0 <= row < len(self._idList):
            itemId = self._idList[row]
            if self.canRemoveItem(itemId):
                QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
                try:
                    db = QtGui.qApp.db
                    table = self._table
                    db.transaction()
                    try:
                        self.beforeRemoveItem(itemId)
                        self.deleteRecord(table, itemId)
                        self.afterRemoveItem(itemId)
                        db.commit()
                    except:
                        db.rollback()
                        raise
                    self.beginRemoveRows(parent, row, row)
                    del self._idList[row]
                    self.endRemoveRows()
                    self.emitItemsCountChanged()
                    for x in self._cols:
                        if (hasattr(x, 'clearCache')):
                            x.clearCache()
                    return True
                finally:
                    QtGui.QApplication.restoreOverrideCursor()
        return False

    def removeRowList(self, rowList, parent=QModelIndex(), raiseExceptions=False):
        if self._idList:  # and 0<=row<len(self._idList):
            try:
                QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
                db = QtGui.qApp.db
                db.transaction()
                table = self._table
                for row in rowList:
                    itemId = self._idList[row]
                    if not self.canRemoveItem(itemId):
                        raise CException(u'cannot remove item with id %i' % itemId)
                    self.beforeRemoveItem(itemId)
                    self.beginRemoveRows(parent, row, row)
                    self.deleteRecord(table, itemId)
                    del self._idList[row]
                    self.endRemoveRows()
                    self.afterRemoveItem(itemId)
                    self.emitItemsCountChanged()
                db.commit()
            except:
                db.rollback()
                if raiseExceptions:
                    raise
            finally:
                QtGui.QApplication.restoreOverrideCursor()

    def removeIdList(self, idList, parent=QModelIndex(), raiseExceptions=False):
        if self._idList:
            try:
                QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
                db = QtGui.qApp.db
                db.transaction()
                table = self._table
                for itemId in idList:
                    if itemId in self._idList:
                        row = self._idList.index(itemId)
                        if not self.canRemoveItem(itemId):
                            raise CException(u'cannot remove item with id %i' % itemId)
                        self.beforeRemoveItem(itemId)
                        self.beginRemoveRows(parent, row, row)
                        self.deleteRecord(table, itemId)
                        del self._idList[row]
                        self.endRemoveRows()
                        self.afterRemoveItem(itemId)
                        self.emitItemsCountChanged()
                db.commit()
            except:
                db.rollback()
                if raiseExceptions:
                    raise
            finally:
                QtGui.QApplication.restoreOverrideCursor()

    def deleteRecord(self, table, itemId):
        if table.hasField('deleted'):
            QtGui.qApp.db.markRecordsDeleted(table, table[self.idFieldName].eq(itemId))
        else:
            try:
                QtGui.qApp.db.deleteRecord(table, table[self.idFieldName].eq(itemId))
            except CDatabaseException:
                QMessageBox().critical(None, u'Ошибка',
                                       u'Не удалось удалить. Возможно, запись используется другим объектом.')

    def emitItemsCountChanged(self):
        self.emit(QtCore.SIGNAL('itemsCountChanged(int)'), len(self._idList) if self._idList else 0)

    def emitDataChanged(self):
        leftTop = self.index(0, 0)
        rightBottom = self.index(self.rowCount(), self.columnCount())
        self.emit(QtCore.SIGNAL('dataChanged(QModelIndex, QModelIndex)'), leftTop, rightBottom)
