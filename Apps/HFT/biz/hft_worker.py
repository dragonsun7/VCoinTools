# -*- coding: utf-8 -*-
__author__ = 'Dragon Sun'

from PyQt5.QtCore import *
from Common.exchanges.okex_exchange import *
from Apps.HFT.model.hft_model import *


class HFTWorker(QObject):
    log_signal = pyqtSignal(object)

    def __init__(self, exchange, model, pair):
        QObject.__init__(self)
        self.exchange: OKExExchange = exchange
        self.model: HFTModel = model
        self.pair = pair
        self._cancelled = False

        self.place_amount = 0.33  # 挂单数量(先暂时固定数量)
        self.small_value = 0.0001  # 一个小值，用于计算出新的买一价或卖一价
        self.delta_value = 0.01  # 买卖差价至少要这么多
        self.count = 0  # 计数器

    def work(self):
        while not self._cancelled:
            time.sleep(1)
            self.count += 1
            self.log('---------- %d ----------' % self.count)

            # 获取当前的挂单：无单、买单、卖单
            orders = self.exchange.get_order_info(self.pair, -1)
            if orders is None:
                continue
            assert len(orders) <= 1, '挂单数量应该小于等于1'

            # 根据情况进行挂单动作(新挂单或者重新挂单)
            if 1 == len(orders):
                self.do_replace_order(self.pair, orders[0])
            else:
                self.do_no_order(self.pair)

    # 当前有挂单的处理
    def do_replace_order(self, pair, order):
        # 获取当前挂单信息
        order_id = order['order_id']
        trade_side = TRADE_SIDE_BUY if 'buy' == order['type'] else TRADE_SIDE_SELL
        price = order['price']

        # 买一/卖一价和当前挂单的价格不一致才需要重挂
        # 如果是挂卖单，还需要保证挂单价格不能低于买入价
        first_price = self._get_first_price(pair, trade_side)  # 获取当前的买一卖一价
        if first_price != -1 and first_price != price:  # 如果当前的买一卖一价和当前挂单的价格不一致
            if self._do_cancel_order(pair, order_id):  # 先取消挂单
                self._do_place_order(pair, trade_side)  # 重新挂单

    # 当前没有挂单的处理
    def do_no_order(self, pair):
        # 设置初始参数
        trade_side = TRADE_SIDE_BUY

        prev_place_order = self.model.hft_get_prev_place_order(pair)  # 获取上一次挂单记录
        if prev_place_order is None:
            # 如果之前没有挂单，则按照初始状态挂买单
            self.log('数据库中没有挂单记录，挂买单')
        else:
            # 如果之前是买单，则检查该买单是否成交
            #   如果没有成交，则表示用户取消，从数据库中删除这条记录
            #   如果成交了，则记录到数据库，并开始挂卖单
            # 如果之前是卖单，则检查该卖单是否成交
            #   如果没有成交，则表示用户取消，从数据库中删除这条记录
            #   如果成交了，则记录到数据库，并开始挂买单

            # 查询上一次挂单的成交状态
            prev_order_id = prev_place_order['order_id']
            okex_orders = self.exchange.get_order_info(pair, prev_order_id)

            # 如果没有查询到，则删除掉数据库中上一次挂单记录，并按照初始状态挂买单
            if (okex_orders is None) or (0 == len(okex_orders)):
                self.log('数据库中有挂单记录，但是没有在OKEx上查到，删除数据库中的挂单记录，并初始挂买单')
                self.model.hft_del_prev_place_order(pair, prev_order_id)
            else:
                okex_order = okex_orders[0]
                okex_order_status = okex_order['status']

                # 如果上一次挂单被手动撤销，则按照新价重挂上一次的挂单
                if ORDER_RECALL == okex_order_status:
                    self.log('上一次挂单记录被手动撤销，按照新价重新挂单')
                    trade_side = TRADE_SIDE_BUY if 'buy' == okex_order['type'] else TRADE_SIDE_SELL

                # 如果上一次挂单未成交，则按照新价格(保持买/卖一)重新挂
                if ORDER_OPEN == okex_order_status:
                    self.log('上一次挂单未成交，按照新价重新挂单')
                    trade_side = TRADE_SIDE_BUY if 'buy' == okex_order['type'] else TRADE_SIDE_SELL

                # 如果上一次挂单部分成交(暂不考虑)
                if ORDER_PART == okex_order_status:
                    self.log('上一次挂单部分成交，这种情况暂不处理')
                    pass

                # 如果上一次挂单完全成交，记录到成交表中，并删除上一次挂单记录，然后交换交易方向重新挂单
                if ORDER_CLOSE == okex_order_status:
                    self.log('上一次挂单完全成交，进行反向挂单')
                    self.model.hft_save_order(pair, prev_place_order)
                    self.model.hft_del_prev_place_order(pair, prev_order_id)
                    trade_side = TRADE_SIDE_BUY if 'sell' == okex_order['type'] else TRADE_SIDE_SELL

                # 如果上一次挂单撤单中，则不处理
                if ORDER_RECALLING == okex_order_status:
                    self.log('上一次挂单正在撤销中')
                    pass
        # 开始挂单
        self._do_place_order(pair, trade_side)

    # 获取当前买一或者卖一的价格
    def _get_first_price(self, pair, trade_side):
        if (trade_side == TRADE_SIDE_BUY) and (pair in self.model.bids.keys()) and (len(self.model.bids[pair]) > 0):
            return self.model.bids[pair][0][0]
        if (trade_side == TRADE_SIDE_SELL) and (pair in self.model.asks.keys()) and (len(self.model.asks[pair]) > 0):
            return self.model.asks[pair][0][0]
        return -1

    # 获取当前买一或者卖一的数量
    def _get_first_amount(self, pair, trade_side):
        if (trade_side == TRADE_SIDE_BUY) and (pair in self.model.bids.keys()) and (len(self.model.bids[pair]) > 0):
            return self.model.bids[pair][0][1]
        if (trade_side == TRADE_SIDE_SELL) and (pair in self.model.asks.keys()) and (len(self.model.asks[pair]) > 0):
            return self.model.asks[pair][0][1]
        return -1

    # 获取新的挂单金额
    def _get_new_price(self, pair, trade_side):
        new_price = self._get_first_price(pair, trade_side)
        if -1 == new_price:
            return -1
        if TRADE_SIDE_BUY == trade_side:
            return new_price + self.small_value
        if TRADE_SIDE_SELL == trade_side:
            return new_price - self.small_value
        return -1

    # 取消订单的处理
    def _do_cancel_order(self, pair, order_id):
        result = self.exchange.cancel_order(pair, order_id)
        if result:
            self.model.hft_del_prev_place_order(pair, order_id)
        return result

    # 挂单
    def _do_place_order(self, pair, trade_side):
        new_price = self._get_new_price(pair, trade_side)  # 计算出新的挂单价格
        prev_order = self.model.hft_get_prev_order(pair)  # 获取上一次成交订单信息
        buy_order_id = 0
        if (prev_order is not None) and (TRADE_SIDE_SELL == trade_side):
            buy_order_id = prev_order['order_id']

        # 保证卖单的价格大于等于买入价格
        if (TRADE_SIDE_SELL == trade_side) and (prev_order is not None):
            buy_price = prev_order['price']
            if (buy_price != -1) and (buy_price > new_price):
                new_price = buy_price

        # 开始重新挂单
        side = '买单' if TRADE_SIDE_BUY == trade_side else '卖单'
        s = '下单：{0}, 价格：{1}, 数量: {2}'.format(side, new_price, self.place_amount)
        self.log(s)
        order_id = self.exchange.place_order(pair, trade_side, new_price, self.place_amount)
        if order_id != -1:
            self.model.hft_save_place_order(pair, order_id, trade_side, new_price, self.place_amount, buy_order_id)
        else:
            self.log('挂单失败')

    def log(self, msg):
        self.log_signal.emit(msg)
