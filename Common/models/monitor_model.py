# -*- coding: utf-8 -*-
__author__ = 'Dragon Sun'


from Common.models.base_model import *


class MonitorModel(BaseModel):

    def __init__(self, stop_loss_radio,  # 止损百分比
                 exchange_symbol, exchange_username,
                 db_host, db_port, db_user, db_password, db_database):
        BaseModel.__init__(self, exchange_symbol, exchange_username,
                           db_host, db_port, db_user, db_password, db_database)
        self.stop_loss_radio = stop_loss_radio
        self.financial_datas = {}

    # ------------------------------ 数据方法 ------------------------------ #

    # 初始金额
    def init_balance(self, curr):
        """
        获取初期余额
        :param curr: (str) 币种
        :return: (float) 初期余额
        """
        sql = 'SELECT SUM(total) AS total FROM tr_balance_init WHERE user_id = %s AND curr = %s'
        params = [self.user_id, curr]
        data_set = db.get_one(sql, params)
        value = data_set['total']
        return 0 if value is None else value

    # 开盘价差
    def open_diff_usdt(self, pair):
        return self.tickers[pair]['last'] - self.tickers[pair]['open']

    def open_diff_usdt_str(self, pair):
        return self.to_price_string(pair, self.open_diff_usdt(pair))

    # 开盘价差(%)
    def open_diff_percent(self, pair):
        open_value = self.tickers[pair]['open']
        return 0 if 0 == open else self.open_diff_usdt(pair) / open_value * 100

    def open_diff_percent_str(self, pair):
        return self.to_percent_string(self.open_diff_percent(pair))

    # 获取交易对周期统计数据
    def statistics_data(self, pair, period_type):
        # {
        #     "trade_count"         int     成交笔数
        #     "buy_count"           int     买单笔数
        #     "buy_vol"             float   买单量
        #     "sell_count"          int     卖单笔数
        #     "sell_vol"            float   卖单量
        #     "big_trade_count"     int     大单笔数
        #     "big_buy_count"       int     大买单笔数
        #     "big_buy_vol"         float   大买单量
        #     "big_sell_count"      int     大卖单笔数
        #     "big_sell_vol"        float   大卖单量
        #     "inflow"              float   流入资金
        #     "outflow"             float   流出资金
        #     "net_inflow"          float   净流入
        # }

        sql = 'SELECT * FROM analyze_data(%s, %s, %s);'
        params = [self.pairs_id[pair], self._get_start_time(period_type), 10000]
        rec = db.get_one(sql, params)
        return rec

    # 持仓量
    def position_amount(self, curr):
        """
        获取持仓量
        :param curr: (str) 币种
        :return: (float) 持仓量
        """
        curr = curr.upper()
        sql = 'SELECT total FROM tr_balance WHERE user_id = %s AND curr = %s'
        data = db.get_one(sql, [self.user_id, curr])
        return data['total'] if data is not None else 0

    # 持仓总价
    def position_total(self, pair):
        """
        获取持仓总价
        :param pair: (str) 交易对
        :return: (float) 持仓总价
        """
        sql = '''
SELECT amount, price FROM tr_order WHERE user_id = %s AND pair_id = %s AND order_type = %s ORDER BY ts DESC
        '''
        buys = db.get_all(sql, [self.user_id, self.pairs_id[pair], TRADE_SIDE_BUY])
        curr_a, curr_b = self.split_pair(pair)
        amount = self.position_amount(curr_a)

        total = 0
        for buy_order in buys:
            order_amount = buy_order['amount']
            order_price = buy_order['price']
            if amount > order_amount:
                total += order_amount * order_price
                amount -= order_amount
            else:
                total += amount * order_price
                break
        return total

    # 获取指定数量的币，按照当前市场深度能卖出的总价
    def sell_total(self, pair, amount):
        """
        指定数量的币按照当前市场深度卖出后的总价格
        :param pair: (str) 交易对
        :param amount: (float) 数量
        :return: (float) 总价，如果为None代表无法计算
        """
        total = 0
        if pair not in self.pairs:
            return None
        if pair not in self.bids.keys():
            return None

        for d_price, d_amount in self.bids[pair]:
            if d_amount >= amount:
                total += d_price * amount
                amount = 0
                break
            else:
                total += d_price * d_amount
                amount -= d_amount

        if amount > 0:
            return None  # 市场深度不够，卖不完
        else:
            return total

    # 计算交易对财务数据
    def cale_financial_data(self, pair):
        curr_a, curr_b = self.split_pair(pair)
        if pair not in self.tickers.keys():
            return False
        last = self.tickers[pair]['last']

        # 持仓量
        position_amount = self.position_amount(curr_a)

        # 持仓总价
        position_total = self.position_total(pair)

        # 持仓均价
        position_avg = 0 if 0 == position_amount else position_total / position_amount

        # 止损价
        stop_loss_price = position_avg * self.stop_loss_radio

        # 均价价差
        avg_diff_usdt = 0 if 0 == position_amount else last - position_avg
        avg_diff_percent = 0 if 0 == position_amount else avg_diff_usdt / last * 100

        # 盈余
        sell_total = self.sell_total(pair, position_amount)  # 能卖出的总价
        if sell_total is None:
            profit_usdt = None
            profit_percent = None
        else:
            profit_usdt = sell_total - position_total
            profit_percent = 0 if 0 == position_total else profit_usdt / position_total * 100

        self.financial_datas[pair] = {}
        self.financial_datas[pair]['position_amount'] = position_amount
        self.financial_datas[pair]['position_total'] = position_total
        self.financial_datas[pair]['position_avg'] = position_avg
        self.financial_datas[pair]['stop_loss_price'] = stop_loss_price
        self.financial_datas[pair]['avg_diff_usdt'] = avg_diff_usdt
        self.financial_datas[pair]['avg_diff_percent'] = avg_diff_percent
        self.financial_datas[pair]['sell_total'] = sell_total
        self.financial_datas[pair]['profit_usdt'] = profit_usdt
        self.financial_datas[pair]['profit_percent'] = profit_percent

        return True

    # 计算整体财务数据
    def cale_whole_financial_data(self):
        total_settle = 0  # 当前结算
        total_profit_usdt = 0  # 盈余
        total_position_usdt = 0  # 仓位(USDT)
        for pair in self.pairs:
            if self.cale_financial_data(pair):
                sell_total = self.financial_datas[pair]['sell_total']
                profit_usdt = self.financial_datas[pair]['profit_usdt']
                position_total = self.financial_datas[pair]['position_total']
                total_settle += sell_total if sell_total is not None else 0  # 当前结算
                total_profit_usdt += profit_usdt if profit_usdt is not None else 0 # 盈亏
                total_position_usdt += position_total if position_total is not None else 0  # 仓位
        usdt_balance = self.position_amount('USDT')
        total_profit_percent = 0 if 0 == total_position_usdt else total_profit_usdt / total_position_usdt * 100  # 盈亏%
        total_position_percent = total_position_usdt / (total_position_usdt + usdt_balance) * 100  # 仓位%

        return {
            'total_profit_percent': total_profit_percent,
            'total_profit_usdt': total_profit_usdt,
            'total_position_percent': total_position_percent,
            'total_position_usdt': total_position_usdt,
            'total_settle': total_settle
        }
