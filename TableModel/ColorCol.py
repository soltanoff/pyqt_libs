# -*- coding: utf-8 -*-
from PyQt4 import QtGui
from PyQt4.QtCore import QVariant

from TableModel.Col import CCol
from Utils.Forcing import forceString


class CColorCol(CCol):
    def getBackgroundColor(self, values):
        val = values[0]
        colorName = forceString(val)
        if colorName:
            return QVariant(QtGui.QColor(colorName))
        return CCol.invalid

    def format(self, values):
        return CCol.invalid
