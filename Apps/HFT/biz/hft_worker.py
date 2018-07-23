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
        self.prev_order_id = -1  # 暂存的挂单ID

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
                self._place_order(self.pair, self.place_amount, self.small_value, orders[0])
            else:
                self._place_order(self.pair, self.place_amount, self.small_value)

    # 挂单
    #
    #
    # 如果当前没有挂单：
    #   根据暂存的订单ID获取成交状态，如果成交则入库
    #   检索数据库，找到上一次成交记录
    #       如果没有上一次成交记录，则初始挂单(买单)
    #       如果上一次成交记录是买单，则按照新价挂卖单
    #       如果上一次成交记录是卖单，则按照新价挂买单
    #   总结：
    #       1. 根据暂存的订单ID获取成交状态，如果成交则入库
    #       2. 查找上一次成交记录
    #       3. 如果没有找到或者上一次为卖单，则按照新价挂买单，否则挂卖单
    #
    #
    # 如果当前有挂单
    #   如果挂单价格为价一，且数量小于价一数量，则不需要重挂
    #   如果挂单价格为价一，且数量等于价一数量：
    #       如果挂单价格与价二的差价等于最小价，则不需要重挂
    #       如果挂单价格与价二的差价大于最小价，则重挂
    #   如果挂单价格不为价一，则重挂
    #   (这个先不做)如果挂单类型为卖单，且买入价高于当前价一，则还需要保证挂单价格大于等于买入价
    # 总结：
    #       1. 获取当前挂单信息
    #       2. 获取当前价一和量一
    #       3. 如果挂单价格不为价一，则重挂
    #       4. 如果挂单价格为价一，且数量等于量一，则：如果价一与价二的差价大于最小价，则重挂
    #
    #
    # 重挂的动作：取消当前挂单、获取价一、结合最小价、挂单
    #
    #
    # 名词：
    #   当前挂单：       place_order
    #   上一次成交订单：  deal_order
    #   价一：           depth_price1
    #   价二：           depth_price2
    #   量一：           depth_qty1
    #   挂单价格:        place_price
    #   挂单数量:        place_qty
    #   最小差异价格：    delta_min
    #
    def _place_order(self, pair, qty, delta_min, place_order=None):

        # 如果当前没有挂单
        if place_order is None:
            # 1. 根据暂存的订单ID获取成交状态，如果成交则入库
            if not self._save_closed_order(pair):
                return

            # 2. 查找上一次的成交记录
            deal_order = self.model.hft_get_prev_order(pair)  # 获取上一次成交订单

            # 3. 如果没有找到或者上一次为卖单，则按照新价挂买单，否则挂卖单
            side = TRADE_SIDE_BUY if deal_order is None else deal_order['order_type']  # 获取交易方向
            price = self._get_new_price(pair, side)  # 生成挂单价格
            if -1 == price:
                return
            self.exchange.place_order(pair, side, price, qty)  # 挂单

        # 如果当前有挂单
        else:
            # 1. 获取当前挂单信息
            side = self.model.hft_to_trade_side(place_order['type'])
            place_order_id = place_order['order_id']
            place_price = place_order['price']
            place_qty = place_order['amount']

            # 2. 获取当前价一和量一
            depth1 = self.model.hft_get_depth(pair, side, 0)
            if depth1 is None:
                return
            depth_price1 = depth1[0]
            depth_qty1 = depth1[1]

            # 3. 如果挂单价格不为价一，则重挂
            if place_price != depth_price1:
                self._replace_order(pair, side, qty, place_order_id)
                return

            # 4. 如果挂单价格为价一，且数量等于量一，则：如果价一与价二的差价大于最小价，则重挂
            if (place_price == depth_price1) and (place_qty == depth_qty1):
                # 获取价二
                depth2 = self.model.hft_get_depth(pair, side, 1)
                if depth2 is None:
                    return
                depth_price2 = depth2[0]

                # 如果价一价hft_order_place二差价大于最小价，则重挂
                if abs(place_price - depth_price2) > delta_min:
                    self._replace_order(pair, side, qty, place_order_id)
                    return

    def _replace_order(self, pair, side, qty, place_order_id):
        # 取消当前挂单
        if not self.exchange.cancel_order(pair, place_order_id):
            return

        # 一定时间的延时
        time.sleep(1)

        # 获取挂单价格(获取价一、结合最小价)
        price = self._get_new_price(pair, side)
        if -1 == price:
            return

        # 挂单
        self.prev_order_id = self.exchange.place_order(pair, side, price, qty)

    # 获取新的挂单金额
    def _get_new_price(self, pair, side):
        depth1 = self.model.hft_get_depth(pair, side, 0)
        if depth1 is None:
            return -1
        price = depth1[0] + self.small_value if TRADE_SIDE_BUY == side else depth1[0] - self.small_value
        return price

    # 保存已成交的订单
    def _save_closed_order(self, pair):
        if self.prev_order_id != -1:
            # 获取前一个订单号的订单
            orders = self.exchange.get_order_info(pair, self.prev_order_id)

            # 没有成功的获取数据
            if orders is None:
                return False

            # 没有找到对应的订单
            if 0 == len(orders):
                self.prev_order_id = 0
                return False

            # 如果已成交，则入库
            prev_order = orders[0]
            if ORDER_CLOSE == prev_order['status']:
                prev_order_id = prev_order['order_id']
                prev_side = TRADE_SIDE_BUY if 'buy' == prev_order['type'] else TRADE_SIDE_SELL
                prev_amount = prev_order['amount']
                prev_price = prev_order['price']
                prev_total = prev_price * prev_amount
                prev_ts = prev_order['create_date']
                self.model.save_order(pair, prev_order_id, prev_side, prev_amount, prev_price, prev_total, prev_ts)
                self.prev_order_id = 0
        return True

    # 输出日志
    def log(self, msg):
        self.log_signal.emit(msg)
