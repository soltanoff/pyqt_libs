# -*- coding: utf-8 -*-
from PyQt4 import QtCore
from PyQt4.QtCore import QMimeData

from TableModel.TableModel import CTableModel
from Utils.Forcing import forceString


class CDragDropTableModel(CTableModel):
    def __init__(self, parent, cols=None, tableName=''):
        if cols is None:
            cols = []
        super(CDragDropTableModel, self).__init__(parent, cols, tableName)

    def flags(self, index):
        flags = super(CDragDropTableModel, self).flags(index)
        if index.isValid():
            return flags | QtCore.Qt.ItemIsDragEnabled
        return flags

    def mimeData(self, indexes):
        idList = set()
        for index in indexes:
            idList.add(forceString(self.idList()[index.row()]))

        mimeData = QMimeData()
        mimeData.setText(u','.join(idList))
        return mimeData
