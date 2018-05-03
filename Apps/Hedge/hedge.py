# -*- coding: utf-8 -*-
__author__ = 'Dragon Sun'

import Common.db.postgres as db
import Apps.Hedge.conf as conf

if __name__ == '__main__':
    # 初始化数据库
    db.init_singleton(conf.db['host'], conf.db['port'], conf.db['user'], conf.db['password'], conf.db['database'])

    sql = 'select * from bs_exchange'
    dataSet = db.get_all(sql)
