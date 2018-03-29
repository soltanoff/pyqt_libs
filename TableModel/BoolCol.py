# -*- coding: utf-8 -*-
from PyQt4.QtCore import Qt, QVariant

from TableModel.Col import CCol


class CBoolCol(CCol):
    u"""
      Boolean column
    """
    valChecked = QVariant(Qt.Checked)
    valUnchecked = QVariant(Qt.Unchecked)

    def __init__(self, title, fields, defaultWidth, alignment='c', **kwargs):
        CCol.__init__(self, title, fields, defaultWidth, alignment, **kwargs)

    def format(self, values):
        return CCol.invalid

    def checked(self, values):
        val = values[0]
        if val.toBool():
            return CBoolCol.valChecked
        else:
            return CBoolCol.valUnchecked

    def formatNative(self, values):
        return values[0].toBool()
