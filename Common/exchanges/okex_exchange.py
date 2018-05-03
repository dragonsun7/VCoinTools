# -*- coding: utf-8 -*-
__author__ = 'Dragon Sun'

from Common.exchanges.okex_websocket_exchange import *


class OKExExchange(OKExWebsocketExchange):

    # ---------------------------------------- 重载方法 ---------------------------------------- #
    def __init__(self, model,
                 websocket_url=None, proxy_host=None, proxy_port=None, ping_interval=10, ping_timeout=5):
        OKExWebsocketExchange.__init__(self, model,
                                       websocket_url, proxy_host, proxy_port, ping_interval, ping_timeout)

    def symbol(self):
        return 'OKEx'

    def get_depth(self, pair):
        url = 'https://www.okex.com/api/v1/depth.do'
        params = {'symbol': pair.lower()}
        json_obj = self.request(HTTP_METHOD_GET, url, params)
        asks = sorted(json_obj['asks'], reverse=False)
        bids = sorted(json_obj['bids'], reverse=True)
        return asks, bids

    def place_order(self, pair, trade_side, price, amount):
        url = 'https://www.okex.com/api/v1/trade.do'
        params = {
            'api_key': self.api_key,
            'symbol': pair.lower(),
            'type': 'buy' if trade_side == TRADE_SIDE_BUY else 'sell',
            'price': price,
            'amount': amount
        }
        params['sign'] = self._build_sign(params)
        json_obj = self.request(HTTP_METHOD_POST, url, params)
        result = json_obj['result']
        order_id = json_obj['order_id'] if result else -1
        err_code = 0 if result else json_obj['error_code']
        err_msg = ''  # TODO
        return result, order_id, err_code, err_msg

    def cancel_order(self, pair, order_id):
        url = 'https://www.okex.com/api/v1/cancel_order.do'
        params = {
            'api_key': self.api_key,
            'symbol': pair.lower(),
            'order_id': order_id
        }
        params['sign'] = self._build_sign(params)
        json_obj = self.request(HTTP_METHOD_POST, url, params)
        return json_obj['result']

    # ---------------------------------------- REST方法 ---------------------------------------- #

    def batch_place_order(self, trade_infos):
        # TODO 测试
        """
        批量下单
        :param trade_infos:list, 下单数据列表，每个元素都是：{'price':price, 'amount':amount, 'type':'sell'/'buy'}
        :return:list, order_ids
        """
        url = 'https://www.okex.com/api/v1/batch_trade.do'
        params = {
            'api_key': self.api_key,
            'symbol': self.pair.lower(),
            'orders_data': json.dumps(trade_infos)
        }
        params['sign'] = self._build_sign(params)
        json_obj = self.request(HTTP_METHOD_POST, url, params)
        result = json_obj['result']
        orders_id = []
        if result:
            for order_info in json_obj['order_info']:
                orders_id.append(order_info['order_id'])
        return result, order_info

    def batch_cancel_order(self, orders_id):
        # TODO 测试
        """
        批量撤销订单(最多允许3个)
        :param orders_id: 订单ID数组，每个元素都是字符串
        :return: list success(撤销成功的ID), list error(撤销失败的ID)
        """
        assert (len(orders_id) > 1) and (len(orders_id) <= 3), '批量撤销的订单数量应该大于1小于等于3'
        url = 'https://www.okex.com/api/v1/cancel_order.do'
        params = {
            'api_key': self.api_key,
            'symbol': self.pair.lower(),
            'order_id': ','.join(orders_id)
        }
        params['sign'] = self._build_sign(params)
        json_obj = self.request(HTTP_METHOD_POST, url, params)
        return json_obj['success'], json_obj['error']

    # ---------------------------------------- Websocket基本方法 -------------------------------- #

    def _ws_proc_depth_message(self, asks, bids, data):
        # TODO
        """
        处理订阅的市场深度数据
        :param asks: 现有的asks数据
        :param bids: 现有的bids数据
        :param data: dict,收到的市场深度数据，里面包含'asks'和'bids'两个list
        :return: 处理后的asks和bids
        """
        ask_list = []
        bid_list = []
        if 'asks' in data.keys():
            for ask in data['asks']:
                ask_list.append([float(ask[0]), float(ask[1])])
        if 'bids' in data.keys():
            for bid in data['bids']:
                bid_list.append([float(bid[0]), float(bid[1])])

        if len(asks) > 0:  # 不是第一次收到asks数据
            self._ws_do_depth_data(asks, ask_list)
        if len(bids) > 0:  # 不是第一次收到bids数据
            self._ws_do_depth_data(bids, bid_list)

        ask_list = sorted(ask_list, reverse=False)
        bid_list = sorted(bid_list, reverse=True)

        return ask_list, bid_list

    # ---------------------------------------- 私有方法 ---------------------------------------- #

