# -*- coding: utf-8 -*-
import datetime

from PyQt4 import QtCore, QtGui

from Utils.Forcing import forceString


class CBarCodeWorker(QtCore.QObject):
    read = QtCore.pyqtSignal(dict)
    error = QtCore.pyqtSignal(str)

    def __init__(self, port=u'COM3'):
        QtCore.QObject.__init__(self)
        self.port = port
        self.close = False
        self.func = lambda x: str(x)

    def readData(self):
        result = dict()
        try:
            import serial

            if hasattr(QtGui.qApp, 'barcodeSerialPort'): QtGui.qApp.barcodeSerialPort.close()
            QtGui.qApp.barcodeSerialPort = serial.Serial(self.port, 19200, timeout=1)

            while not self.close:
                message = bytearray('')
                i = 0
                while i < 60 and not self.close:
                    if QtGui.qApp.barcodeSerialPort.inWaiting() > 0:
                        while QtGui.qApp.barcodeSerialPort.inWaiting() > 0:
                            message.append(QtGui.qApp.barcodeSerialPort.read())
                    QtCore.QThread.msleep(50)
                    i += 1

                if message:
                    try:
                        self.read.emit(self.func(message))
                    except Exception as e:
                        result['errorMessage'] = u'Не удалось получить данные со считывателя штрих-кодов.'
                        self.error.emit(result['errorMessage'])

        except Exception as e:
            self.error.emit(
                u'СКАНЕР ШТРИХ-КОДОВ\n\n' +
                u'Ошибка при попытке подключения к сканеру\nОбратитесь к вашему системному администратору\n\n' +
                u'Текст ошибки:\n' + e.message)
        finally:
            if hasattr(QtGui.qApp, 'barcodeSerialPort') and QtGui.qApp.barcodeSerialPort:
                QtGui.qApp.barcodeSerialPort.close()

    @staticmethod
    def readActionBarCode(message):
        import re

        result = dict()
        message = str(message)
        result['action_id'] = re.findall('(\d+)\s', message)[0]
        result['amount'] = re.findall('\s(.*)', message)[0]
        result['errorMessage'] = u''
        return result

    @staticmethod
    def readOMSBarCode(message):
        sixBitEncoding = {
            0: u' ', 1: u'.', 2: u'-', 3: u'"', 4: u'0', 5: u'1', 6: u'2', 7: u'3',
            8: u'4', 9: u'5', 10: u'6', 11: u'7', 12: u'8', 13: u'9', 14: u'А', 15: u'Б',
            16: u'В', 17: u'Г', 18: u'Д', 19: u'Е', 20: u'Ё', 21: u'Ж', 22: u'З', 23: u'И',
            24: u'Й', 25: u'К', 26: u'Л', 27: u'М', 28: u'Н', 29: u'О', 30: u'П', 31: u'Р',
            32: u'С', 33: u'Т', 34: u'У', 35: u'Ф', 36: u'Х', 37: u'Ц', 38: u'Ч', 39: u'Ш',
            40: u'Щ', 41: u'Ь', 42: u'Ъ', 43: u'Ы', 44: u'Э', 45: u'Ю', 46: u'Я', 47: u' ',
            48: u' ', 49: u' ', 50: u' ', 51: u' ', 52: u' ', 53: u' ', 54: u' ', 55: u' ',
            56: u' ', 57: u' ', 58: u' ', 59: u' ', 60: u' ', 61: u' ', 62: u' ', 63: u'|',
        }

        polisN = 0
        for i in message[1:9]:
            polisN = (polisN << 8) | i

        name = u''
        pos = 0
        rest = 0
        for i in message[9:60]:
            posMod = pos % 3
            if posMod == 0:
                name += sixBitEncoding[(i >> 2)]
                rest = i & 0x03
            elif posMod == 1:
                name += sixBitEncoding[(rest << 4) | (i >> 4)]
                rest = i & 0x0F
            elif posMod == 2:
                name += sixBitEncoding[(rest << 2) | (i >> 6)]
                name += sixBitEncoding[(i & 0x3F)]
                rest = 0
            pos += 1

        sex = message[60]

        bDays = 0  # birthDate
        for i in message[61:63]:
            bDays = (bDays << 8) | i

        dateBeg = datetime.date(1900, 1, 1)
        bDate = dateBeg + datetime.timedelta(days=bDays)

        pDays = 0
        for i in message[63:65]:
            pDays = (pDays << 8) | i

        polisEndDate = dateBeg + datetime.timedelta(days=pDays)

        ecp = u''
        for i in message[65:131]:
            ecp += u'%02X' % i

        nameSplit = name.split('|')
        endDate = QtCore.QDate(polisEndDate) if datetime.date(1900, 1, 1) != polisEndDate else QtCore.QDate()
        result = dict()
        result['lastName'] = nameSplit[0].strip()
        result['firstName'] = nameSplit[1].strip()
        result['patrName'] = nameSplit[2].strip()
        result['sex'] = sex
        result['bDate'] = QtCore.QDate(bDate)  # birth date
        result['number'] = forceString(polisN)
        # duration (срок действия)
        result['endDate'] = endDate
        result['errorMessage'] = u''
        return result

    @staticmethod
    def defaultRead(message):
        return {'data': str(message)}
