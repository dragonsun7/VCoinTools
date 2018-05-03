# -*- coding: utf-8 -*-
__author__ = 'Dragon Sun'


from Common.exchanges.base_exchange import *


class HuobiExchange(BaseExchange):

    def __init__(self, username, pair, api_key, secret_key, conf=None):
        BaseExchange.__init__(self, username, pair, api_key, secret_key, conf)

    def use_proxy(self):
        return True

    def symbol(self):
        return 'Huobi'

    def convert_pair(self, pair):
        return str(pair).replace('_', '')

    def get_depth(self):
        url = 'https://api.huobipro.com/market/depth'
        params = {
            'symbol': self.pair.lower(),
            'type': 'step1'
        }

        json = self.request(HTTP_METHOD_GET, url, params)
        if json['status'] != 'ok':
            return [], []
        asks = json['tick']['asks']
        bids = json['tick']['bids']
        return asks, bids
