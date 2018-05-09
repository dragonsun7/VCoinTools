# -*- coding: utf-8 -*-
__author__ = 'Dragon Sun'

import time
from PyQt5.QtCore import *


class OKExBaseWorker(QObject):
    success_signal = pyqtSignal()
    failure_signal = pyqtSignal()

    def __init__(self, exchange, model):
        QObject.__init__(self)
        self.exchange = exchange
        self.model = model


class OKExGetOrderHistoryWorker(OKExBaseWorker):

    def work(self):
        for pair in self.model.pairs:
            time.sleep(0.05)
            result = self.exchange.get_order_history(pair)
            if not result:
                self.failure_signal.emit()
                return
        self.success_signal.emit()
