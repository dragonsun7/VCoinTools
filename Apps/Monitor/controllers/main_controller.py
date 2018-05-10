# -*- coding: utf-8 -*-
__author__ = 'Dragon Sun'

import sys
from Apps.Monitor import conf as config
from Common.base_controller import *
from Apps.Monitor.model.monitor_model import *
from Common.exchanges.okex_exchange import *
from Common.exchanges.okex_thread import *
from Apps.Monitor.views.main_view import *


class MainController(BaseController):

    def __init__(self):
        BaseController.__init__(self)
        self.timer = None
        self.order_thread: QThread = None
        self.order_worker = None

        # 创建模型对象
        self.model = MonitorModel(
            stop_loss_radio=config.exchange['stop_loss_ratio'],
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
        self.exchange.on_data_signal.connect(self.on_data)

        # 初始化界面
        self.app = QApplication(sys.argv)
        self.main_window = QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.main_window)

        # 初始化控件
        self.traverse(self.main_window, self.traverse_set_empty)
        self.ui.pair_combobox.clear()
        self.ui.pair_combobox.addItems(self.model.pairs)
        self.ui.start_button.setEnabled(True)
        self.ui.stop_button.setEnabled(False)

        # connect slot
        self.ui.pair_combobox.currentIndexChanged.connect(self.on_pair_combobox_changed)
        self.ui.coin_period_combobox.currentIndexChanged.connect(self.on_period_combobox_changed)
        self.ui.add_button.clicked.connect(self.on_add_pair_button_click)
        self.ui.del_button.clicked.connect(self.on_remove_pair_button_click)
        self.ui.start_button.clicked.connect(self.on_start_button_click)
        self.ui.stop_button.clicked.connect(self.on_stop_button_click)
        self.ui.update_order_action.triggered.connect(self.on_update_order_action)
        self.ui.update_balance_action.triggered.connect(self.on_update_balance_action)
        self.ui.clear_log_action.triggered.connect(self.on_clear_log_action)

        # 初始化相关数据
        self.current_pair = ''  # 当前交易对
        self.current_period = KLINE_TYPE_MIN01  # 当前统计时间周期
        self.is_websocket_connected = False
        self.ui.init_balance_label.setText(self.model.to_price_string('USDT', self.model.init_balance('USDT')))  # 期初余额
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
        self.on_ticker(self.current_pair)
        self.on_data(self.current_pair)
        self.on_timer()

    def on_period_combobox_changed(self, index):
        self.current_period = index
        self.on_timer()

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
        self.log('开始连接...')
        self.exchange.start_websocket()

    def on_stop_button_click(self):
        self.exchange.stop_websocket()
        self.log('已断开！')

    # ---------- 补全订单 start ---------- #

    def on_update_order_action(self):
        self.log('开始补全订单...')
        self.order_thread = QThread()
        self.order_worker = OKExGetOrderHistoryWorker(self.exchange, self.model)
        self.order_worker.moveToThread(self.order_thread)
        self.order_worker.success_signal.connect(self.on_update_order_history_success)
        self.order_worker.failure_signal.connect(self.on_update_order_history_failure)
        self.order_thread.started.connect(self.order_worker.work)
        self.order_thread.start()

    def on_update_order_history_success(self):
        self.order_thread.quit()
        self.log('补全订单成功！')
        QMessageBox.information(self.main_window, '补全订单', '补全订单成功', QMessageBox.Ok)

    def on_update_order_history_failure(self):
        self.order_thread.quit()
        self.log('补全订单失败！')
        QMessageBox.warning(self.main_window, '补全订单', '补全订单失败', QMessageBox.Ok)

    # ---------- 补全订单 end ---------- #

    def on_update_balance_action(self):
        result = self.exchange.update_balance()
        if result:
            self.log('补全余额成功！')
        else:
            self.log('补全余额失败！')

    def on_clear_log_action(self):
        self.ui.log_edit.clear()

    # ------------------------------ Websocket Signal Connect ------------------------------ #

    def on_connect(self):
        self.log('Websocket已连接！')
        self.is_websocket_connected = True
        self.exchange.subscribe(self.model.pairs)

        # 创建定时器
        if self.timer is None:
            self.timer = QTimer()
            self.timer.timeout.connect(self.on_timer)
            self.timer.start(1000)

    def on_disconnect(self):
        self.log('Websocket已断开！')
        self.is_websocket_connected = False
        self.current_pair = ''

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
                    # 更新行情数据
                    ticker = self.model.tickers[pair]
                    self.ui.coin_last_label.setText(self.model.to_price_string(pair, ticker['last']))
                    self.ui.coin_open_label.setText(self.model.to_price_string(pair, ticker['open']))
                    self.ui.coin_close_label.setText(self.model.to_price_string(pair, ticker['close']))
                    self.ui.coin_highest_label.setText(self.model.to_price_string(pair, ticker['high']))
                    self.ui.coin_lowest_label.setText(self.model.to_price_string(pair, ticker['low']))
                    self.ui.coin_vol_label.setText(self.model.to_amount_string(pair, ticker['vol']))
                    self.set_label_numeric_value(self.ui.coin_open_diff_percent_label,
                                                 self.model.open_diff_percent(pair), self.model.decimals[pair], True)
                    self.set_label_numeric_value(self.ui.coin_open_diff_usdt_label,
                                                 self.model.open_diff_usdt(pair), self.model.decimals[pair], True)

    def on_data(self, pair):
        total_financial_data = self.model.cale_whole_financial_data()

        # 盈亏%
        total_profit_percent = total_financial_data['total_profit_percent']
        total_profit_usdt = total_financial_data['total_profit_usdt']
        total_position_percent = total_financial_data['total_position_percent']
        total_position_usdt = total_financial_data['total_position_usdt']
        total_settle = total_financial_data['total_settle']
        self.set_label_numeric_value(self.ui.total_profit_percent_label, total_profit_percent, 2, sign_color=True)
        self.set_label_numeric_value(self.ui.total_profit_usdt_label, total_profit_usdt, 4, sign_color=True)
        self.set_label_numeric_value(self.ui.total_position_percent_label, total_position_percent, 2)
        self.set_label_numeric_value(self.ui.total_position_usdt_label, total_position_usdt, 4)
        self.set_label_numeric_value(self.ui.total_settle_label, total_settle, 4)

        if pair == self.current_pair:
            if pair not in self.model.financial_datas.keys():
                return

            # 持仓量
            position_amount = self.model.financial_datas[pair]['position_amount']
            self.set_label_numeric_value(self.ui.coin_position_amount_label, position_amount, self.model.decimals[pair])

            # 持仓总价
            position_total = self.model.financial_datas[pair]['position_total']
            self.set_label_numeric_value(self.ui.coin_position_usdt_label, position_total, 4)

            # 持仓均价
            position_avg = self.model.financial_datas[pair]['position_avg']
            self.set_label_numeric_value(self.ui.coin_avg_label, position_avg, 4)

            # 止损价
            stop_loss_price = self.model.financial_datas[pair]['stop_loss_price']
            self.set_label_numeric_value(self.ui.coin_stop_loss_label, stop_loss_price, 4)

            # 均价价差
            avg_diff_usdt = self.model.financial_datas[pair]['avg_diff_usdt']
            avg_diff_percent = self.model.financial_datas[pair]['avg_diff_percent']
            self.set_label_numeric_value(self.ui.coin_avg_diff_percent_label, avg_diff_percent, 2, sign_color=True)
            self.set_label_numeric_value(self.ui.coin_avg_diff_usdt_label, avg_diff_usdt, 4, sign_color=True)

            # 能卖出的总价
            sell_total = self.model.financial_datas[pair]['sell_total']
            if sell_total is None:
                self.ui.coin_profit_percent_label.setText('市场深度不够')
                self.ui.coin_profit_usdt_label.setText('市场深度不够')
            else:
                profit_usdt = self.model.financial_datas[pair]['profit_usdt']
                profit_percent = self.model.financial_datas[pair]['profit_percent']
                self.set_label_numeric_value(self.ui.coin_profit_percent_label, profit_percent, 2, sign_color=True)
                self.set_label_numeric_value(self.ui.coin_profit_usdt_label, profit_usdt, 4, sign_color=True)

    def on_timer(self):
        # 显示周期数据
        pair = self.current_pair
        if pair != '':
            d = self.model.decimals[pair]
            data = self.model.statistics_data(pair, self.current_period)
            if data:
                self.set_label_numeric_value(self.ui.coin_inflow_label, data['inflow'], d, is_green=True)
                self.set_label_numeric_value(self.ui.coin_outflow_label, data['outflow'], d, is_red=True)
                self.set_label_numeric_value(self.ui.coin_net_inflow_label, data['net_inflow'], d, sign_color=True)
                self.set_label_numeric_value(self.ui.coin_trade_count_label, data['trade_count'], 0)
                self.set_label_numeric_value(self.ui.coin_buy_count_label, data['buy_count'], 0, is_green=True)
                self.set_label_numeric_value(self.ui.coin_sell_count_label, data['sell_count'], 0, is_red=True)
                self.set_label_numeric_value(self.ui.coin_buy_vol_label, data['buy_vol'], d, is_green=True)
                self.set_label_numeric_value(self.ui.coin_sell_vol_label, data['sell_vol'], d, is_red=True)
                self.set_label_numeric_value(self.ui.coin_trade_count_big_label, data['big_trade_count'], 0)
                self.set_label_numeric_value(self.ui.coin_buy_count_big_label, data['big_buy_count'], 0, is_green=True)
                self.set_label_numeric_value(self.ui.coin_sell_count_big_label, data['big_sell_count'], 0, is_red=True)
                self.set_label_numeric_value(self.ui.coin_buy_vol_big_label, data['big_buy_vol'], d, is_green=True)
                self.set_label_numeric_value(self.ui.coin_sell_vol_big_label, data['big_sell_vol'], d, is_red=True)

    # ------------------------------ private ------------------------------ #

    def log(self, s):
        time_str = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        log_str = time_str + ': ' + s
        self.ui.log_edit.appendPlainText(log_str)
