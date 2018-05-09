# -*- coding: utf-8 -*-
__author__ = 'Dragon Sun'

import re
import datetime
import Common.db.postgres as db
from Common.biz_consts import *
from Common.libs.utils import *


class BaseModel:

    def __init__(self, exchange_symbol, exchange_username, db_host, db_port, db_user, db_password, db_database):
        # 交易行情字典
        # {'high': '2.071', 'vol': '73368512.1865', 'last': '2.0251', 'low': '1.8706', 'buy': '2.0245',
        #  'change': '0.1114', 'sell': '2.0255', 'dayLow': '1.8706', 'close': '2.0251', 'dayHigh': '2.071',
        #  'open': '1.9137', 'timestamp': 1525342359947}

        self.exchange_symbol = exchange_symbol  # 交易所符号
        self.exchange_username = exchange_username  # 用户名
        self.exchange_id = None  # 交易所ID
        self.user_id = None  # 用户ID
        self.api_key = None  # API Key
        self.secret_key = None  # Secret Key
        self.buy_fee = None  # 买单手续费比率
        self.sell_fee = None  # 卖单手续费比率
        self.pairs = []  # 交易对列表
        self.pairs_id = {}  # 交易对ID
        self.decimals = {}  # 交易对价格小数位数
        self.asks = {}  # 市场深度——bids
        self.bids = {}  # 市场深度——asks
        self.tickers = {}  # 交易行情

        # 初始化数据库
        db.init_singleton(host=db_host, port=db_port, user=db_user, password=db_password, database=db_database)

        # 初始化数据
        self._get_user_info()
        self._get_pairs_info()

    # ------------------------------ 方法 ------------------------------ #

    # noinspection PyMethodMayBeStatic
    def split_pair(self, pair):
        """
        拆分交易对
        :param pair: (str) 交易对
        :return: (str) curr_a, (str) curr_b
        """
        currs = pair.split('_')
        return currs[0].upper(), currs[1].upper()

    # noinspection PyMethodMayBeStatic
    def to_price_string(self, pair, price):
        return '%.4f' % price  # TODO 从数据库中获取小数点位数

    # noinspection PyMethodMayBeStatic
    def to_amount_string(self, pair, amount):
        return '%.4f' % amount  # TODO 从数据库中获取小数点位数

    # noinspection PyMethodMayBeStatic
    def to_percent_string(self, percent):
        return '%.2f' % percent

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

    # 保存成交记录
    def save_deals(self, pair, deals):
        """
        保存交易记录到数据库
        :param pair: (str) 交易对
        :param deals: (list) 交易记录
        :return: void
        """
        sql = '''
        INSERT INTO 
          tr_deals(pair_id, order_id, ts, side, price, amount, total)
        VALUES
          (%s, %s, %s, %s, %s, %s, %s)
        ON 
          CONFLICT(pair_id, order_id)
        DO
          NOTHING  
                '''

        commands = []
        for deal in deals:
            # 示例数据：[['4855021', '1.412', '28.664', '20:45:05', 'bid']]
            order_id = int(deal[0])
            ts = self._time_str_to_datetime(deal[3])
            side = TRADE_SIDE_BUY if deal[4] == 'bid' else TRADE_SIDE_SELL
            price = float(deal[1])
            amount = float(deal[2])
            total = price * amount
            params = [self.pairs_id[pair], order_id, ts, side, price, amount, total]
            commands.append({'sql': sql, 'params': params})
        db.batch_execute(commands)

    # 保存订单数据
    def save_order(self, pair, order_id, order_type, amount, price, total, ts):
        """
        保存订单数据
        :param pair: (str) 交易对
        :param order_id: (int) 订单编号
        :param order_type: (int) 订单类型(买/卖)
        :param amount: (float) 数量
        :param price: (float) 价格
        :param total: (float) 总额
        :param ts: 时间
        :return: void
        """
        sql = '''
INSERT INTO
tr_order(user_id, pair_id, order_id, order_type, amount, price, total, ts)
VALUES
(%s, %s, %s, %s, %s, %s, %s, %s)
ON
CONFLICT(user_id, pair_id, order_id)
DO
UPDATE SET amount = %s, price = %s, total = %s, ts = %s
            '''
        params = [self.user_id, self.pairs_id[pair], order_id,
                  order_type, amount, price, total, ts, amount, price, total, ts]
        if 0 != amount:
            db.execute(sql, params)

    # 保存账户余额
    def save_balance(self, curr, free, freezed):
        """
        保存订阅的用户余额数据
        :param curr: (str) 币种
        :param free: (float) 可用数量
        :param freezed: (float) 冻结数量
        :return:
        """
        total = free + freezed
        is_legal = True if curr == 'USDT' else False

        sql = '''
INSERT INTO
  tr_balance(user_id, curr, free, freezed, total, is_legal)
VALUES
  (%s, %s, %s, %s, %s, %s)
ON 
    CONFLICT(user_id, curr)
DO
    UPDATE SET free = %s, freezed = %s, total = %s
                '''
        params = [self.user_id, curr, free, freezed, total, is_legal, free, freezed, total]
        db.execute(sql, params)

    # 保存K线数据
    def save_kline(self, pair, kline_type, data):
        """
        保存K线数据
        :param pair: (str) 交易对
        :param kline_type: (int) K线类型
        :param data: (list) K线数据
        :return: void
        """
        sql = '''
INSERT INTO
  {table_name}(pair_id, time_slot, price_open, price_close, price_lowest, price_highest, amount, percent)
VALUES 
  (%s, %s, %s, %s, %s, %s, %s, %s)
ON
  CONFLICT(pair_id, time_slot)
DO
  NOTHING
                '''.format(table_name=self._kline_table_name(kline_type))

        commands = []
        for kline in data:
            # [["1523628180000", "1.382", "1.384", "1.382", "1.3839", "14618.5662"]]
            # [时间,开盘价,最高价,最低价,收盘价,成交量]
            time_slot = datetime.datetime.fromtimestamp(int(kline[0]) / 1000)
            price_open = float(kline[1])
            price_close = float(kline[4])
            price_lowest = float(kline[3])
            price_highest = float(kline[2])
            amount = float(kline[5])
            percent = 0 if 0 == price_open else (price_close - price_open) / price_open * 100
            params = [self.pairs_id[pair], time_slot, price_open, price_close,
                      price_lowest, price_highest, amount, percent]
            commands.append({'sql': sql, 'params': params})
        db.batch_execute(commands)

    # ------------------------------ 私有方法 ------------------------------ #

    @staticmethod
    def _get_start_time(period_type):
        assert ((period_type >= PERIOD_LAST_MIN01) and (period_type <= PERIOD_THIS_MONTH)), 'period_type超出范围值'

        time = datetime.datetime.now()
        if PERIOD_LAST_MIN01 == period_type:
            time += datetime.timedelta(minutes=-1)
        if PERIOD_LAST_MIN03 == period_type:
            time += datetime.timedelta(minutes=-3)
        if PERIOD_LAST_MIN05 == period_type:
            time += datetime.timedelta(minutes=-5)
        if PERIOD_LAST_MIN15 == period_type:
            time += datetime.timedelta(minutes=-15)
        if PERIOD_LAST_MIN30 == period_type:
            time += datetime.timedelta(minutes=-30)
        if PERIOD_LAST_HOUR01 == period_type:
            time += datetime.timedelta(hours=-1)
        if PERIOD_LAST_HOUR02 == period_type:
            time += datetime.timedelta(hours=-2)
        if PERIOD_LAST_HOUR04 == period_type:
            time += datetime.timedelta(hours=-4)
        if PERIOD_LAST_HOUR06 == period_type:
            time += datetime.timedelta(hours=-6)
        if PERIOD_LAST_HOUR12 == period_type:
            time += datetime.timedelta(hours=-12)
        if PERIOD_LAST_DAY == period_type:
            time += datetime.timedelta(days=-1)
        if PERIOD_LAST_WEEK == period_type:
            time += datetime.timedelta(weeks=-1)
        if PERIOD_TODAY == period_type:
            time = time.replace(hour=0, minute=0, second=0, microsecond=0)
        if PERIOD_THIS_WEEK == period_type:
            time += datetime.timedelta(days=-time.weekday())
            time = time.replace(hour=0, minute=0, second=0, microsecond=0)
        if PERIOD_THIS_MONTH == period_type:
            time = time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        return time

    @staticmethod
    def _time_str_to_datetime(time_str):
        """
        时间字符串加上当前日期形成完整日期
        :param time_str: (str) %H:%M:%S格式的时间字符串
        :return: 完整的日期时间
        """
        # 如果当前的小时数为00，传入的小时数为23，则采用前一天的日期
        search = re.match(r'(.*):(.*):(.*)', time_str)
        if search is None:
            return None
        hour = int(search.group(1))

        time = datetime.datetime.now()
        if (0 == time.hour) and (23 == hour):
            time += datetime.timedelta(days=-1)

        date_str = time.strftime('%Y-%m-%d ')
        full_str = date_str + time_str
        return datetime.datetime.strptime(full_str, '%Y-%m-%d %H:%M:%S')

    @staticmethod
    def _kline_table_name(kline_type):
        suffix_list = ['min01', 'min03', 'min05', 'min15', 'min30',
                       'hour01', 'hour02', 'hour04', 'hour06', 'hour12', 'day', 'week']
        assert (kline_type >= 0) and (kline_type < len(suffix_list)), 'kline_type超出范围值'
        return 'kl_{0}'.format(suffix_list[kline_type])

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
  p.uid AS pair_id,
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
            self.pairs_id[pair] = rec['pair_id']
            self.decimals[pair] = int(rec['decimal_count'])
