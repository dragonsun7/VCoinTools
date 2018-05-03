# -*- coding: utf-8 -*-
__author__ = 'Dragon Sun'


import re
import json
import hashlib

from Common.exchanges.websocket_exchange import *
from Common.models.base_model import *


# Websocket订阅频道类型
WS_CHANNEL_TYPE_TICKER = 0  # 行情
WS_CHANNEL_TYPE_DEPTH = 1  # 市场深度
WS_CHANNEL_TYPE_DEALS = 2  # 交易记录
WS_CHANNEL_TYPE_ORDER = 3  # 订单
WS_CHANNEL_TYPE_BALANCE = 4  # 余额
WS_CHANNEL_TYPE_KLINE = 5  # K线

# K线类型
KLINE_TYPE_MIN01 = 0
KLINE_TYPE_MIN03 = 1
KLINE_TYPE_MIN05 = 2
KLINE_TYPE_MIN15 = 3
KLINE_TYPE_MIN30 = 4
KLINE_TYPE_HOUR01 = 5
KLINE_TYPE_HOUR02 = 6
KLINE_TYPE_HOUR04 = 7
KLINE_TYPE_HOUR06 = 8
KLINE_TYPE_HOUR12 = 9
KLINE_TYPE_DAY = 10
KLINE_TYPE_WEEK = 11

# 交易方向
TRADE_SIDE_BUY = 1
TRADE_SIDE_SELL = 2

# 订单状态
ORDER_RECALL = -1  # 撤销
ORDER_OPEN = 0  # 未成交
ORDER_PART = 1  # 部分成交
ORDER_CLOSE = 2  # 已成交


class OKExWebsocketExchange(WebsocketExchange):

    on_subscribe_signal = QtCore.pyqtSignal(str)  # 交易对订阅成功，参数为交易对
    on_all_subscribe_signal = QtCore.pyqtSignal()  # 所有交易对订阅成功
    on_ticker_signal = QtCore.pyqtSignal(str)  # 市场行情数据更新，参数为交易对
    on_depth_signal = QtCore.pyqtSignal(str)  # 市场深度数据更新，参数为交易对

    def __init__(self, model: BaseModel, url, proxy_host=None, proxy_port=None, ping_interval=10, ping_timeout=5):
        WebsocketExchange.__init__(self, model.api_key, model.secret_key,
                                   url, proxy_host, proxy_port, ping_interval, ping_timeout)
        self.model = model
        self._unchecked_subscribe = {}  # 保存未验证的订阅频道名称

    # 订阅交易对
    def subscribe(self, pairs):
        """
        订阅交易对数据
        :param pairs: (list) 交易对
        :return: void
        """
        # 每一个交易对会订阅如下信息：
        #   登陆
        #   行情数据
        #   市场深度
        #   成交记录
        #   订单数据
        #   账户信息
        #   K线数据
        if self.websocket_worker.websocket_app is not None:
            for pair in pairs:
                s = self._ws_build_login_json()
                self.websocket_worker.websocket_app.send(s)

                channel_names = list()
                channel_names.append(self._ws_encode_channel_name(pair, WS_CHANNEL_TYPE_TICKER))
                channel_names.append(self._ws_encode_channel_name(pair, WS_CHANNEL_TYPE_DEPTH))
                channel_names.append(self._ws_encode_channel_name(pair, WS_CHANNEL_TYPE_DEALS))
                channel_names.append(self._ws_encode_channel_name(pair, WS_CHANNEL_TYPE_ORDER))
                channel_names.append(self._ws_encode_channel_name(pair, WS_CHANNEL_TYPE_BALANCE))
                for kline_type in range(KLINE_TYPE_MIN01, KLINE_TYPE_WEEK + 1):
                    channel_names.append(self._ws_encode_channel_name(pair, WS_CHANNEL_TYPE_KLINE, kline_type))
                self._unchecked_subscribe[pair] = channel_names  # 保存要订阅的频道，用于检测是否订阅成功
                s = self._ws_build_multi_channel_json(channel_names)
                self.websocket_worker.websocket_app.send(s)

    # ------------------------------ 重载方法 ------------------------------ #

    def _on_websocket_dispatch_message(self, message):
        data_set = json.loads(message)
        for rec in data_set:
            if 'channel' in rec.keys():
                channel = rec['channel']
                data = rec['data']
                if 'addChannel' == channel:
                    self._ws_received_add_channel(data)
                else:
                    pair, channel_type, kline_type = self._ws_decode_channel_name(channel)
                    if pair != '' and channel_type != '':
                        switch = {
                            WS_CHANNEL_TYPE_TICKER: self._ws_received_ticker,
                            WS_CHANNEL_TYPE_DEPTH: self._ws_received_depth,
                            WS_CHANNEL_TYPE_DEALS: self._ws_received_deals,
                            WS_CHANNEL_TYPE_ORDER: self._ws_received_order,
                            WS_CHANNEL_TYPE_BALANCE: self._ws_received_balance,
                            WS_CHANNEL_TYPE_KLINE: self._ws_received_kline
                        }
                        if channel_type == WS_CHANNEL_TYPE_KLINE:
                            if kline_type != '':
                                switch[channel_type](pair, kline_type, data)
                        else:
                            switch[channel_type](pair, data)

    # ------------------------------ 构建请求数据 ------------------------------ #

    def _ws_build_login_json(self):
        """
        生成Websocket用户登陆请求的JSON字符串
        :return: (str) 请求的JSON字符串
        """
        params = {'api_key': self.api_key}
        params['sign'] = self._build_sign(params)
        login_dict = {'event': 'login', 'parameters': params}
        return json.dumps(login_dict)

    def _ws_build_single_channel(self, channel_name):
        """
        生成单一注册订阅的数据字典
        :param channel_name: (str) 频道名称
        :return: (dict) 订阅数据字典
        """
        params = {'api_key': self.api_key}
        params['sign'] = self._build_sign(params)
        return {'event': 'addChannel', 'channel': channel_name, 'parameters': params}

    def _ws_build_single_channel_json(self, channel_name):
        """
        生成单一注册订阅的JSON字符串
        :param channel_name: (str) 频道名称
        :return: (str) 注册订阅的JSON数据字符串
        """
        return json.dumps(self._ws_build_single_channel(channel_name))

    def _ws_build_multi_channel_json(self, channel_names):
        """
        生成批量注册订阅的JSON字符串
        :param channel_names: (list) 多个频道名称的列表
        :return: 批量注册订阅的JSON数据字符串
        """
        dict_list = []
        for channel_name in channel_names:
            dict_list.append(self._ws_build_single_channel(channel_name))
        return json.dumps(dict_list)

    # ------------------------------ 私有方法 ------------------------------ #

    # noinspection PyMethodMayBeStatic
    def _build_sign(self, params):
        """
        构建HTTP请求所需的sign
        :param params: dict, 参数字典
        :return: str, sign, 全大写
        """
        sign = ''
        for key in sorted(params.keys()):
            sign += key + '=' + str(params[key]) + '&'
        encode = (sign + 'secret_key=' + self.secret_key).encode('utf-8')
        return hashlib.md5(encode).hexdigest().upper()

    # noinspection PyMethodMayBeStatic
    def _ws_to_own_channel_type(self, standard_channel_type):
        """
        将标准频道类型转换为OKEx对应的频道类型
        :param standard_channel_type: (int) 标准频道类型
        :return: (str) OKEx对应的频道类型
        """
        owns = ['ticker', 'depth', 'deals', 'order', 'balance', 'kline']
        assert ((standard_channel_type >=0) and (standard_channel_type < len(owns))), 'standard_channel_type超出范围值'
        return owns[standard_channel_type]

    # noinspection PyMethodMayBeStatic
    def _ws_to_standard_channel_type(self, own_channel_type):
        """
        将OKEx对应的频道类型转换为标准的频道类型
        :param own_channel_type: (str) OKEx的频道类型
        :return: (int) 标准频道类型
        """
        owns = ['ticker', 'depth', 'deals', 'order', 'balance', 'kline']
        channel_type = arr_index(owns, own_channel_type)
        assert channel_type != NOT_FOUND, 'own_channel_type超出范围值'
        return channel_type

    # noinspection PyMethodMayBeStatic
    def _ws_to_own_kline_type(self, standard_kline_type):
        """
        将标准K线类型转换为OKEx对应的K线类型
        :param standard_kline_type: (int) 标准K线类型
        :return: (str) OKEx对应的K线类型
        """
        owns = ['1min', '3min', '5min', '15min', '30min', '1hour', '2hour', '4hour', '6hour', '12hour', 'day', 'week']
        assert ((standard_kline_type >= 0) and (standard_kline_type < len(owns))), 'standard_kline_type超出范围值'
        return owns[standard_kline_type]

    # noinspection PyMethodMayBeStatic
    def _ws_to_standard_kline_type(self, own_kline_type):
        """
        将OKEx对应的K线类型转换为标准的K线类型
        :param own_kline_type: (str) OKEx对应的K线类型
        :return: (int) 标准的K线类型
        """
        owns = ['1min', '3min', '5min', '15min', '30min', '1hour', '2hour', '4hour', '6hour', '12hour', 'day', 'week']
        kline_type = arr_index(owns, own_kline_type)
        assert kline_type != NOT_FOUND, 'own_kline_type超出范围值'
        return kline_type

    def _ws_encode_channel_name(self, pair, channel_type, kline_type=None):
        """
        构建频道名称
        :param pair: (str) 交易对
        :param channel_type: (int) 订阅频道类型
        :param kline_type: (int) K线类型，如果订阅类型不是K线，则可以不传
        :return: (str) 频道名称
        """
        pair = pair.lower()
        own_channel_type = self._ws_to_own_channel_type(channel_type)
        if channel_type == WS_CHANNEL_TYPE_KLINE:
            assert (kline_type is not None), '没有指定K线类型'
            formatter = 'ok_sub_spot_{pair}_{channel_type}_{kline_type}'
            own_kline_type = self._ws_to_own_kline_type(kline_type)
            return formatter.format(pair=pair, channel_type=own_channel_type, kline_type=own_kline_type)
        else:
            formatter = 'ok_sub_spot_{pair}_{channel_type}'
            return formatter.format(pair=pair, channel_type=own_channel_type)

    def _ws_decode_channel_name(self, channel_name):
        """
        解析频道名称，如果匹配不成功，则返回空字符串
        :param channel_name: (str) 频道名称
        :return: 返回 (str) 交易对、(int) 频道类型、(int) K线类型
        """
        search = re.match(r'ok_sub_spot_(.*)_(.*)_(.*)', channel_name)
        if search is None:
            return '', '', ''

        if search.group(2) == self._ws_to_own_channel_type(WS_CHANNEL_TYPE_KLINE):
            pair = search.group(1).upper()
            own_channel_type = search.group(2)
            own_kline_type = search.group(3)
        else:
            pair = ('{cur_a}_{cur_b}'.format(cur_a=search.group(1), cur_b=search.group(2))).upper()
            own_channel_type = search.group(3)
            own_kline_type = ''

        channel_type = self._ws_to_standard_channel_type(own_channel_type)
        kline_type = None if own_kline_type == '' else self._ws_to_standard_kline_type(own_kline_type)
        return pair, channel_type, kline_type

    # noinspection PyMethodMayBeStatic
    def _get_depth_index(self, depths, price):
        """
        获取指定市场深度中，价格所在的索引值
        :param depths: (list) 市场深度数组，每个元素是一个包含了两个元素的数组，第一个是价格，第二个是数量
        :param price: (float) 价格
        :return: int, 如果找到了对应的价格，返回对应的索引，否则返回-1
        """
        for i, depth in enumerate(depths):
            if depth[0] == price:
                return i
        return -1

    def _ws_do_depth_data(self, cur_depths, new_depths):
        """
        按照规则处理市场深度数据
        :param cur_depths: (list) 当前市场深度数据(asks或者bids)
        :param new_depths: (list) 收到的市场深度数据(asks或者bids)
        :return: (list) 处理后的市场深度数据
        """
        # 如果有对应的价格，且数量为0，则删除
        # 如果有对应的价格，且数量不为0，则修改
        # 如果没有对应的价格，则新增
        for new_item in new_depths:
            price = new_item[0]
            amount = new_item[1]
            index = self._get_depth_index(cur_depths, price)
            if -1 == index:
                cur_depths.append(new_item)
            else:
                if 0 == amount:
                    del cur_depths[index]
                else:
                    cur_depths[index][1] = amount
        return cur_depths

    # ------------------------------ 消息分发处理 ------------------------------ #

    def _ws_received_add_channel(self, data):
        result = data['result']
        channel = data['channel']
        pair, _, _ = self._ws_decode_channel_name(channel)
        if result:
            self._unchecked_subscribe[pair].remove(channel)
            if 0 == len(self._unchecked_subscribe[pair]):
                # 对应的交易对订阅成功
                self.on_subscribe_signal.emit(pair)

            all_ok = True
            for pair, channels in self._unchecked_subscribe.items():
                if 0 != len(channels):
                    all_ok = False
                    break
            if all_ok:
                # 所有交易对订阅成功
                self.on_all_subscribe_signal.emit()

    def _ws_received_ticker(self, pair, data):
        """
        处理订阅的行情数据
        :param pair: (str) 交易对
        :param data: (dict) 数据
        :return: void
        """
        # {'high': '2.071', 'vol': '73368512.1865', 'last': '2.0251', 'low': '1.8706', 'buy': '2.0245',
        #  'change': '0.1114', 'sell': '2.0255', 'dayLow': '1.8706', 'close': '2.0251', 'dayHigh': '2.071',
        #  'open': '1.9137', 'timestamp': 1525342359947}
        self.model.tickers[pair] = {
            'high': float(data['high']),
            'vol': float(data['vol']),
            'last': float(data['last']),
            'low': float(data['low']),
            'buy': float(data['buy']),
            'change': float(data['change']),
            'sell': float(data['sell']),
            'dayLow': float(data['dayLow']),
            'close': float(data['close']),
            'dayHigh': float(data['dayHigh']),
            'open': float(data['open']),
            'timestamp': data['timestamp']
        }
        self.on_ticker_signal.emit(pair)

    def _ws_received_depth(self, pair, data):
        """
        处理订阅的市场深度数据
        :param pair: (str) 交易对
        :param data: (dict) 数据, 收到的市场深度数据，里面包含'asks'和'bids'两个list
        :return: void
        """

        def pre_proc_depths(depths):
            """
            预处理市场深度数据(因为传入的数据全是字符串，这个函数会将其转换为浮点数)
            :param depths: (list) 处理前的市场深度数据
            :return: (list) 处理后的市场深度数据
            """
            new_depths = []
            for depth in depths:
                new_depths.append([float(depth[0]), float(depth[1])])
            return new_depths

        # 从传入的数据中提取市场深度数据
        new_asks = []
        new_bids = []
        if 'asks' in data.keys():
            new_asks = pre_proc_depths(data['asks'])
        if 'bids' in data.keys():
            new_bids = pre_proc_depths(data['bids'])

        # 处理深度数据(asks按照价格升序排列，bids按照价格降序排列)
        if pair not in self.model.asks.keys():
            self.model.asks[pair] = new_asks
        else:
            self.model.asks[pair] = self._ws_do_depth_data(self.model.asks[pair], new_asks)

        if pair not in self.model.bids.keys():
            self.model.bids[pair] = new_bids
        else:
            self.model.bids[pair] = self._ws_do_depth_data(self.model.bids[pair], new_bids)

        self.model.asks[pair] = sorted(self.model.asks[pair], reverse=False)
        self.model.bids[pair] = sorted(self.model.bids[pair], reverse=True)

        # 提交signal
        self.on_depth_signal.emit(pair)

    def _ws_received_deals(self, pair, data):
        pass

    def _ws_received_order(self, pair, data):
        pass

    def _ws_received_balance(self, pair, data):
        pass

    def _ws_received_kline(self, pair, kline_type, data):
        pass
