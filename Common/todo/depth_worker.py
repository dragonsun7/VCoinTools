# -*- coding: utf-8 -*-
__author__ = 'Dragon Sun'


import threading
import time

DEPTH_STATUS_SUCCESS = 0
DEPTH_STATUS_DISCARD = 1


class DepthWorker(threading.Thread):

    # on_depth(worker, exchange_symbol, pair, asks, bids, status)
    def __init__(self, exchange, on_depth=None):
        threading.Thread.__init__(self)
        self.exchange = exchange
        self.on_depth = on_depth

    def run(self):
        while True:
            status = DEPTH_STATUS_SUCCESS
            asks, bids, elapsed = self.exchange.cale_elapsed(self.exchange.get_depth)
            if elapsed > DEPTH_DISCARD_INTERVAL:
                status = DEPTH_STATUS_DISCARD
            if self.on_depth is not None:
                self.on_depth(self, self.exchange.symbol, self.exchange.pair, asks, bids, status)
            time.sleep(DEPTH_INTERVAL)
