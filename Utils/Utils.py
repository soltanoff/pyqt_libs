# -*- coding: UTF-8 -*-
from functools import wraps

UTILS_FUNCTION_RESULT_CACHE = dict()


# TODO: soltanoff: исключить из аргументов `self`
def memorize(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        cacheArgs = u'%s+%s+%s' % (func.func_name, args, kwargs)

        if cacheArgs in UTILS_FUNCTION_RESULT_CACHE:
            return UTILS_FUNCTION_RESULT_CACHE[cacheArgs]
        else:
            rv = func(*args, **kwargs)
            UTILS_FUNCTION_RESULT_CACHE[cacheArgs] = rv
            return rv

    return wrapper


def clearMemorizeCache():
    UTILS_FUNCTION_RESULT_CACHE.clear()


def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        startTime = time.time()
        result = func(*args, **kwargs)
        endTime = time.time() - startTime
        print('\nExec time: %s sec. ' % endTime)
        return result

    return wrapper


def compareCallStack(leftStack, rightStack, excludeLastCallFunctionName=None):
    u"""
    Сравнивает два стека
    :return: (common_elements, parent_flag)
        где common_elements - это количество первых одинаковых элементов обоих стеков
        parent_flag - это флаг наследования, принимающий значение
                      1, если функция левого стека является "родительской" для функции правого,
                      0, если стеки относятся к несвязанным функциям,
                      -1, если функция правого стека является "родительской" для функции левого
    """
    fullEqualityNumber = 0  # количество первых полностью схожих элементов стеков
    isInherit = 0

    if not (isinstance(leftStack, (list, tuple)) and isinstance(rightStack, (list, tuple))):
        return (fullEqualityNumber, isInherit)

    if not (leftStack and rightStack):
        return (fullEqualityNumber, isInherit)

    fileNameIdx = 0
    lineNumberIdx = 1
    callerIdx = 2
    calleesIdx = 3

    leftStackLength = len(leftStack)
    rightStackLength = len(rightStack)

    inheritanceDirection = 1
    if rightStackLength < leftStackLength:
        leftStackLength, rightStackLength = rightStackLength, leftStackLength
        leftStack, rightStack = rightStack, leftStack
        inheritanceDirection = -1

    if excludeLastCallFunctionName:
        leftStackLength -= 1

    for stackIdx in xrange(leftStackLength):
        isFileNameEquality = leftStack[stackIdx][fileNameIdx] == rightStack[stackIdx][fileNameIdx]
        if (isFileNameEquality
                and leftStack[stackIdx][lineNumberIdx] == rightStack[stackIdx][lineNumberIdx]
                and leftStack[stackIdx][callerIdx] == rightStack[stackIdx][callerIdx]
                and leftStack[stackIdx][calleesIdx] == rightStack[stackIdx][calleesIdx]):
            fullEqualityNumber += 1
        else:
            break

    isInherit = inheritanceDirection * (1 if fullEqualityNumber in [leftStackLength, leftStackLength - 1] else 0)

    return (fullEqualityNumber, isInherit)


if __name__ == '__main__':
    import time


    @timer
    @memorize
    def slowFunc(a, b):
        return a ** b


    print('First time exec: Result: %s' % (slowFunc(799999999, 999)))
    print('Second time exec: Result: %s' % slowFunc(799999999, 999))
    print('Other time exec: Result: %s' % slowFunc(1337, 1))
