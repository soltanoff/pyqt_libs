# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt, QVariant, QEvent, QRectF

from Utils.Forcing import forceInt


class CLocItemDelegate(QtGui.QStyledItemDelegate):
    def __init__(self, parent):
        QtGui.QStyledItemDelegate.__init__(self, parent)
        self.row = 0
        self.lastrow = 0
        self.column = 0
        self.editor = None

    def createEditor(self, parent, option, index):
        column = index.column()
        editor = index.model().createEditor(column, parent)
        self.connect(editor, QtCore.SIGNAL('commit()'), self.emitCommitData)
        self.connect(editor, QtCore.SIGNAL('editingFinished()'), self.commitAndCloseEditor)
        self.connect(editor, QtCore.SIGNAL('saveExtraData(QString, QString)'), self.saveExtraData)
        self.editor = editor
        self.row = index.row()
        self.rowcount = index.model().rowCount()
        self.column = column
        self._extraData = None
        self._extraField = None
        return editor

    def setEditorData(self, editor, index):
        if editor is not None:
            model = index.model()
            column = index.column()
            row = index.row()
            if row < len(model.items()):
                record = model.items()[row]
                value = model.data(index, Qt.EditRole)
            else:
                record = model.getEmptyRecord()
                value = record.value(index.model().cols()[column].fieldName())
            model.setEditorData(column, editor, value, record)

    def setModelData(self, editor, model, index):
        if editor is not None:
            column = index.column()
            editorData = index.model().getEditorData(column, editor)
            if self._extraField:
                model.setExtraData(self._extraField, self._extraData)
            model.setData(index, editorData)

    def emitCommitData(self):
        self.emit(QtCore.SIGNAL('commitData(QWidget *)'), self.sender())

    def commitAndCloseEditor(self):
        editor = self.sender()
        self.emit(QtCore.SIGNAL('commitData(QWidget *)'), editor)
        self.emit(QtCore.SIGNAL('closeEditor(QWidget *,QAbstractItemDelegate::EndEditHint)'), editor,
                  QtGui.QAbstractItemDelegate.NoHint)

    def editorEvent(self, event, model, option, index):
        flags = int(model.flags(index))
        checkableFlags = int(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        notCheckableFlags = (checkableFlags & flags) != checkableFlags
        if notCheckableFlags:
            return False

        value = index.data(Qt.CheckStateRole)
        if not value.isValid():
            return False

        editableFlags = int(Qt.ItemIsEnabled | Qt.ItemIsEditable)
        if (editableFlags & flags) == editableFlags:
            return QtGui.QStyledItemDelegate.editorEvent(self, event, model, option, index)

        state = QVariant(Qt.Unchecked if forceInt(value) == Qt.Checked else Qt.Checked)

        eventType = event.type()
        if eventType in [QEvent.MouseButtonRelease, QEvent.MouseButtonDblClick]:
            return model.setData(index, state, Qt.CheckStateRole)

        if eventType == QEvent.KeyPress:
            if event.key() in [Qt.Key_Space, Qt.Key_Select]:
                return model.setData(index, state, Qt.CheckStateRole)
        return QtGui.QStyledItemDelegate.editorEvent(self, event, model, option, index)

    def saveExtraData(self, fieldName, data):
        if fieldName:
            self._extraField = fieldName
            self._extraData = data

    def eventFilter(self, object, event):
        def editorCanEatTab():
            if isinstance(self.editor, QtGui.QDateEdit):
                return self.editor.currentSection() != QtGui.QDateTimeEdit.YearSection
            return False

        def editorCanEatBacktab():
            if isinstance(self.editor, QtGui.QDateEdit):
                return self.editor.currentSection() != QtGui.QDateTimeEdit.DaySection
            return False

        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Tab:
                if editorCanEatTab():
                    self.editor.keyPressEvent(event)
                    return True
                if self.editor is not None:
                    self.parent().commitData(self.editor)
                self.parent().keyPressEvent(event)
                return True
            elif event.key() == Qt.Key_Backtab:
                if editorCanEatBacktab():
                    self.editor.keyPressEvent(event)
                    return True
                if self.editor is not None:
                    self.parent().commitData(self.editor)
                self.parent().keyPressEvent(event)
                return True
        return QtGui.QStyledItemDelegate.eventFilter(self, object, event)

    def updateEditorGeometry(self, editor, option, index):
        QtGui.QStyledItemDelegate.updateEditorGeometry(self, editor, option, index)
        index.model().afterUpdateEditorGeometry(editor, index)

    # Функции, дублирующиеся с делегатом для CTableView
    def paint(self, painter, option, index):
        option = QtGui.QStyleOptionViewItemV4(option)
        self.initStyleOption(option, index)
        model = index.model()
        if hasattr(model, 'cols'):
            column = index.column()
            col = model.cols()[column]
            if col.isRTF():
                painter.save()
                doc = QtGui.QTextDocument()
                doc.setDefaultFont(option.font)
                doc.setHtml(option.text)
                option.text = ''  # model.data(index, Qt.DisplayRole).toString()
                option.widget.style().drawControl(QtGui.QStyle.CE_ItemViewItem, option, painter)
                painter.translate(option.rect.left(), option.rect.top())
                clip = QRectF(0, 0, option.rect.width(), option.rect.height())
                doc.drawContents(painter, clip)

                painter.restore()
                return
        return QtGui.QStyledItemDelegate.paint(self, painter, option, index)

    def sizeHint(self, option, index):
        option = QtGui.QStyleOptionViewItemV4(option)
        self.initStyleOption(option, index)
        model = index.model()
        if hasattr(model, 'cols'):
            column = index.column()
            col = model.cols()[column]
            if col.isRTF():
                doc = QtGui.QTextDocument()
                doc.setDefaultFont(option.font)
                doc.setHtml(option.text)
                doc.setTextWidth(option.rect.width())
                return QtCore.QSize(doc.idealWidth(), doc.size().height())
        return QtGui.QStyledItemDelegate.sizeHint(self, option, index)
