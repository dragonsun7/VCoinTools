# -*- coding: utf-8 -*-
__author__ = 'Dragon Sun'

from Common.models.base_model import *

# 挂单状态
PLACE_ORDER_STATUS_NONE = 0  # 未挂单
PLACE_ORDER_STATUS_BUY = 1  # 挂买单
PLACE_ORDER_STATUS_SELL = 2  # 挂卖单


class HFTModel(BaseModel):

    def __init__(self, exchange_symbol, exchange_username,
                 db_host, db_port, db_user, db_password, db_database):
        BaseModel.__init__(self, exchange_symbol, exchange_username,
                           db_host, db_port, db_user, db_password, db_database)

    # 获取上一次成交订单信息
    def hft_get_prev_order(self, pair):
        sql = 'SELECT * FROM hft_order WHERE user_id = %s AND pair_id = %s AND order_type = 1 ORDER BY ts DESC LIMIT 1'
        params = [self.user_id, self.pairs_id[pair]]
        rec = db.get_one(sql, params)
        return rec

    # 获取上一次挂单信息
    def hft_get_prev_place_order(self, pair):
        sql = 'SELECT * FROM hft_order_place WHERE user_id = %s AND pair_id = %s ORDER BY ts DESC LIMIT 1'
        params = [self.user_id, self.pairs_id[pair]]
        return db.get_one(sql, params)

    # 删除指定挂单
    def hft_del_prev_place_order(self, pair, order_id):
        sql = 'DELETE FROM hft_order_place WHERE user_id = %s AND pair_id = %s AND order_id = %s'
        params = [self.user_id, self.pairs_id[pair], order_id]
        db.execute(sql, params)

    # 保存当前挂单记录
    def hft_save_place_order(self, pair, order_id, trade_side, price, amount, buy_order_id=0, deal_amount=0):
        sql = '''
INSERT INTO
  hft_order_place(user_id, pair_id, order_id, order_type, amount, price, total, ts, buy_order_id, deal_amount)
VALUES
  (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON
  CONFLICT(user_id, pair_id, order_id)
DO
  UPDATE SET order_type = %s, amount = %s, price = %s, total = %s, ts = %s, buy_order_id = %s, deal_amount = %s
        '''
        total = amount * price
        now = datetime.datetime.now()
        params = [
            self.user_id, self.pairs_id[pair], order_id, trade_side,
            amount, price, total, now, buy_order_id, deal_amount,
            trade_side, amount, price, total, now, buy_order_id, deal_amount
        ]
        db.execute(sql, params)

    # 成交后记录成交记录
    def hft_save_order(self, pair, order):
        sql = '''
INSERT INTO
  hft_order(user_id, pair_id, order_id, order_type, amount, price, total, ts, buy_order_id)
VALUES
  (%s, %s, %s, %s, %s, %s, %s, %s, %s)
ON
  CONFLICT(user_id, pair_id, order_id)
DO
  NOTHING
        '''
        params = [
            self.user_id, self.pairs_id[pair], order['order_id'], order['order_type'], order['amount'],
            order['price'], order['total'], order['ts'], order['buy_order_id']
        ]
        db.execute(sql, params)
