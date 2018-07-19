# -*- coding: utf-8 -*-
from DisplayTree.TreeModel.TreeItem import CTreeItem


class CTreeItemWithId(CTreeItem):
    def __init__(self, parent, name, itemId):
        CTreeItem.__init__(self, parent, name)
        self._id = itemId

    def id(self):
        return self._id

    def findItemId(self, itemId):
        if self._id == itemId:
            return self
        for item in self.items():
            result = item.findItemId(itemId)
            if result:
                return result
        return None

    def appendItemIds(self, l):
        if self._id:
            l.append(self._id)
        for item in self.items():
            item.appendItemIds(l)

    def getItemIdList(self):
        result = []
        self.appendItemIds(result)
        return result
