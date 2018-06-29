# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt, QMimeData

from ExtendedTableView import CExtendedTableView
from TableModel.RichTextItemDelegate import CRichTextItemDelegate
from Utils.Forcing import toVariant


class CTableView(CExtendedTableView):
    def __init__(self, parent):
        super(CTableView, self).__init__(parent)
        self._popupMenu = None
        self._actDeleteRow = None
        self._actCopyCell = None
        self._actRecordProperties = None
        self.__reportHeader = u'List of records'
        self.__reportDescription = u''

        self.setItemDelegate(CRichTextItemDelegate(self))

        h = self.fontMetrics().height()
        self.verticalHeader().setDefaultSectionSize(3 * h / 2)
        self.verticalHeader().hide()
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setStretchLastSection(True)

        self.setSortingEnabled(True)
        self.horizontalHeader().setSortIndicatorShown(False)

        self.setHorizontalScrollMode(self.ScrollPerPixel)
        self.setVerticalScrollMode(self.ScrollPerPixel)

    def createPopupMenu(self, actions=None):
        if not actions:
            actions = []
        self._popupMenu = QtGui.QMenu(self)
        self._popupMenu.setObjectName('popupMenu')
        for action in actions:
            if isinstance(action, QtGui.QAction):
                self._popupMenu.addAction(action)
            elif action == '-':
                self._popupMenu.addSeparator()
        self.connect(self._popupMenu, QtCore.SIGNAL('aboutToShow()'), self.popupMenuAboutToShow)
        return self._popupMenu

    def setPopupMenu(self, menu):
        self._popupMenu = menu

    def popupMenu(self):
        if not self._popupMenu:
            self.createPopupMenu()
        return self._popupMenu

    def addPopupSeparator(self):
        self.popupMenu().addSeparator()

    def addPopupAction(self, action):
        self.popupMenu().addAction(action)

    def addPopupDelRow(self):
        self._actDeleteRow = QtGui.QAction(u'Удалить запись', self)
        self._actDeleteRow.setObjectName('actDeleteRow')
        self.connect(self._actDeleteRow, QtCore.SIGNAL('triggered()'), self.removeCurrentRow)
        self.addPopupAction(self._actDeleteRow)

    def addPopupDelSelectedRow(self):
        self._actDeleteRow = QtGui.QAction(u'Удалить выбранные записи', self)
        self._actDeleteRow.setObjectName('actDeleteRow')
        self.connect(self._actDeleteRow, QtCore.SIGNAL('triggered()'), self.removeSelectedRows)
        self.addPopupAction(self._actDeleteRow)

    def addPopupCopyCell(self):
        self._actCopyCell = QtGui.QAction(u'Копировать', self)
        self._actCopyCell.setObjectName('actCopyCell')
        self.connect(self._actCopyCell, QtCore.SIGNAL('triggered()'), self.copyCurrentCell)
        self.addPopupAction(self._actCopyCell)

    def addPopupRecordProperies(self):
        self._actRecordProperties = QtGui.QAction(u'Свойства записи', self)
        self._actRecordProperties.setObjectName('actRecordProperties')
        self.connect(self._actRecordProperties, QtCore.SIGNAL('triggered()'), self.showRecordProperties)
        self.addPopupAction(self._actRecordProperties)

    def setReportHeader(self, reportHeader):
        self.__reportHeader = reportHeader

    def reportHeader(self):
        return self.__reportHeader

    def setReportDescription(self, reportDescription):
        self.__reportDescription = reportDescription

    def reportDescription(self):
        return self.__reportDescription

    def popupMenuAboutToShow(self):
        currentIndex = self.currentIndex()
        curentIndexIsValid = currentIndex.isValid()
        if self._actDeleteRow:
            self._actDeleteRow.setEnabled(curentIndexIsValid and self.canRemoveRow(currentIndex.row()))
        if self._actCopyCell:
            self._actCopyCell.setEnabled(curentIndexIsValid)
        if self._actRecordProperties:
            self._actRecordProperties.setEnabled(curentIndexIsValid)

    def setIdList(self, idList, itemId=None, realItemCount=None, **params):
        if not itemId:
            itemId = self.currentItemId()
        if not idList:
            selectionModel = self.selectionModel()
            if selectionModel:
                selectionModel.clear()
        self.model().setIdList(idList, realItemCount, **params)
        if idList:
            self.setCurrentItemId(itemId)
        if self.isSortingEnabled() and self.horizontalHeader().isSortIndicatorShown():
            self.sortByColumn(self.horizontalHeader().sortIndicatorSection(),
                              self.horizontalHeader().sortIndicatorOrder())

    def setCurrentRow(self, row):
        rowCount = self.model().rowCount()
        if row >= rowCount:
            row = rowCount - 1
        if row >= 0:
            self.setCurrentIndex(self.model().index(row, 0))
        elif rowCount > 0:
            self.setCurrentIndex(self.model().index(0, 0))

    def currentRow(self):
        index = self.currentIndex()
        if index.isValid():
            return index.row()
        return None

    def setCurrentItemId(self, itemId):
        self.setCurrentRow(self.model().findItemIdIndex(itemId))

    def currentItemId(self):
        return self.itemId(self.currentIndex())

    def currentItem(self):
        itemId = self.currentItemId()
        record = self.model().recordCache().get(itemId) if itemId else None
        return record

    def selectedRowList(self):
        return list(set([index.row() for index in self.selectedIndexes()]))

    def selectedElementsAsStringsList(self):
        return list(set([(unicode(index.data().toString())) for index in self.selectedIndexes()]))

    def selectedItemIdList(self):
        itemIdList = self.model().idList()
        return [itemIdList[row] for row in self.selectedRowList()]

    def setSelectedRowList(self, rowList):
        model = self.model()
        selectionModel = self.selectionModel()
        for row in rowList:
            index = model.index(row, 0)
            selectionModel.select(index, QtGui.QItemSelectionModel.Select|QtGui.QItemSelectionModel.Rows)

    def setSelectedItemIdList(self, idList):
        self.setSelectedRowList((self.model().findItemIdIndex(itemId) for itemId in idList))

    def prepareCopy(self):
        cbfItemId = 'application/x-s11/itemid'
        currentItemId = self.currentItemId()
        strData=self.model().table().tableName+':'
        if currentItemId:
            strData += str(currentItemId)
        return {cbfItemId:strData}

    def copy(self):
        dataList = self.prepareCopy()
        mimeData = QMimeData()
        for dataFormat, data in dataList.iteritems():
            v = toVariant(data)
            mimeData.setData(dataFormat, v.toByteArray())
        QtGui.qApp.clipboard().setMimeData(mimeData)

    def itemId(self, index):
        if index.isValid():
            row = index.row()
            itemIdList = self.model().idList()
            if row in xrange(len(itemIdList)):
                return itemIdList[row]
        return None

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            event.ignore()
        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            event.ignore()
        elif key == Qt.Key_Space:
            event.accept()
            self.emit(QtCore.SIGNAL('hide()'))
        elif event == QtGui.QKeySequence.Copy:
            event.accept()
            self.copy()
        else:
            super(CTableView, self).keyPressEvent(event)

    def contextMenuEvent(self, event): # event: QContextMenuEvent
        if self._popupMenu:
            self._popupMenu.exec_(event.globalPos())
            event.accept()
        else:
            event.ignore()

    def canRemoveRow(self, row):
        return self.model().canRemoveRow(row)

    def confirmRemoveRow(self, row, multiple=False):
        return self.model().confirmRemoveRow(self, row, multiple)

    def removeCurrentRow(self):
        def removeCurrentRowInternal():
            index = self.currentIndex()
            if index.isValid() and self.confirmRemoveRow(self.currentIndex().row()):
                row = self.currentIndex().row()
                self.model().removeRow(row)
                self.setCurrentRow(row)
        QtGui.qApp.call(self, removeCurrentRowInternal)

    def removeSelectedRows(self):
        def removeSelectedRowsInternal():
            currentRow = self.currentIndex().row()
            newSelection = []
            deletedCount = 0
            rows = self.selectedRowList()
            rows.sort()
            for row in rows:
                actualRow = row-deletedCount
                self.setCurrentRow(actualRow)
                confirm = self.confirmRemoveRow(actualRow, len(rows)>1)
                if confirm is None:
                    newSelection.extend(x-deletedCount for x in rows if x>row)
                    break
                if confirm:
                    self.model().removeRow(actualRow)
                    deletedCount += 1
                    if currentRow>row:
                        currentRow-=1
                else:
                    newSelection.append(actualRow)
            if newSelection:
                self.setSelectedRowList(newSelection)
            else:
                self.setCurrentRow(currentRow)
        QtGui.qApp.call(self, removeSelectedRowsInternal)
