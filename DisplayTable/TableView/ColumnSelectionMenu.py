# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore


class CTableColumnSelectionMenu(QtGui.QMenu):
    selectionChanged = QtCore.pyqtSignal(int, bool)

    def __init__(self, parent, columnNames, columnSelection):
        super(CTableColumnSelectionMenu, self).__init__(parent)

        self._columnActions = []
        for columnName, columnSelected in zip(columnNames, columnSelection):
            act = QtGui.QAction(columnName, self)  # , checkable=True, checked=columnSelected)
            self._columnActions.append(act)
            self.addAction(act)

        self.installEventFilter(self)

    def getColumnSelection(self):
        return [act.isChecked() for act in self._columnActions]

    def eventFilter(self, obj, evt):
        if evt.type() == QtCore.QEvent.MouseButtonRelease:
            if isinstance(obj, CTableColumnSelectionMenu):
                action = self.activeAction()
                if action:
                    action.trigger()
                    self.emitSelectionChanged(action)
                return True
        return False

    def emitSelectionChanged(self, action):
        try:
            idx = self._columnActions.index(action)
            self.selectionChanged.emit(idx, not action.isChecked())
        except ValueError:
            pass
