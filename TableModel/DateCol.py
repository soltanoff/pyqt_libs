# -*- coding: utf-8 -*-
import datetime

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QVariant

from TableModel.Col import CCol
from Utils.Forcing import pyDate, forceDate


class CDateCol(CCol):
    u"""
      Date column
    """

    def __init__(self, title, fields, defaultWidth, alignment='l', highlightRedDate=True, **kwargs):
        CCol.__init__(self, title, fields, defaultWidth, alignment, **kwargs)
        self.highlightRedDate = highlightRedDate and QtGui.qApp.highlightRedDate()

    def format(self, values):
        u"""Преобразует дату в строку в формате dd.mm.yy.
        Это не очень удобно. А если нужно иметь 4 цифры года? тогда не нужно тормозить - нужно почитать код..."""
        val = values[0]
        if val and val.type() in (QVariant.Date, QVariant.DateTime):
            val = val.toDate()
            return QVariant(val.toString(Qt.LocaleDate))
        return CCol.invalid

    def formatNative(self, values):
        val = values[0]
        if val and val.type() in (QVariant.Date, QVariant.DateTime):
            return pyDate(val.toDate())
        return datetime.date(datetime.MINYEAR, 1, 1)

    def getForegroundColor(self, values, record=None):
        val = values[0]
        date = forceDate(val)
        # TODO: soltanoff: fill color if thi is weekend
        if self.highlightRedDate and date:
            return QVariant(QtGui.QColor(255, 0, 0))
        return QVariant()

