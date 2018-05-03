# -*- coding: utf-8 -*-
__author__ = 'Dragon Sun'


from Common.models.base_model import *


class OKExModel(BaseModel):

    def __init__(self, exchange_symbol, exchange_username, db_host, db_port, db_user, db_password, db_database):
        BaseModel.__init__(self, exchange_symbol, exchange_username,
                           db_host, db_port, db_user, db_password, db_database)
