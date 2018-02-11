# -*- coding: UTF-8 -*-
import collections

from PyQt4 import QtCore

# list of all threads created by the `CThread`class
IDLE_THREADS = []

# TODO: soltanoff: docstrings

class CThread(QtCore.QThread):
    global IDLE_THREADS
    ACTION_SETATTR = 0
    ACTION_CALL = 1
    ACTION_GETLIST = 2
    ACTION_GETDICT = 3

    def __init__(self, func):
        super(CThread, self).__init__()

        self.thr_func = func
        self.thr_stopFlag = False
        # FIXME: во-первых, сигналы стоит объявлять до использования: атрибут Класса (не объекта) __pyqtSignals__
        # FIXME: во-вторых, строковые сигналы - устаревший подход, вместо которого рекомендуется использовать QtCore.pyqtSignall()
        self.connect(
            self,
            QtCore.SIGNAL('fromMainThread(PyQt_PyObject, PyQt_PyObject)'),
            self._fromMainThread,
            QtCore.Qt.QueuedConnection
        )
        self.connect(
            self,
            QtCore.SIGNAL('fromMainThreadBlocking(PyQt_PyObject, PyQt_PyObject)'),
            self._fromMainThread,
            QtCore.Qt.BlockingQueuedConnection
        )
        self.connect(
            self,
            QtCore.SIGNAL('finished()'),
            self._removeThread
        )

    def run(self):
        self.thr_func(self, *self.thr_args)

    def __call__(self, instance, *args, **kwargs):
        self.thr_instance = instance
        self.thr_args = args

        if kwargs.get('thr_start'): self.start()

    def __getattr__(self, name):
        if name.startswith('thr_'): return self.__dict__[name]

        attr = self.thr_instance.__getattribute__(name)
        if callable(attr):
            self.thr_lastCallFunc = self.thr_instance.__class__.__dict__[name]
            return self._callFunc
        elif type(attr) in (list, dict):
            self.emit(
                QtCore.SIGNAL('fromMainThreadBlocking(PyQt_PyObject, PyQt_PyObject)'),
                self.ACTION_GETLIST if type(attr) == list else self.ACTION_GETDICT,
                name
            )
            return self.thr_result
        elif isinstance(attr, collections.Hashable):
            return attr
        else:
            raise (TypeError('unhashable type: %s' % type(attr).__name__))

    def __setattr__(self, name, value):
        if name.startswith('thr_'):
            self.__dict__[name] = value
        else:
            self.thr_instance.__setattr__(name, value)
            self.emit(
                QtCore.SIGNAL('fromMainThreadBlocking(PyQt_PyObject, PyQt_PyObject)'),
                self.ACTION_SETATTR,
                (name, value)
            )

    def _callFunc(self, *args, **kwargs):
        method = kwargs.get('thr_method')
        if not method:
            return self.thr_lastCallFunc(self, *args)
        if method == 'q':
            self.emit(
                QtCore.SIGNAL('fromMainThread(PyQt_PyObject, PyQt_PyObject)'),
                self.ACTION_CALL,
                (self.thr_lastCallFunc, args)
            )
            return
        if method == 'b':
            self.emit(
                QtCore.SIGNAL('fromMainThreadBlocking(PyQt_PyObject, PyQt_PyObject)'),
                self.ACTION_CALL,
                (self.thr_lastCallFunc, args)
            )
            return self.thr_result

    # FIXME: слот необходимо пердварять декоратором QtCore.pyqtSlot(<types>)
    def _fromMainThread(self, action, value):
        if action == self.ACTION_SETATTR:
            self.thr_instance.__setattr__(*value)
        elif action == self.ACTION_CALL:
            func, arg = value
            self.thr_result = func(self.thr_instance, *arg)
        elif action == self.ACTION_GETLIST:
            self.thr_result = self.thr_instance.__getattribute__(value)[:]
        elif action == self.ACTION_GETDICT:
            self.thr_result = self.thr_instance.__getattribute__(value).copy()

    def thr_stop(self):
        self.disconnect(
            self,
            QtCore.SIGNAL('fromMainThread(PyQt_PyObject, PyQt_PyObject)'),
            self._fromMainThread
        )
        self.disconnect(
            self,
            QtCore.SIGNAL('fromMainThreadBlocking(PyQt_PyObject, PyQt_PyObject)'),
            self._fromMainThread
        )
        self.thr_stopFlag = True

    def _removeThread(self):
        IDLE_THREADS.remove(self)


def threadIDLE(func):
    def wrapper(*args, **kwargs):
        global IDLE_THREADS
        thread = CThread(func)
        thread(*args, **kwargs)
        IDLE_THREADS.append(thread)
        return thread

    return wrapper


def closeThreads():
    for thread in IDLE_THREADS:
        thread.thr_stop()
    for thread in IDLE_THREADS:
        thread.wait()


def terminateThreads():
    for thread in IDLE_THREADS[:]:
        thread.terminate()


if __name__ == "__main__":
    import sys
    import time

    from PyQt4 import QtGui


    class Foo(QtGui.QLabel):
        def __init__(self, parent=None):
            QtGui.QLabel.__init__(self, parent)
            self.setFixedSize(320, 240)
            self.digits = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']

        @threadIDLE
        def bar(self, primaryText):
            rows = []
            digits = self.digits
            for item in digits:
                rows.append('%s: %s' % (primaryText, item))
                self.setText('\n'.join(rows), thr_method='b')
                time.sleep(0.5)

        def setText(self, text):
            QtGui.QLabel.setText(self, text)


    app = QtGui.QApplication(sys.argv)
    foo = Foo()
    foo.show()
    foo.bar('From thread', thr_start=True)
    app.exec_()
