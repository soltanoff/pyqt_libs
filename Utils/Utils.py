# -*- coding: UTF-8 -*-
from functools import wraps

UTILS_FUNCTION_RESULT_CACHE = dict()


# TODO: soltanoff: сделать проверку на использование в classmethod, поскольку ключ кеша формуриется странный.
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


if __name__ == '__main__':
    import time


    @timer
    @memorize
    def slowFunc(a, b):
        return a ** b


    print('First time exec: Result: %s' % (slowFunc(799999999, 999)))
    print('Second time exec: Result: %s' % slowFunc(799999999, 999))
    print('Other time exec: Result: %s' % slowFunc(1337, 1))
