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
