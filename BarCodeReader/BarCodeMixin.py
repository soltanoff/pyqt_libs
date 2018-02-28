# -*- coding: utf-8 -*-
from PyQt4 import QtGui

from BarCodeReader.BarCodeReaderThread import CBarCodeReaderThread
from Utils.Forcing import forceBool, getVal, forceString


class CBarCodeMixin(object):
    def enableBarCodeReader(
            self,
            busyByEvent=False,
            mode=CBarCodeReaderThread.omsMode,
            createNew=False,
            withoutSignals=False
    ):
        isBarCodeReaderEnable = forceBool(getVal(QtGui.qApp.preferences.appPrefs, 'BarCodeReaderEnable', False))
        scannerPort = forceString(getVal(QtGui.qApp.preferences.appPrefs, 'BarCodeReaderName', u"COM3"))
        if isBarCodeReaderEnable:
            if (not hasattr(QtGui.qApp, 'barCodethread') or createNew) or \
                    (hasattr(QtGui.qApp, 'barCodethread') and QtGui.qApp.barCodethread.isFinished()):
                self.disableBarCodeReader()
                QtGui.qApp.barCodethread = CBarCodeReaderThread(scannerPort)
                QtGui.qApp.barCodethread.start()

            if not withoutSignals:
                QtGui.qApp.barCodethread.barCodeReader.read.connect(self.barCodeResultHandler)
                QtGui.qApp.barCodethread.barCodeReader.error.connect(self.onBarcodeReaderError)
            QtGui.qApp.barCodethread.busyByEvent = busyByEvent
            QtGui.qApp.barCodethread.setFunc(mode)

    def disableBarCodeReader(self):
        if hasattr(QtGui.qApp, 'barCodethread'):
            try:
                QtGui.qApp.barCodethread.busyByEvent = False
                QtGui.qApp.barCodethread.disable()
                QtGui.qApp.barCodethread.exit()
            except:
                pass

    def barCodeResultHandler(self, result):
        if not QtGui.qApp.barCodethread.busyByEvent and result and self.isActiveWindow():
            if QtGui.qApp.barCodethread.mode == CBarCodeReaderThread.omsMode:
                self.readOMS(result)
            elif QtGui.qApp.barCodethread.mode == CBarCodeReaderThread.actionMode:
                self.setVerifiedAction(result)
            else:
                self.read(result)

    def readOMS(self, result):
        pass

    def setVerifiedAction(self, result):
        pass

    def read(self, result):
        pass

    def onBarcodeReaderError(self, message):
        if self.isActiveWindow():
            QtGui.QMessageBox.information(self, u'Внимание!', message, QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
