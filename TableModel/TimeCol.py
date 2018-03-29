# -*- coding: utf-8 -*-
import datetime

from PyQt4.QtCore import Qt, QVariant

from TableModel.Col import CCol


class CTimeCol(CCol):
    u"""
      Time column
    """

    def __init__(self, title, fields, defaultWidth, alignment='l', **kwargs):
        CCol.__init__(self, title, fields, defaultWidth, alignment, **kwargs)

    def format(self, values):
        val = values[0]
        if val.type() in (QVariant.Time, QVariant.DateTime):
            val = val.toTime()
            return QVariant(val.toString(Qt.SystemLocaleShortDate))
        return CCol.invalid

    def formatNative(self, values):
        val = values[0]
        if val and val.type() in (QVariant.Time, QVariant.DateTime):
            return pyTime(val.toTime())
        return datetime.time()
