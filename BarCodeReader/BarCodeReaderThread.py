# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui

from BarCodeReader.BarCodeWorker import CBarCodeWorker


class CBarCodeReaderThread(QtCore.QThread):
    omsMode = 'oms'
    actionMode = 'action'
    defaultMode = 'default'

    availableModes = {
        omsMode: CBarCodeWorker.readOMSBarCode,
        actionMode: CBarCodeWorker.readActionBarCode,
        defaultMode: CBarCodeWorker.defaultRead,
    }

    def __init__(self, port=u'COM3', mode='oms'):
        QtCore.QThread.__init__(self)
        self.barCodeReader = CBarCodeWorker(port)
        self.barCodeReader.moveToThread(self)
        self.busyByEvent = False
        self.mode = mode

    def disable(self):
        self.barCodeReader.close = True
        try:
            QtGui.qApp.barcodeSerialPort.close()
        except Exception as e:
            print('[CBarCodeReaderThread]: %s' % e)

    def setFunc(self, mode):
        self.mode = mode
        self.barCodeReader.func = self.availableModes.get(mode, self.availableModes[self.defaultMode])

    def run(self):
        self.setFunc(self.mode)
        self.barCodeReader.readData()
