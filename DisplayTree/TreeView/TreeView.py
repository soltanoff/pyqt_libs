# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore


class CTreeView(QtGui.QTreeView):
    def __init__(self, parent):
        QtGui.QTreeView.__init__(self, parent)
        self._popupMenu = None
        self.collapseAll(True)

    def collapseAll(self, remember=True):
        if remember:
            self._treeDepth = 0
        QtGui.QTreeView.collapseAll(self)

    def createPopupMenu(self, actions=None):
        if actions is None:
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
        return self._popupMenu

    def popupMenuAboutToShow(self):
        raise NotImplementedError

    def contextMenuEvent(self, event):
        if self._popupMenu:
            self._popupMenu.exec_(event.globalPos())
            event.accept()
        else:
            event.ignore()

    def dragEnterEvent(self, event):
        for mimeType in self.model().mimeTypes():
            if event.mimeData().hasFormat(mimeType):
                event.acceptProposedAction()
                break
        super(CTreeView, self).dragEnterEvent(event)

    def dropEvent(self, event):
        index = self.indexAt(event.pos())
        if index.row() < 0:
            return
        for mimeType in self.model().mimeTypes():
            if event.mimeData().hasFormat(mimeType):
                self.model().dropMimeData(event.mimeData(), event.proposedAction(), index.row(), index.column(), index)
                self.selectionModel().emit(QtCore.SIGNAL('currentChanged(QModelIndex, QModelIndex)'),
                                           self.currentIndex(),
                                           self.currentIndex())
                break
            event.acceptProposedAction()
