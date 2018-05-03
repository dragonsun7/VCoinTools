# -*- coding: utf-8 -*-
__author__ = 'Dragon Sun'


import Common.db.postgres as db
from Common.libs.utils import *


class BaseModel:

    def __init__(self, exchange_symbol, exchange_username, db_host, db_port, db_user, db_password, db_database):
        self.exchange_symbol = exchange_symbol
        self.exchange_username = exchange_username
        self.user_id = None  # user id
        self.exchange_id = None  # exchange id
        self.api_key = None  # api key
        self.secret_key = None  # secret key
        self.buy_fee = None  # 买单手续费比率
        self.sell_fee = None  # 卖单手续费比率
        self.pairs = []  # 交易对列表
        self.decimals = {}  # 交易对价格小数位数
        self.asks = {}  # bids
        self.bids = {}  # asks

        # {'high': '2.071', 'vol': '73368512.1865', 'last': '2.0251', 'low': '1.8706', 'buy': '2.0245',
        #  'change': '0.1114', 'sell': '2.0255', 'dayLow': '1.8706', 'close': '2.0251', 'dayHigh': '2.071',
        #  'open': '1.9137', 'timestamp': 1525342359947}
        self.tickers = {}  # 交易行情

        # 初始化数据库
        db.init_singleton(host=db_host, port=db_port, user=db_user, password=db_password, database=db_database)

        # 初始化数据
        self._get_user_info()
        self._get_pairs_info()

    # ------------------------------ 方法 ------------------------------ #

    # 添加交易对
    def add_pair(self, pair, decimal=4):
        pair = pair.upper()
        currs = pair.split('_')
        if (len(currs) != 2) or (currs[0] == '') or (currs[1] == ''):
            return False

        sql1 = '''
INSERT INTO
  bs_pair(exchange_id, symbol, curr_a, curr_b, active)
VALUES
  (%s, %s, %s, %s, TRUE)
ON
  CONFLICT(exchange_id, symbol)
DO
  UPDATE SET active = TRUE        
        '''
        params1 = [self.exchange_id, pair, currs[0], currs[1]]
        db.execute(sql1, params1)

        sql2 = 'SELECT uid FROM bs_pair WHERE exchange_id = %s AND symbol = %s'
        params2 = [self.exchange_id, pair]
        rec = db.get_one(sql2, params2)
        pair_id = rec['uid']

        sql3 = '''
INSERT INTO
  st_pair(user_id, pair_id, decimal_count)
VALUES
  (%s, %s, %s)
ON
  CONFLICT(user_id, pair_id)
DO
  UPDATE SET decimal_count = %s
        '''
        params3 = [self.user_id, pair_id, decimal, decimal]
        db.execute(sql3, params3)

        self._get_pairs_info()
        return True

    # 移除交易对
    def remove_pair(self, pair):
        sql = '''
UPDATE
  bs_pair
SET
  active = FALSE
WHERE
  exchange_id = %s
  AND symbol = %s        
        '''
        params = [self.exchange_id, pair]
        db.execute(sql, params)

    # ------------------------------ 私有方法 ------------------------------ #

    # 获取用户相关信息
    def _get_user_info(self):
        """
        获取用户相关信息
        :return: void
        """
        sql = '''
SELECT
  u.uid as user_id,
  e.uid as exchange_id,
  u.api_key,
  u.secret_key,
  u.buy_fee,
  u.sell_fee
FROM
  bs_exchange_user AS u,
  bs_exchange as e
WHERE
  u.exchange_id = e.uid
  AND e.active
  AND u.active
  AND e.symbol = %s
  AND u.username = %s
        '''
        params = [self.exchange_symbol, self.exchange_username]
        rec = db.get_one(sql, params)
        self.user_id = rec['user_id']
        self.exchange_id = rec['exchange_id']
        self.api_key = rec['api_key']
        self.secret_key = rec['secret_key']
        self.buy_fee = rec['buy_fee']
        self.sell_fee = rec['sell_fee']

    # 获取可用交易对信息
    def _get_pairs_info(self):
        """
        获取交易对相关信息
        :return: void
        """
        sql = '''
SELECT
  p.symbol AS pair,
  s.decimal_count
FROM
  bs_pair AS p,
  bs_exchange AS e,
  bs_exchange_user AS u,
  st_pair AS s
WHERE
  p.active AND e.active	AND u.active
  AND p.exchange_id = e.uid
  AND u.exchange_id = e.uid
  AND s.user_id = u.uid
  AND s.pair_id = p.uid
  AND e.symbol = %s
  AND u.username = %s
        '''
        params = [self.exchange_symbol, self.exchange_username]
        data_set = db.get_all(sql, params)
        for rec in data_set:
            pair = str(rec['pair']).upper()
            if NOT_FOUND == arr_index(self.pairs, pair):
                self.pairs.append(pair)
            self.decimals[pair] = int(rec['decimal_count'])

    # 保存成交记录
    def _save_deals(self):
        # TODO
        pass

    # 保存K线数据
    def _save_kline(self):
        # TODO
        pass

    # 保存订单数据
    def _save_order(self):
        # TODO
        pass

    # 保存账户余额
    def _save_balance(self):
        # TODO
        pass

# # noinspection PyMethodMayBeStatic
# def _get_kline_table_name(self, kline_type):
#     types = ['min01', 'min03', 'min05', 'min15', 'min30',
#              'hour01', 'hour02', 'hour04', 'hour06', 'hour12', 'day', 'week']
#     assert (kline_type >= 0) and (kline_type < len(types)), 'kline_type超出范围值'
#     return 'kl_{0}'.format(types[kline_type])
