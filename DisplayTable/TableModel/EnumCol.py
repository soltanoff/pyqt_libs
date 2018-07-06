# -*- coding: utf-8 -*-
from PyQt4.QtCore import QVariant

from TableModel.Col import CCol
from Types.Enum import CEnum
from Utils.Forcing import forceInt


class CEnumCol(CCol):
    u"""
      Enum column (like sex etc)
    """

    def __init__(self, title, fields, vallist, defaultWidth, alignment='l', notPresentValue=None):
        CCol.__init__(self, title, fields, defaultWidth, alignment)
        self._vallist = vallist.nameMap if isinstance(vallist, type) and issubclass(vallist, CEnum) else vallist
        self._notPresentValue = notPresentValue

    def format(self, values):
        val = values[0]
        val_int, ok = val.toInt()
        i = val_int if ok else None
        if isinstance(self._vallist, dict):
            if i not in self._vallist:
                return QVariant('{%s}' % val.toString() if self._notPresentValue is None else self._notPresentValue)
            else:
                return QVariant(self._vallist[i])
        elif 0 <= i < len(self._vallist):
            return QVariant(self._vallist[i])
        else:
            return QVariant('{%s}' % val.toString() if self._notPresentValue is None else self._notPresentValue)

    def formatNative(self, values):
        val = values[0]
        i = forceInt(val)
        try:
            return self._vallist[i]
        except (IndexError, KeyError):
            return '{%s}' % val.toString()
