# -*- coding: utf-8 -*-
__author__ = 'Dragon Sun'

import importlib
from exchanges.depth_worker import *


class ExchangeMgr:

    def __init__(self, exchanges, on_depth=None):
        self.exchanges = exchanges
        self.on_depth = on_depth
        self.depth_workers = []

    @classmethod
    def factory(cls, exchange_symbol, username, pair):
        module_name = 'exchanges.{0}'.format(exchange_symbol.lower())
        class_name = '{0}Exchange'.format(exchange_symbol)
        module = importlib.import_module(module_name)
        a_class = getattr(module, class_name)
        instance = a_class(username, pair)
        return instance

    def start_depth(self):
        for exchange in self.exchanges:
            worker = DepthWorker(exchange, self.on_depth)
            worker.start()
