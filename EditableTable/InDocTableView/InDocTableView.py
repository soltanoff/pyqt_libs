# -*- coding: utf-8 -*-
from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QModelIndex
from PyQt4.QtGui import QTableWidgetItem, QAbstractItemView

from EditableTable.InDocTableModel.LocItemDelegate import CLocItemDelegate


class CInDocTableView(QtGui.QTableView):
    __pyqtSignals__ = ('editInProgress(bool)',
                       )
    MAX_COLS_SIZE = 350
    MIN_COLS_SIZE = 72

    def __init__(self, parent):
        QtGui.QTableView.__init__(self, parent)
        self.__actUpRow = None
        self.__actDownRow = None
        self.__actDeleteRows = None
        self.__actSelectAllRow = None
        self.__actSelectRowsByData = None
        self.__actDuplicateCurrentRow = None
        self.__actAddFromReportRow = None
        self.__actDuplicateSelectRows = None
        self.__actClearSelectionRow = None
        self.__actRecordProperties = None
        self.__sortColumn = None
        self.__sortAscending = False
        self.__delRowsChecker = None

        self._popupMenu = None

        self.rbTable = None
        self.isCloseDate = False

        self.verticalHeader().setDefaultSectionSize(3 * self.fontMetrics().height() / 2)
        self.verticalHeader().hide()

        self.setHorizontalScrollMode(self.ScrollPerPixel)
        self.setVerticalScrollMode(self.ScrollPerPixel)

        self.setShowGrid(True)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)
        self.setItemDelegate(CLocItemDelegate(self))
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().sectionClicked[int].connect(self.enableSorting)
        self.setTabKeyNavigation(True)
        self.setEditTriggers(
            QtGui.QAbstractItemView.AnyKeyPressed |
            QtGui.QAbstractItemView.EditKeyPressed |
            QtGui.QAbstractItemView.SelectedClicked |
            QtGui.QAbstractItemView.DoubleClicked
        )
        self.setFocusPolicy(Qt.StrongFocus)

    def dropEvent(self, event):
        if event.source() == self \
                and (event.dropAction() == Qt.MoveAction or self.dragDropMode() == QAbstractItemView.InternalMove):
            success, row, col, topIndex = self.dropOn(event)
            if success:
                selRows = self.getSelectedRowsFast()
                top = selRows[0]
                dropRow = row
                if dropRow == -1:
                    dropRow = self.rowCount()
                offset = dropRow - top

                for i, row in enumerate(selRows):
                    r = row + offset
                    if r > self.rowCount() or r < 0:
                        r = 0
                    self.insertRow(r)

                selRows = self.getSelectedRowsFast()
                top = selRows[0]
                offset = dropRow - top
                for i, row in enumerate(selRows):
                    r = row + offset
                    if r > self.rowCount() or r < 0:
                        r = 0

                    for j in range(self.columnCount()):
                        source = QTableWidgetItem(self.item(row, j))
                        self.setItem(r, j, source)
                event.accept()
        else:
            QtGui.QTableView.dropEvent(event)

    def getSelectedRowsFast(self):
        selRows = []
        for item in self.selectedItems():
            if item.row() not in selRows:
                selRows.append(item.row())
        return selRows

    def droppingOnItself(self, event, index):
        dropAction = event.dropAction()

        if self.dragDropMode() == QAbstractItemView.InternalMove:
            dropAction = Qt.MoveAction

        if event.source() == self and event.possibleActions() & Qt.MoveAction and dropAction == Qt.MoveAction:
            selectedIndexes = self.selectedIndexes()
            child = index
            while child.isValid() and child != self.rootIndex():
                if child in selectedIndexes:
                    return True
                child = child.parent()

        return False

    def dropOn(self, event):
        if event.isAccepted():
            return False, None, None, None

        index = QModelIndex()
        row = -1
        col = -1

        if self.viewport().rect().contains(event.pos()):
            index = self.indexAt(event.pos())
            if not index.isValid() or not self.visualRect(index).contains(event.pos()):
                index = self.rootIndex()

        if self.model().supportedDropActions() & event.dropAction():
            if index != self.rootIndex():
                dropIndicatorPosition = self.position(event.pos(), self.visualRect(index), index)
                if dropIndicatorPosition == QAbstractItemView.AboveItem:
                    row = index.row()
                    col = index.column()
                elif dropIndicatorPosition == QAbstractItemView.BelowItem:
                    row = index.row() + 1
                    col = index.column()
                else:
                    row = index.row()
                    col = index.column()

            if not self.droppingOnItself(event, index):
                return True, row, col, index

        return False, None, None, None

    def position(self, pos, rect, index):
        r = QAbstractItemView.OnViewport
        margin = 2
        if pos.y() - rect.top() < margin:
            r = QAbstractItemView.AboveItem
        elif rect.bottom() - pos.y() < margin:
            r = QAbstractItemView.BelowItem
        elif rect.contains(pos, True):
            r = QAbstractItemView.OnItem
        if r == QAbstractItemView.OnItem and not (self.model().flags(index) & Qt.ItemIsDropEnabled):
            r = QAbstractItemView.AboveItem if pos.y() < rect.center().y() else QAbstractItemView.BelowItem
        return r
