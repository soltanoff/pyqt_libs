# -*- coding: utf-8 -*-
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

from Utils.Forcing import toVariant


class CTreeItem(object):
    def __init__(self, parent, name):
        self._parent = parent  # type: CTreeItem
        self._name = name
        self._items = None  # type: list[CTreeItem]

    def name(self):
        return self._name

    def child(self, row):
        items = self.items()
        if 0 <= row < len(items):
            return items[row]
        else:
            return None

    def childCount(self):
        return len(self.items())

    def isLeaf(self):
        return not bool(self.items())

    def columnCount(self):
        return 1

    def data(self, column):
        if column == 0:
            return toVariant(self._name)
        else:
            return QtCore.QVariant()

    def flags(self):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def parent(self):
        return self._parent

    def row(self):
        if self._parent and self._parent._items:
            return self._parent._items.index(self)
        return 0

    def items(self):
        if self._items is None:
            self._items = self.loadChildren()
        return self._items

    def update(self):
        self._items = self.loadChildren()

    def loadChildren(self):
        u""" :rtype: list[CTreeItem] """
        assert False, 'pure virtual call'

    def findItem(self, predicat):
        if predicat(self):
            return self
        for item in self.items():
            result = item.findItem(predicat)
            if result:
                return result
        return None

    def removeChildren(self):
        self._items = None
