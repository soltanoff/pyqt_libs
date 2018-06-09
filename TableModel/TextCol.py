# -*- coding: utf-8 -*-
from PyQt4.QtCore import QVariant

from TableModel.Col import CCol


class CTextCol(CCol):
    """
      General text column
    """

    def __init__(self, title, fields, defaultWidth, alignment='l', isRTF=False, toolTipValue=False, **kwargs):
        CCol.__init__(self, title, fields, defaultWidth, alignment, isRTF, **kwargs)
        self._toolTipValue = toolTipValue

    def toolTipValue(self, values):
        if self._toolTipValue:
            return self.format(values)
        return QVariant()
