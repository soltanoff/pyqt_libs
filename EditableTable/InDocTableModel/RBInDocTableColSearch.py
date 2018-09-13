# -*- coding: utf-8 -*-

class CRBInDocTableColSearch(CRBInDocTableCol):
    def __init__(self, title, fieldName, width, tableName, **params):
        CRBInDocTableCol.__init__(self, title, fieldName, width, tableName, **params)

    def createEditor(self, parent):
        editor = CRBComboBox(parent)
        editor.setRTF(self._isRTF)
        editor.setTable(self.tableName, addNone=self.addNone, filter=self.filter, order=self.order)
        editor.setShowFields(self.showFields)
        editor.setPrefferedWidth(self.prefferedWidth)
        return editor