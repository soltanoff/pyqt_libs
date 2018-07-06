# -*- coding: utf-8 -*-

from TableModel.Col import CCol
from Utils.Forcing import toVariant, forceDecimal


class CDecimalCol(CCol):
    u"""
        General Decimal column
    """

    def __init__(self, title, fields, defaultWidth, alignment='l', **kwargs):
        CCol.__init__(self, title, fields, defaultWidth, alignment, **kwargs)

    def format(self, values):
        return toVariant(forceDecimal(values[0]))

    def formatNative(self, values):
        return forceDecimal(values[0])
