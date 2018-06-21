# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore

from ExtendedTableView import CExtendedTableView
from TableModel.RichTextItemDelegate import CRichTextItemDelegate


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
