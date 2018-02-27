# -*- coding: utf-8 -*-
from PyQt4 import QtCore

DB_DEBUG = False

# DATE
CURRENT_DATE = QtCore.QDate.currentDate(QtCore.QDate())
CURRENT_DATETIME = QtCore.QDateTime.currentDateTime(QtCore.QDateTime())
DATE_LEFT_INF = QtCore.QDate(2000, 1, 1)
DATE_RIGHT_INF = QtCore.QDate(2200, 1, 1)
DATETIME_LEFT_INF = QtCore.QDateTime(DATE_LEFT_INF)
DATETIME_RIGHT_INF = QtCore.QDateTime(DATE_RIGHT_INF)
