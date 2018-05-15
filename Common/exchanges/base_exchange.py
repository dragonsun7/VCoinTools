# -*- coding: utf-8 -*-
__author__ = 'Dragon Sun'

import http
import ssl
import urllib3
import requests
from Common.base_class import *


# HTTP请求方法
HTTP_METHOD_GET = 'GET'
HTTP_METHOD_POST = 'POST'


class BaseExchange(BaseClass):

    # ---------------------------------------- 需要重载的方法 ---------------------------------------- #

    def __init__(self, api_key, secret_key, proxy_host=None, proxy_port=None):
        BaseClass.__init__(self)
        self.api_key = api_key
        self.secret_key = secret_key
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port

    # noinspection PyMethodMayBeStatic
    def symbol(self):
        """
        返回交易所标识
        :return: (str) 交易所标识
        """
        return ''

    # noinspection PyMethodMayBeStatic
    def get_depth(self, pair):
        """
        获取交易对的市场深度(盘口)
        离盘口越远，索引值越大，asks的价格越高，bids的价格越低
        :param pair: (str) 交易对
        :return: (list) asks, (list) bids，每个元素都为：[price, amount]
        """
        return [], []

    # noinspection PyMethodMayBeStatic
    def place_order(self, pair, trade_side, price, amount):
        """
        下单
        :param pair: (str) 交易对
        :param trade_side: (int) 交易方向 TRADE_SIDE_BUY/TRADE_SIDE_SELL
        :param price: (float) 价格
        :param amount: (float) 数量
        :return: (bool) result, (str) order_id, (int) err_code, (str) err_msg
        """
        return False, 0, 0, ''

    # noinspection PyMethodMayBeStatic
    def cancel_order(self, pair, order_id):
        """
        撤单
        :param pair: (str) 交易对
        :param order_id: (str) 订单ID
        :return: bool
        """
        return False

    # ---------------------------------------- 私有方法 ---------------------------------------- #

    # noinspection PyMethodMayBeStatic
    def _build_proxies(self):
        if (self.proxy_host is None) or (self.proxy_port is None):
            return None
        else:
            return {'https': 'http://{0}:{1}'.format(self.proxy_host, self.proxy_port)}

    # noinspection PyMethodMayBeStatic
    def request(self, method, url, params):
        proxies = self._build_proxies()
        if HTTP_METHOD_GET == method:
            try:
                return requests.get(url, params, proxies=proxies).json()
            except (
                    ssl.SSLEOFError, requests.exceptions.SSLError, urllib3.exceptions.MaxRetryError,
                    http.client.RemoteDisconnected, requests.exceptions.ProxyError
            ):
                return None
        else:
            try:
                return requests.post(url, params, proxies=proxies).json()
            except (
                    ssl.SSLEOFError, requests.exceptions.SSLError, urllib3.exceptions.MaxRetryError,
                    http.client.RemoteDisconnected, requests.exceptions.ProxyError
            ):
                return None
