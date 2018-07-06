# -*- coding: utf-8 -*-

from TableModel.Col import CCol


class CNumCol(CCol):
    u"""
      Numeric column: right aligned
    """

    def __init__(self, title, fields, defaultWidth, alignment='r', **kwargs):
        CCol.__init__(self, title, fields, defaultWidth, alignment, **kwargs)