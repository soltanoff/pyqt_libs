# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QRectF


class CRichTextItemDelegate(QtGui.QStyledItemDelegate):
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
