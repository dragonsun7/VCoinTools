# -*- coding: utf-8 -*-
__author__ = 'Dragon Sun'

from Common.exchanges.okex_websocket_exchange import *


class OKExExchange(OKExWebsocketExchange):

    order_history_signal = QtCore.pyqtSignal(str)  # 获取用户历史订单信息成功，参数为交易对

    # ---------------------------------------- 重载方法 ---------------------------------------- #
    def __init__(self, model,
                 websocket_url=None, proxy_host=None, proxy_port=None, ping_interval=10, ping_timeout=5):
        OKExWebsocketExchange.__init__(self, model,
                                       websocket_url, proxy_host, proxy_port, ping_interval, ping_timeout)

    def symbol(self):
        return 'OKEx'

    # ---------------------------------------- REST方法 ---------------------------------------- #

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

    def get_order_history(self, pair, page=1):
        """
        获取历史订单信息，只返回最近两天的信息
        :param pair: (str) 交易对
        :param page: (int) 页数
        :return: (bool) 是否执行成功
        """
        page_length = 200
        url = 'https://www.okex.com/api/v1/order_history.do'
        params = {
            'api_key': self.api_key,
            'symbol': pair.lower(),
            'status': 1,
            'current_page': page,
            'page_length': page_length
        }
        params['sign'] = self._build_sign(params)
        json_obj = self.request(HTTP_METHOD_POST, url, params)
        result = json_obj['result']
        if not result:
            return False

        # 保存订单
        orders = json_obj['orders']
        for order in orders:
            order_id = order['order_id']
            order_type = TRADE_SIDE_BUY if order['type'] == 'buy' else TRADE_SIDE_SELL
            amount = order['deal_amount']
            price = order['avg_price']
            total = price * amount
            ts = datetime.datetime.fromtimestamp(int(order['create_date']) / 1000)
            self.model.save_order(pair, order_id, order_type, amount, price, total, ts)

        # 是否还有更多的数据
        total = json_obj['total']
        if page_length * page < total:
            return self.get_order_history(pair, page + 1)
        else:
            return True

    def update_balance(self):
        """
        获取用户余额信息
        :return: (bool) 是否成功
        """
        url = 'https://www.okex.com/api/v1/userinfo.do'
        params = {
            'api_key': self.api_key
        }
        params['sign'] = self._build_sign(params)
        json_obj = self.request(HTTP_METHOD_POST, url, params)
        result = json_obj['result']
        if not result:
            return False

        info_dict = json_obj['info']
        funds_dict = info_dict['funds']
        free_dict = funds_dict['free']
        freezed_dict = funds_dict['freezed']
        for curr in free_dict.keys():
            free = float(free_dict[curr])
            freezed = float(freezed_dict[curr])
            self.model.save_balance(curr.upper(), free, freezed)
        return True

    # ---------------------------------------- 私有方法 ---------------------------------------- #

