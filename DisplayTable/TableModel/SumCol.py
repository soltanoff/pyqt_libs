# -*- coding: utf-8 -*-
from PyQt4.QtCore import QLocale

from TableModel.NumCol import CNumCol
from Utils.Forcing import toVariant, forceDouble


class CSumCol(CNumCol):
    u"""
      Numeric column: right aligned, sum formatted
    """
    locale = QLocale()

    def format(self, values):
        sum = forceDouble(values[0])
        return toVariant(self.locale.toString(sum, 'f', 2))

    def formatNative(self, values):
        return forceDouble(values[0])
