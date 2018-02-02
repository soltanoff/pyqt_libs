# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt, QVariant

from Utils.Forcing import forceStringEx, toVariant, forceRef, forceString


class CCol(object):
    """
      Root of all columns
    """
    alg = {
        'l': QVariant(Qt.AlignLeft + Qt.AlignVCenter),
        'c': QVariant(Qt.AlignHCenter + Qt.AlignVCenter),
        'r': QVariant(Qt.AlignRight + Qt.AlignVCenter),
        'j': QVariant(Qt.AlignJustify + Qt.AlignVCenter)
    }

    invalid = QVariant()

    def __init__(self, title, fields, defaultWidth, alignment, isRTF=False, **params):
        assert isinstance(fields, (list, tuple))
        self._title = QVariant(title)
        self._toolTip = CCol.invalid
        self._whatsThis = CCol.invalid
        self._fields = fields
        self._defaultWidth = defaultWidth
        self._align = CCol.alg[alignment] if isinstance(alignment, basestring) else alignment
        self._fieldindexes = []
        self._adopted = False
        self._isRTF = isRTF  # rich text - обрабатывать как форматированный текст
        self._enabled = params.get('enabled', True)
        self._visible = params.get('visible', True)
        self.color = None
        self._cacheDict = params.get('cache', {})

    def fieldName(self):
        return self._fields[0] if len(self._fields) else None

    def flags(self, index=None):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def valueType(self):
        return None

    def toString(self, val, record=None):
        return val

    def toCheckState(self, val, record=None):
        return QVariant()

    def isKeyInCache(self, key):
        return self._cacheDict.has_key(key)

    def getFromCache(self, key):
        return self._cacheDict[key]

    def putIntoCache(self, key, value):
        self._cacheDict[key] = value

    def format(self, values):
        id = forceStringEx(values[0])
        if not self.isKeyInCache(id):
            self.load(id)
        return toVariant(self.getFromCache(id))

    def load(self, id):
        self.putIntoCache(id, id)

    def clearCache(self):
        self._cacheDict.clear()

    def clearCacheById(self, id):
        if self.isKeyInCache(id):
            self._cacheDict.pop(id)

    @staticmethod
    def resolveValueByCaches(value, rules):
        for cache, fieldName in rules:
            itemId = forceRef(value)
            if not itemId:
                return CCol.invalid
            record = cache.get(itemId)
            if not record:
                return CCol.invalid
            value = record.value(fieldName)
        return value if value else CCol.invalid

    def adoptRecord(self, record):
        if record:
            self._fieldindexes = []
            if isinstance(self._fields, (list, tuple)):
                for fieldName in self._fields:
                    fieldIndex = record.indexOf(fieldName)
                    assert fieldIndex >= 0, fieldName
                    self._fieldindexes.append(fieldIndex)
            self._adopted = True

    def extractValuesFromRecord(self, record):
        if not self._adopted:
            self.adoptRecord(record)
        result = []
        if record:
            for i in self._fieldindexes:
                result.append(record.value(i))
        else:
            for i in self._fieldindexes:
                result.append(QVariant())
        result.append(record)
        return result

    def setTitle(self, title):
        self._title = toVariant(title)

    def title(self):
        return self._title

    def setToolTip(self, toolTip):
        self._toolTip = toVariant(toolTip)

    def toolTip(self):
        return self._toolTip

    def toolTipValue(self, values):
        return QVariant()

    def setWhatsThis(self, whatsThis):
        self._whatsThis = toVariant(whatsThis)

    def whatsThis(self):
        return self._whatsThis

    def fields(self):
        return self._fields

    def defaultWidth(self):
        return self._defaultWidth

    def alignment(self):
        return self._align

    def formatNative(self, values):
        u"""Столбец введен для возможности сортировки с учетом реального типа данных в столбце."""
        return forceStringEx(self.format(values))

    def checked(self, values):
        return CCol.invalid

    def getForegroundColor(self, values, record=None):
        return CCol.invalid

    def getBackgroundColor(self, values):
        return CCol.invalid

    def paintCell(self, values):
        val = self.color
        if val:
            colorName = forceString(val)
            if colorName:
                return QtCore.QVariant(QtGui.QColor(colorName))
        return CCol.invalid

    def getDecoration(self, values):
        return CCol.invalid

    def invalidateRecordsCache(self):
        pass

    def isRTF(self):
        return self._isRTF

    def isEnabled(self):
        return self._enabled

    def isVisible(self):
        return self._visible

    def setVisible(self, isVisible=True):
        self._visible = isVisible
