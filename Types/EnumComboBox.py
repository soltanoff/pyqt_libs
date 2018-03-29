# -*- coding: utf-8 -*-
from PyQt4 import QtGui

from Types.EnumModel import CEnumModel


class CEnumComboBox(QtGui.QComboBox):
    def value(self):
        return self.model().getValue(self.currentIndex())

    def setValue(self, value):
        index = self.model().getValueIndex(value)
        if index is not None:
            self.setCurrentIndex(index)

    def setEnum(self, enumClass, keys=None, addNone=False, specialValues=None):
        self.setModel(CEnumModel(enumClass, keys=keys, addNone=addNone, specialValues=specialValues))
