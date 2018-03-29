# -*- coding: utf-8 -*-
import datetime

from PyQt4.QtCore import Qt, QVariant

from TableModel.Col import CCol
from TableModel.DateCol import CDateCol
from Utils.Forcing import pyDate, pyDateTime


class CDateTimeCol(CDateCol):
    u"""
      Date and time column
    """

    def format(self, values):
        val = values[0]
        if val is not None:
            if val.type() == QVariant.Date:
                val = val.toDate()
                return QVariant(val.toString(Qt.LocaleDate))
            elif val.type() == QVariant.DateTime:
                val = val.toDateTime()
                return QVariant(val.toString(Qt.LocaleDate))
        return CCol.invalid

    def formatNative(self, values):
        val = values[0]
        if val.type() == QVariant.Date:
            return pyDate(val.toDate())
        elif val.type() == QVariant.DateTime:
            return pyDateTime(val.toDateTime())
        return datetime.datetime(datetime.MINYEAR, 1, 1)
