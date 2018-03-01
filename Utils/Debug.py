import datetime
import signal
import sys
import traceback

import Constants


def totalSeconds(td):
    u"""
    :type td: datetime.timedelta
    :rtype: float
    """
    return (td.microseconds + .0 + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6


# decorator for `exec_` or `query` methods
def printQueryTime(callStack=False, printQueryFirst=False):
    def decorator(query):
        def wrapper(self, stmt):
            if not (hasattr(Constants, 'DB_DEBUG') and Constants.DB_DEBUG):
                return query(self, stmt)

            if callStack:
                sys.__stdout__.write(u'\u2588' * 100 + u'\n')
            if printQueryFirst:
                sys.__stdout__.write(printableQuery(stmt))
                if callStack:
                    print '\n'
                    traceback.print_stack(file=sys.__stdout__)

            sys.__stdout__.write('\n')
            t1 = datetime.datetime.today()
            result = query(self, stmt)
            t2 = datetime.datetime.today()
            numRows = result.size() if result.isSelect() else result.numRowsAffected()
            if printQueryFirst:
                sys.__stdout__.write(
                    u'[%s][%6dms][%5d rows]' % (t1, totalSeconds(t2 - t1) * 1000.0, numRows)
                )
            else:
                sys.__stdout__.write(
                    u'[%s][%6dms][%5d rows]: %s' % (t1, totalSeconds(t2 - t1) * 1000.0, numRows, printableQuery(stmt))
                )
                if callStack:
                    print '\n'
                    traceback.print_stack()
            sys.__stdout__.write('\n\n')
            return result
        return wrapper
    return decorator


def logFunctionCalls():
    def trace(frame, event, arg):
        if event == 'call':
            traceback.print_stack(frame)
    sys.settrace(trace)


def catchSignal(signalType=signal.SIGSEGV):
    def catcher():
        traceback.print_stack()
        sys.exit()
    signal.signal(signalType, catcher)


def printableQuery(stmt):
    return u' '.join(u' '.join(line.split()) for line in unicode(stmt).splitlines() if line and not (line.lstrip().startswith(u'--') or line.lstrip().startswith(u'#')))
