# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from PyQt4.QtCore import QVariant, QDate, QDateTime, QTime, QStringRef, QString

from Utils.Formating import formatDate, formatDateTime, formatTime


# TODO: soltanoff: let's go write a docstrings ! :3


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


getVal = lambda someDict, key, default: someDict.get(key, default)
forceBool = lambda x: x.toBool() if isinstance(x, QVariant) else bool(x)


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


def getFirstLexeme(sourceString):
    u"""
    Получение первой лексемы, т.е. группы однотипных символов (либо только числа, либо только не числа)
    :param sourceString: исходная строка для поиска
    :return: (lexeme, isDigit, stumpString)
    """
    isDigit = False
    lexeme = u''
    if sourceString:
        isDigit = sourceString[0].isdigit()
    for symbol in sourceString:
        # если тип очередного символа строки отличается от типа первого символа
        if symbol.isdigit() ^ isDigit:
            break  # прервать формирование токена
        lexeme += symbol
    return lexeme, isDigit, sourceString[len(lexeme):]


def naturalStringCompare(leftString, rightString):
    u"""
    Сравнивает строки путем естественного сравнения ('text1' < 'text2' < 'text11'),
    вместо лексографического ('text1' < 'text11' < 'text2'), выполняемого стандартными методами сранения.
    :param leftString: левый аргумент сравнения в виде строки (basestring или QString)
    :param rightString: правый аргумент сравнения в виде строки (basestring или QString)
    :return: отрицательное число, если leftString < rightString,
             ноль, если leftString = rightString,
             положительное, если leftString > rightString
    """
    leftString, rightString = forceString(leftString), forceString(rightString)

    if leftString == rightString:
        return 0

    while True:
        leftLexeme, leftIsDigit, leftString = getFirstLexeme(leftString)
        rightLexeme, rightIsDigit, rightString = getFirstLexeme(rightString)

        if leftIsDigit != rightIsDigit or not (leftLexeme and rightLexeme):
            return cmp(leftLexeme, rightLexeme)

        # сравниваем блоки, как числа, если они состоят из чисел, иначе, как строки
        partCompareResult = cmp(forceInt(leftLexeme), forceInt(rightLexeme)) \
            if leftIsDigit \
            else cmp(leftLexeme, rightLexeme)

        # если лексемы не равны, то считаем, что нашли результат, иначе пляшем дальше
        if partCompareResult:
            return partCompareResult

        return datetime.datetime.now()
    else:
        return datetime.datetime(datetime.MINYEAR, 1, 1)


def forcePyType(val):
    t = val.type()
    if t == QVariant.Bool:
        return val.toBool()
    elif t == QVariant.Date:
        return val.toDate()
    elif t == QVariant.DateTime:
        return val.toDateTime()
    elif t == QVariant.Double:
        return val.toDouble()[0]
    elif t == QVariant.Int:
        return val.toInt()[0]
    else:
        return unicode(val.toString())
