# -*- coding: utf-8 -*-
from EditableTable.InDocTableModel.Col import CInDocTableCol
from Types.ComboBox import CComboBox
from Types.Enum import CEnumMeta
from Types.EnumComboBox import CEnumComboBox
from Utils.Forcing import forceInt, toVariant


class CEnumInDocTableCol(CInDocTableCol):
    u""" Столбец для отображения и редактирования поля, являющегося перечислением.
         Множество возможных значений задается списком, словарем или подклассом CEnum """

    def __init__(self, title, fieldName, width, values, **params):
        u"""
        :param title: заголовок
        :param fieldName: поле в QSqlRecord
        :param width: ширина
        :type values: list | dict | CEnumMeta
        :type params: dict """
        CInDocTableCol.__init__(self, title, fieldName, width, **params)
        self._addNone = params.get('addNone', False)
        self.values = values

    @property
    def isEnumClass(self):
        return isinstance(self.values, CEnumMeta)

    def toString(self, val, record):
        if self._addNone and val.isNull():
            return toVariant(u'Не задано')
        return toVariant(self.values[forceInt(val)])

    def createEditor(self, parent):
        if self.isEnumClass:
            editor = CEnumComboBox(parent)
            editor.setEnum(self.values, addNone=self._addNone)
            return editor

        editor = CComboBox(parent)
        if self._addNone:
            editor.addItem(u'Не задано', toVariant(None))
        for value, title in enumerate(self.values):
            editor.addItem(title, value)
        return editor

    def setEditorData(self, editor, value, record):
        if self.isEnumClass:
            editor.setValue(forceInt(value))
            return

        idx = editor.findData(value)
        if idx in xrange(editor.count()):
            editor.setCurrentIndex(forceInt(idx))

    def getEditorData(self, editor):
        if self.isEnumClass:
            return toVariant(editor.value())

        idx = editor.currentIndex()
        return editor.itemData(idx)
