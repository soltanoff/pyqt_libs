# -*- coding: utf-8 -*-
from PyQt4 import QtGui


class CInDocTableView(QtGui.QTableView):
    __pyqtSignals__ = ('editInProgress(bool)',
                       )
    MAX_COLS_SIZE = 350
    MIN_COLS_SIZE = 72

    def __init__(self, parent):
        QtGui.QTableView.__init__(self, parent)
        self._popupMenu = None

        h = self.fontMetrics().height()
        self.verticalHeader().setDefaultSectionSize(3 * h / 2)
        self.verticalHeader().hide()

        self.setShowGrid(True)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)
