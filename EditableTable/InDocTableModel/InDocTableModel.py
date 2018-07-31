# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtSql, QtGui
from PyQt4.QtCore import Qt, QVariant

from Utils.Forcing import toVariant, forcePyType, forceStringEx
from Utils.Formating import trim


class CInDocTableCol(object):
    alg = {
        'l': QVariant(Qt.AlignLeft + Qt.AlignVCenter),
        'c': QVariant(Qt.AlignHCenter + Qt.AlignVCenter),
        'r': QVariant(Qt.AlignRight + Qt.AlignVCenter),
        'j': QVariant(Qt.AlignJustify + Qt.AlignVCenter)
    }

    # Поле БД с созданием соответствующего виджета для редактирования
    def __init__(self, title, fieldName, width, **params):
        self._title = toVariant(title)
        self._fieldName = fieldName
        self._width = width
        self._toolTip = toVariant(params.get('toolTip', None))
        self._whatsThis = toVariant(params.get('whatThis', None))
        self._external = params.get('external', False)
        self._valueType = params.get('valueType', None)
        self._readOnly = params.get('readOnly', False)
        self._maxLength = params.get('maxLength', None)
        self._inputMask = params.get('inputMask', None)
        self._sortable = params.get('sortable', False)
        self._decsSortToAscById = params.get('decsSortToAscById', False)
        self._useNaturalStringCompare = params.get('naturalStringCompare', True)
        self._alignmentChar = params.get('alignment', 'l')
        self._isVisible = params.get('isVisible', True)
        self._isRTF = params.get('isRTF', False)
        self._completerModel = None
        self._completer = None
        self._completerCode = None

    def setCompleter(self, tableName=None, fieldName=u'name', completerCode=None):
        if tableName:
            self._completerModel = QtSql.QSqlTableModel(None, QtSql.QSqlDatabase.database('vistamed'))
            self._completerModel.setTable(tableName)
            self._completerCode = completerCode
            if completerCode:
                self._completerModel.setFilter("code like '%s'" % completerCode)
            self._completer = QtGui.QCompleter()
            self._completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
            self._completer.setCompletionMode(QtGui.QCompleter.PopupCompletion)

            self._completer.setCompletionColumn(max(0, self._completerModel.fieldIndex(fieldName)))
        else:
            self._completerModel = None
            self._completer = None

    def setTitle(self, title):
        self._title = toVariant(title)

    def title(self):
        return self._title

    def setToolTip(self, toolTip):
        self._toolTip = toVariant(toolTip)
        return self

    def toolTip(self):
        return self._toolTip

    def setWhatsThis(self, whatsThis):
        self._whatsThis = toVariant(whatsThis)
        return self

    def whatsThis(self):
        return self._whatsThis

    def fieldName(self):
        return self._fieldName

    def width(self):
        return self._width
