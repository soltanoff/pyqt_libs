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

    def setExternal(self, external):
        # Внешняя колонка есть в таблице БД, но не хранится в модели
        self._external = external

    def external(self):
        # Внешняя колонка есть в таблице БД, но не хранится в модели
        # Может наоборот: не хранится в БД, но есть в модели
        return self._external

    def setValueType(self, valueType):
        self._valueType = valueType

    def valueType(self):
        return self._valueType

    def setReadOnly(self, readOnly=True):
        self._readOnly = readOnly
        return self

    def readOnly(self):
        return self._readOnly

    def setSortable(self, value=True):
        self._sortable = value
        return self

    def sortable(self):
        return self._sortable

    def decsSortToAscById(self):
        return self._decsSortToAscById

    def useNaturalStringCompare(self):
        return self._useNaturalStringCompare

    def flags(self, index=None):
        result = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if not self._readOnly:
            result |= Qt.ItemIsEditable
        return result

    def toString(self, val, record):
        # строковое представление (тип - QVariant!)
        return val

    def toSortString(self, val, record):
        return forcePyType(self.toString(val, record))

    def toStatusTip(self, val, record):
        return self.toString(val, record)

    def toCheckState(self, val, record):
        return QVariant()

    def getForegroundColor(self, val, record):
        return QVariant()

    def getBackgroundColor(self, val, record):
        return QVariant()

    def createEditor(self, parent):
        editor = QtGui.QLineEdit(parent)
        if self._completer is not None and self._completerModel.select():
            self._completer.setModel(self._completerModel)
            editor.setCompleter(self._completer)
        if self._maxLength:
            editor.setMaxLength(self._maxLength)
        if self._inputMask:
            editor.setInputMask(self._inputMask)
        return editor

    def setEditorData(self, editor, value, record):
        editor.setText(forceStringEx(value))

    def getEditorData(self, editor):
        """
        Получить значение из редактора.

        :param editor: редактор, значение из которого необходимо получить.
        :type editor: QVariant
        :return:
        """
        text = trim(editor.text())
        if text:
            if self._completer:
                variantText = QtCore.QVariant(text)
                completionColumn = self._completer.completionColumn()
                startIndex = self._completerModel.index(0,
                                                        completionColumn)
                if not self._completerModel.match(startIndex,
                                                  QtCore.Qt.DisplayRole,
                                                  variantText):
                    db = QtGui.qApp.db
                    completerTable = db.table('rbTextDataCompleter')
                    newRecord = completerTable.newRecord()
                    if newRecord.contains(u'code') and self._completerCode is not None:
                        newRecord.setValue(u'code', QtCore.QVariant(self._completerCode))
                    newRecord.setValue(self._completer.completionColumn(), variantText)
                    db.insertRecord(completerTable, newRecord)
            return toVariant(text)
        else:
            return QVariant()

    def isRTF(self):
        return self._isRTF

    def isVisible(self):
        return self._isVisible

    def saveExternalData(self, rowRecord):
        """
        Сохраняет внешние данные, с которыми работает столбец, используя переданный экземпляр QSqlRecord строки.
        Необходимо для работы столбцов, которые обеспечивают доступ к данным из других таблиц (связь 1:1 или даже 1:М).

        :param rowRecord: экземпляр QSqlRecord-строки, для которой требуется сохранить внешние данные.
        """
        pass

    def alignment(self):
        return CInDocTableCol.alg[self._alignmentChar]
