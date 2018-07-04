# -*- coding: utf-8 -*-
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

from TreeItem import CTreeItem


class CTreeModel(QtCore.QAbstractItemModel):
    def __init__(self, parent, rootItem):
        QtCore.QAbstractItemModel.__init__(self, parent)
        self._rootItem = rootItem  # type: CTreeItem
        self.rootItemVisible = True

    def setRootItem(self, rootItem):
        u""" :type rootItem: CTreeItem """
        self._rootItem = rootItem
        self.reset()

    def getRootItem(self):
        return self._rootItem

    def setRootItemVisible(self, val):
        self.rootItemVisible = val
        self.reset()

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 1

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if parent and parent.isValid():
            parentItem = parent.internalPointer()
            childItem = parentItem.child(row)
            return self.createIndex(row, column, childItem)
        elif self.rootItemVisible:
            return self.createIndex(0, 0, self.getRootItem())
        else:
            parentItem = self.getRootItem()
            childItem = parentItem.child(row)
            return self.createIndex(row, column, childItem)

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()
        childItem = index.internalPointer()
        return self.parentByItem(childItem)

    def parentByItem(self, childItem):
        parentItem = childItem.parent() if childItem else None
        if not parentItem or (parentItem == self.getRootItem() and not self.rootItemVisible):
            return QtCore.QModelIndex()
        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent=QtCore.QModelIndex()):
        if parent and parent.isValid():
            parentItem = parent.internalPointer()
            return parentItem.childCount() if 'childCount' in dir(parentItem) else 0
        elif self.rootItemVisible:
            return 1
        else:
            return self.getRootItem().childCount()

    def data(self, index, role):
        if index.isValid() and (role == QtCore.Qt.DisplayRole or role == QtCore.Qt.ToolTipRole):
            item = index.internalPointer()
            if item:
                return item.data(index.column())
        return QtCore.QVariant()

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        item = index.internalPointer()
        if not item:
            return Qt.NoItemFlags
        return item.flags()

    def findItem(self, predicat):
        item = self.getRootItem().findItem(predicat)
        return self.createIndex(item.row(), 0, item) if item else None

    # def findItemId(self, itemId):
    #     item = self.getRootItem().findItemId(itemId)
    #     if item and (self.rootItemVisible or item != self.getRootItem()):
    #         return self.createIndex(item.row(), 0, item)
    #     else:
    #         return None
    #
    # def getItemById(self, itemId):
    #     return self.getRootItem().findItemId(itemId)

    def getItemByIdEx(self, itemId):
        return self.getItemById(itemId)

    def itemId(self, index):
        item = index.internalPointer()
        return item._id if item else None

    def getItemIdList(self, index):
        result = []
        item = index.internalPointer()
        bool(item) and item.appendItemIds(result)
        return result

    def isLeaf(self, index):
        if not index.isValid():
            return False
        item = index.internalPointer()
        return item.isLeaf()

    def updateItem(self, index):
        item = index.internalPointer()
        bool(item) and item.update()

    # def updateItemById(self, itemId):
    #     item = self.getRootItem().findItemId(itemId)
    #     bool(item) and item.update()

    def emitDataChanged(self, group, row):
        index = self.createIndex(row, 0, group._items[row])
        self.emit(QtCore.SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
