from threading import *
import time
import Common.exchanges.okex_exchange as okex


class HFTWorker(Thread):
    def __init__(self, exchange, model):
        Thread.__init__(self)
        self._is_cancelled = False
        self.exchange = exchange
        self.model = model
        self.buy_id = None
        self.sell_id = None
        self.buy_price = 0
        self.sell_price = 0

    def run(self):
        while not self._is_cancelled:
            is_none_order = (self.buy_id is None) and (self.sell_id is None)  # 当前没有挂单
            is_all_order = (self.buy_id is not None) and (self.sell_id is not None)  # 当前买单和卖单都有
            is_single_order = (not is_none_order) and (not is_all_order)

            exchange: okex.OKExExchange = self.exchange
            asks, bids = exchange.get_depth()
            sell1 = float(asks[0][0]) - 0.0001
            buy1 = float(bids[0][0]) + 0.0001
            diff_price = sell1 - buy1
            if diff_price > 0.001:
                orders = [
                    {
                        'price': sell1,
                        'amount': 1,
                        'type': 'sell'
                    },
                    {
                        'price': buy1,
                        'amount': 1,
                        'type': 'buy'
                    }
                ]
                if not is_single_order:
                    if is_all_order and (self.sell_price != sell1 or self.buy_price != buy1):
                        # 撤单
                        self.cancel_order()
                        # 挂单
                        exchange.batch_place_order(orders)
                    elif is_none_order:
                        # 挂单
                        exchange.batch_place_order(orders)

            time.sleep(1)

    def stop(self):
        self._is_cancelled = True

    def cancel_order(self):
        # 始终都会撤销两个单子
        exchange: okex.OKExExchange = self.exchange
        orders_list = [str(self.sell_id), str(self.buy_id)]
        success, error = exchange.batch_cancel_order(orders_list)

        # 如果撤销失败就再撤销一次
        if len(error) > 0:
            for order_id in error:
                exchange.cancel_order(order_id)
