# -*- coding: utf-8 -*-
import re
from PyQt4.QtCore import *

from Utils.Forcing import forceString, forceStringEx, forceInt

trim = lambda x: forceString(x).strip()


# TODO: soltanoff: странный метод... Нужно сделать проще, зачем так сложно?
def nameCase(text):
    result = u''
    up = True
    for symbol in text:
        if symbol.isalpha():
            if up:
                result += symbol.upper()
                up = False
            else:
                result += symbol.lower()
        else:
            up = True
            result += symbol
    return result


def isNameValid(name):
    return not re.search(r'''[0-9a-zA-Z`~!@#$%^&*_=+\\|{}[\];:"<>?/().,]''', forceStringEx(name))


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
        lastName + ' ' + ((firstName[:1] + '.') if firstName else '') + ((patrName[:1] + '.') if patrName else '')
    )


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


# FIXME: move to other file!
class ComparableMixin(object):
    def _compare_to(self, other):
        raise NotImplementedError(u'_compare_to() must be implemented by subclass')

    def __eq__(self, other):
        keys = self._compare_to(other)
        return keys[0] == keys[1] if keys else NotImplemented

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        keys = self._compare_to(other)
        return keys[0] < keys[1] if keys else NotImplemented

    def __le__(self, other):
        keys = self._compare_to(other)
        return keys[0] <= keys[1] if keys else NotImplemented

    def __gt__(self, other):
        keys = self._compare_to(other)
        return keys[0] > keys[1] if keys else NotImplemented

    def __ge__(self, other):
        keys = self._compare_to(other)
        return keys[0] >= keys[1] if keys else NotImplemented
   
