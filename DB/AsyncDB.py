# -*- coding: utf-8 -*-
from Queue import Queue

from PyQt4 import QtGui
from PyQt4.QtCore import QThread

from DB.connection import connectDataBaseByInfo


class AsyncDB:
    class Worker(QThread):
        def __init__(self, parent, connectionInfo, queue):
            QThread.__init__(self, parent)
            self.db = connectDataBaseByInfo(connectionInfo)
            self.queue = queue  # type: Queue

        def run(self):
            while True:
                stmt = self.queue.get()
                try:
                    self.db.query(stmt)
                except:
                    QtGui.qApp.logCurrentException()

        def stop(self):
            self.db.close()
            self.terminate()

    def __init__(self, connectionInfo):
        self.queue = Queue()
        self.worker = self.Worker(QtGui.qApp, connectionInfo, self.queue)
        self.worker.start()

    def __del__(self):
        self.worker.stop()

    def query(self, stmt):
        self.queue.put(stmt)
