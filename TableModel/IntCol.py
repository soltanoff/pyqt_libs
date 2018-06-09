# -*- coding: utf-8 -*-

from TableModel.Col import CCol
from Utils.Forcing import toVariant, forceInt


class CIntCol(CCol):
    u"""
      General int column
    """

    def __init__(self, title, fields, defaultWidth, alignment='l', **kwargs):
        CCol.__init__(self, title, fields, defaultWidth, alignment, **kwargs)

    def format(self, values):
        return toVariant(forceInt(values[0]))

    def formatNative(self, values):
        return forceInt(values[0])
