# -*- coding: utf-8 -*-
from PyQt4 import QtGui
from PyQt4.QtCore import Qt

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
