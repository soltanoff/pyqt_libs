# -*- coding: utf-8 -*-

from PyQt4.QtCore import *

from Utils.Forcing import forceString, forceStringEx, forceInt


def trim(s):
    return forceString(s).strip()


def nameCase(s):
    r = u''
    up = True
    for c in s:
        if c.isalpha():
            if up:
                r += c.upper()
                up = False
            else:
                r += c.lower()
        else:
            up = True
            r += c
    return r


def formatDate(val, toString=True):
    u"""
    Производит конвертацию даты из QDate в строку (при toString = True) или строку в QDate

    :param val: дата.
    :type val: QDate | QVariant | QString
    :param toString: указывает на направление конвертирования: True - из QDate в строку (по умол.), False - из строки в QDate)
    :return: дату в новом формате.
    :rtype: unicode | QDate
    """
    formatString = 'dd.MM.yyyy'
    if toString:
        if isinstance(val, QVariant):
            val = val.toDate()
        return unicode(val.toString(formatString))
    else:
        if isinstance(val, QVariant):
            val = val.toString()
        return QDate.fromString(val, formatString)


def formatTime(val):
    if isinstance(val, QVariant):
        val = val.toDate()
    return unicode(val.toString('H:mm'))


def formatDateTime(val):
    if isinstance(val, QVariant):
        val = val.toDateTime()
    return unicode(val.toString('dd.MM.yyyy H:mm'))


def formatNameInt(lastName, firstName, patrName):
    return trim(lastName + ' ' + firstName + ' ' + patrName)


def formatName(lastName, firstName, patrName):
    lastName = nameCase(forceStringEx(lastName))
    firstName = nameCase(forceStringEx(firstName))
    patrName = nameCase(forceStringEx(patrName))
    return formatNameInt(lastName, firstName, patrName)


def formatShortNameInt(lastName, firstName, patrName):
    return trim(
        lastName + ' ' + ((firstName[:1] + '.') if firstName else '') + ((patrName[:1] + '.') if patrName else ''))


def formatShortName(lastName, firstName, patrName):
    lastName = nameCase(forceStringEx(lastName))
    firstName = nameCase(forceStringEx(firstName))
    patrName = nameCase(forceStringEx(patrName))
    return formatShortNameInt(lastName, firstName, patrName)


def formatSex(sex):
    sex = forceInt(sex)
    if sex == 1:
        return u'М'
    elif sex == 2:
        return u'Ж'
    else:
        return u''


def databaseFormatSex(sex):
    sex = forceString(sex).upper()
    if sex == u'М':
        return 1
    elif sex == u'Ж':
        return 2
    else:
        return None


def formatSNILS(SNILS):
    if SNILS:
        s = forceString(SNILS) + ' ' * 14
        return s[0:3] + '-' + s[3:6] + '-' + s[6:9] + ' ' + s[9:11]
    else:
        return u''
