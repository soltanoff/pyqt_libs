# -*- coding: utf-8 -*-
from PyQt4.QtCore import QVariant

from TableModel.TextCol import CTextCol
from Utils.Formating import nameCase


class CNameCol(CTextCol):
    u"""
        Name column: with appropriate capitalization
    """

    def __init__(self, title, fields, defaultWidth, alignment='l', isRTF=False, **kwargs):
        CTextCol.__init__(self, title, fields, defaultWidth, alignment, isRTF, **kwargs)

    def format(self, values):
        val = unicode(values[0].toString())
        return QVariant(nameCase(val))

    def formatNative(self, values):
        return nameCase(unicode(values[0].toString()))