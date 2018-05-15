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

    # 币币交易-1 获取用户余额
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

    # 币币交易-2 下单
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

        if json_obj is None:
            return -1
        if 'result' in json_obj.keys():
            result = json_obj['result']
            if result:
                return json_obj['order_id']
        else:
            return -1

    # 币币交易-3 批量下单
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

    # 币币交易-4-1 撤销订单
    def cancel_order(self, pair, order_id):
        url = 'https://www.okex.com/api/v1/cancel_order.do'
        params = {
            'api_key': self.api_key,
            'symbol': pair.lower(),
            'order_id': order_id
        }
        params['sign'] = self._build_sign(params)
        json_obj = self.request(HTTP_METHOD_POST, url, params)
        if json_obj is None:
            return False
        if 'result' in json_obj.keys():
            return json_obj['result']
        else:
            return False

    # 币币交易-4-2 批量撤销订单
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

    # 币币交易-5 获取订单信息
    def get_order_info(self, pair, order_id):
        """
        获取订单信息 (访问频率 20次/2秒)
        :param pair: (str) 交易对
        :param order_id: (int) 订单ID，如果为-1则查询未完成订单
        :return: (list) 每个元素是个dict, None(如果出错)
        [
            {
                "amount": 0.1,                  委托数量
                "avg_price": 0,                 成交均价
                "create_date": 1418008467000,   委托时间
                "deal_amount": 0,               成交数量
                "order_id": 10000591,           订单ID
                "orders_id": 10000591,          (不使用)
                "price": 500,                   委托价格
                "status": 0,                    订单状态(-1:已撤销  0:未成交  1:部分成交  2:完全成交 3:撤单处理中)
                "symbol": "btc_usd",            交易对
                "type": "sell"                  交易类型(buy_market:市价买入 / sell_market:市价卖出 / buy / sell)
            }
        ]
        """
        url = 'https://www.okex.com/api/v1/order_info.do'
        params = {
            'api_key': self.api_key,
            'symbol': pair.lower(),
            'order_id': order_id
        }
        params['sign'] = self._build_sign(params)
        json_obj = self.request(HTTP_METHOD_POST, url, params)
        if json_obj is None:
            return None
        result = json_obj['result']
        if not result:
            return None
        return json_obj['orders']

    # 币币交易-6 批量获取订单信息
    def get_batch_order_info(self, query_type, pair, orders_id):
        """
        批量获取订单信息 (访问频率 20次/2秒)
        :param query_type: (int) 查询类型 0:未完成的订单 1:已经完成的订单
        :param pair: (str) 交易对
        :param orders_id: (list) 订单ID
        :return: (list) 同get_order_info
        """
        url = 'https://www.okex.com/api/v1/orders_info.do'
        params = {
            'api_key': self.api_key,
            'symbol': pair.lower(),
            'type': query_type,
            'order_id': ','.join(orders_id)
        }
        params['sign'] = self._build_sign(params)
        json_obj = self.request(HTTP_METHOD_POST, url, params)
        result = json_obj['result']
        if not result:
            return None
        return json_obj['orders']

    # 币币交易-7 获取历史订单信息
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

    # ---------------------------------------- 私有方法 ---------------------------------------- #

