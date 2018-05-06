# -*- coding: utf-8 -*-
__author__ = 'Dragon Sun'


import sys
import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import conf as config
from Common.models.okex_model import *
from Common.exchanges.okex_exchange import *
from Demos.depth.views.demo_depth_view_main import *


class MainController:

    def __init__(self):
        # 创建模型对象
        self.model = OKExModel(
            exchange_symbol=config.exchange['symbol'],
            exchange_username=config.exchange['username'],
            db_host=config.database['host'],
            db_port=config.database['port'],
            db_user=config.database['user'],
            db_password=config.database['password'],
            db_database=config.database['database']
        )

        # 创建交易所对象
        self.exchange = OKExExchange(
            model=self.model,
            websocket_url=config.network['websocket_url'],
            proxy_host=config.network['proxy_host'],
            proxy_port=config.network['proxy_port'],
            ping_interval=config.network['ping_interval'],
            ping_timeout=config.network['ping_timeout'],
        )
        self.exchange.on_connect_signal.connect(self.on_connect)
        self.exchange.on_disconnect_signal.connect(self.on_disconnect)
        self.exchange.on_error_signal.connect(self.on_error)
        self.exchange.on_subscribe_signal.connect(self.on_subscribe)
        self.exchange.on_all_subscribe_signal.connect(self.on_all_subscribe)
        self.exchange.on_ticker_signal.connect(self.on_ticker)
        self.exchange.on_depth_signal.connect(self.on_depth)

        # 初始化界面
        self.app = QApplication(sys.argv)
        self.main_window = QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.main_window)

        # 初始化控件
        self.ui.ticker_price_label.setText('')
        self.ui.ticker_logo_label.setText('')
        self.ui.start_button.setEnabled(True)
        self.ui.stop_button.setEnabled(False)
        asks_header_view: QHeaderView = self.ui.asks_table.horizontalHeader()
        asks_header_view.setSectionsClickable(False)
        bids_header_view: QHeaderView = self.ui.bids_table.horizontalHeader()
        bids_header_view.setSectionsClickable(False)
        self.ui.pair_combobox.addItems(self.model.pairs)

        # connect slot
        self.ui.pair_combobox.currentIndexChanged.connect(self.on_pair_combobox_changed)
        self.ui.add_pair_button.clicked.connect(self.on_add_pair_button_click)
        self.ui.remove_pair_button.clicked.connect(self.on_remove_pair_button_click)
        self.ui.start_button.clicked.connect(self.on_start_button_click)
        self.ui.stop_button.clicked.connect(self.on_stop_button_click)
        self.ui.clear_log_button.clicked.connect(self.on_clear_log_button_click)

        # 初始化相关数据
        self.current_pair = ''  # 当前交易对
        self.is_websocket_connected = False
        self.on_pair_combobox_changed(self.ui.pair_combobox.currentIndex())

    def show(self):
        self.main_window.show()
        sys.exit(self.app.exec_())  # sys.exit()方法能确保主循环安全退出。外部环境能通知主控件怎么结束。

    # ------------------------------ property ------------------------------ #

    @property
    def is_websocket_connected(self):
        return self.is_websocket_connected

    @is_websocket_connected.setter
    def is_websocket_connected(self, value):
        self.ui.start_button.setEnabled(not value)
        self.ui.stop_button.setEnabled(value)

    # ------------------------------ UI Slot ------------------------------ #

    def on_pair_combobox_changed(self, index):
        self.current_pair = self.ui.pair_combobox.itemText(index)
        self.ui.pair_label.setText(self.current_pair)
        self.on_ticker(self.current_pair)
        self.on_depth(self.current_pair)

    def on_add_pair_button_click(self):
        pair = self.ui.pair_combobox.currentText().upper()
        if self.model.add_pair(pair):
            self.ui.pair_combobox.addItem(pair)
            self.ui.pair_combobox.setCurrentIndex(self.ui.pair_combobox.count() - 1)
            self.exchange.subscribe([pair])
        else:
            self.log('交易对%s添加失败！' % pair)

    def on_remove_pair_button_click(self):
        index = self.ui.pair_combobox.currentIndex()
        pair = self.ui.pair_combobox.itemText(index)
        self.model.remove_pair(pair)
        self.ui.pair_combobox.removeItem(index)

    def on_start_button_click(self):
        self.exchange.start_websocket()

    def on_stop_button_click(self):
        self.exchange.stop_websocket()

    def on_clear_log_button_click(self):
        self.ui.log_edit.clear()

    # ------------------------------ Websocket Signal Connect ------------------------------ #

    def on_connect(self):
        self.log('Websocket已连接！')
        self.is_websocket_connected = True
        self.exchange.subscribe(self.model.pairs)

    def on_disconnect(self):
        self.log('Websocket已断开！')
        self.is_websocket_connected = False

    def on_error(self, error):
        self.log('Websocket错误：' + str(error))

    def on_subscribe(self, pair):
        self.log(pair + '订阅成功！')

    def on_all_subscribe(self):
        self.log('所有交易对订阅成功！')

    def on_ticker(self, pair):
        if pair == self.current_pair:
            if self.model.tickers:
                if pair in self.model.tickers.keys():
                    self.ui.ticker_price_label.setText(str(self.model.tickers[pair]['last']))

    def on_depth(self, pair):
        def fill_depth(qt_table, depth_list):
            qt_table.setRowCount(len(depth_list))
            for row, depth in enumerate(depth_list):
                price = depth[0]
                amount = depth[1]
                item_amount = QTableWidgetItem('%.4f' % amount)
                item_amount.setTextAlignment(Qt.AlignRight)
                qt_table.setItem(row, 0, QTableWidgetItem('%.4f' % price))
                qt_table.setItem(row, 1, item_amount)

        if pair == self.current_pair:
            asks = []
            bids = []
            if self.model.asks and (pair in self.model.asks.keys()):
                asks = self.model.asks[pair]
            if self.model.bids and (pair in self.model.bids.keys()):
                bids = self.model.bids[pair]
            fill_depth(self.ui.asks_table, asks)
            fill_depth(self.ui.bids_table, bids)

    # ------------------------------ private ------------------------------ #

    def log(self, s):
        time_str = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        log_str = time_str + ': ' + s
        self.ui.log_edit.appendPlainText(log_str)
