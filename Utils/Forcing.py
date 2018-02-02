# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from PyQt4.QtCore import QVariant, QDate, QDateTime, QTime, QStringRef, QString

from Utils.Formating import formatDate, formatDateTime, formatTime


def toVariant(v):
    if v is None:
        return QVariant()
    t = type(v)
    if t == QVariant:
        return v
    elif t == datetime.time:
        return QVariant(QTime(v))
    elif t == datetime.datetime:
        return QVariant(QDateTime(v))
    elif t == datetime.date:
        return QVariant(QDate(v))
    elif t == Decimal:
        return QVariant(unicode(v))
    else:
        return QVariant(v)


def forceBool(val):
    if isinstance(val, QVariant):
        return val.toBool()
    return bool(val)


def forceDate(val):
    if isinstance(val, QVariant):
        return val.toDate()
    if isinstance(val, QDate):
        return val
    if isinstance(val, QDateTime):
        return val.date()
    if val is None:
        return QDate()
    return QDate(val)


def forceTime(val):
    if isinstance(val, QVariant):
        return val.toTime()
    if isinstance(val, QTime):
        return val
    if isinstance(val, QDateTime):
        return val.time()
    if val is None:
        return QTime()
    return QTime(val)


def forceDateTime(val):
    if isinstance(val, QVariant):
        return val.toDateTime()
    if isinstance(val, QDateTime):
        return val
    if isinstance(val, QDate):
        return QDateTime(val, QTime())
    if isinstance(val, QTime):
        return QDateTime(QDate(), val)
    if val is None:
        return QDateTime()
    return QDateTime(val)


def forceDateTuple(val):
    u"""
    Раньше использовалось, потому что так понимал SOAP. Предполагается, что новый формат SOAP
    тоже будет нормально понимать. Собственно, теперь возвращает не tuple и надо будет починить попозже имя

    :type val: PyQt4.QtCore.QVariant
    :rtype: str
    """
    dt = forceDateTime(val)
    if dt == QDateTime():
        return None

    result = str(dt.toString('yyyy-MM-ddThh:mm:ss'))
    return result if result else None


def forceInt(val):
    u""" :rtype: int """
    if isinstance(val, QVariant):
        return val.toInt()[0]
    elif ((val is None)  # Если пустое значение
          or (isinstance(val, QString) and not val.toInt()[1])  # Если нечисловой QString
          or isinstance(val, basestring) and not val.isdigit()):  # Если нечисловая строка
        return 0
    return int(val)


def forceLong(val):
    u""" :rtype: long """
    if isinstance(val, QVariant):
        return val.toLongLong()[0]
    elif val is None:
        return 0L
    return long(val)


def forceRef(val):
    u""" :rtype: int | None """
    if isinstance(val, QVariant):
        if val.isNull():
            val = None
        else:
            val = int(val.toULongLong()[0])
            if val == 0:
                val = None
    return val


def forceString(val):
    u""" :rtype: unicode """
    if isinstance(val, QVariant):
        valType = val.type()
        if valType == QVariant.Date:
            return formatDate(val.toDate())
        elif valType == QVariant.DateTime:
            return formatDateTime(val.toDateTime())
        elif valType == QVariant.Time:
            return formatTime(val.toTime())
        else:
            val = val.toString()
    if isinstance(val, QDate):
        return formatDate(val)
    if isinstance(val, QDateTime):
        return formatDateTime(val)
    if isinstance(val, QTime):
        return formatTime(val)
    if val is None:
        return u''
    if isinstance(val, QStringRef):
        val = val.toString()
    return unicode(val)


def forceStringEx(val):
    return forceString(val).strip()


def forceDouble(val):
    if isinstance(val, QVariant):
        return val.toDouble()[0]
    elif not val:
        return float(0)
    else:
        return float(val)


def forceDecimal(val):
    if isinstance(val, QVariant):
        res = unicode(val.toString())
        return Decimal(res) if res != u'' else Decimal(0)
    elif not val:
        return Decimal('0.0')
    elif isinstance(val, float):
        return Decimal(unicode(val))
    else:
        return Decimal(val)


def forceMoneyRepr(val):
    return u"%.2f" % forceDouble(val)


def forcePrettyDouble(val, digits=2):
    return round(forceDouble(val), digits)


def formatBool(val):
    if forceBool(val):
        return u'да'
    else:
        return u'нет'


def pyDate(date):
    if date and date.isValid():
        return date.toPyDate()
    else:
        return datetime.date(datetime.MINYEAR, 1, 1)


def pyTime(time):
    if time and time.isValid():
        return time.toPyTime()
    else:
        return datetime.time()


def pyDateTime(dateTime):
    if dateTime and dateTime.isValid():
        if isinstance(dateTime, QDate):
            dateTime = QDateTime(dateTime)
        return dateTime.toPyDateTime()
    else:
        return datetime.datetime(datetime.MINYEAR, 1, 1)
