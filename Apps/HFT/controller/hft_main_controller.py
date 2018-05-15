# -*- coding: utf-8 -*-
__author__ = 'Dragon Sun'

import sys
import Apps.HFT.hft_conf as config
from Common.base_controller import *
from Common.exchanges.okex_exchange import *
from Apps.HFT.model.hft_model import *
from Apps.HFT.view.hft_main import *
from Apps.HFT.biz.hft_worker import *

COL_INDEX_PAIR = 0
COL_INDEX_PROFIT = 1
COL_INDEX_PROFIT_CNY = 2
COL_INDEX_SIDE = 3
COL_INDEX_COUNT = 4
COL_INDEX_AMOUNT = 5
COL_INDEX_TOTAL_AMOUNT = 6


class MainController(BaseController):

    def __init__(self):
        BaseController.__init__(self)
        self.is_websocket_connected = False
        self.threads = []
        self.workers = []

        # 创建模型对象
        self.model = HFTModel(
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

        # 初始化界面
        self.app = QApplication(sys.argv)
        self.main_window = QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.main_window)

        # 连接Slot
        self.ui.start_button.clicked.connect(self.on_start_button_clicked)
        self.ui.stop_button.clicked.connect(self.on_stop_button_clicked)

        # 初始化组件
        self.ui.stop_button.setEnabled(False)

    def __del__(self):
        self.destroy_workers()

    def show(self):
        self.main_window.show()
        sys.exit(self.app.exec_())  # sys.exit()方法能确保主循环安全退出。外部环境能通知主控件怎么结束。

    def show_table_data(self):
        pairs = self.model.pairs
        table = self.ui.table_widget
        table.setRowCount(len(pairs))
        for row, pair in enumerate(pairs):
            table.setItem(row, COL_INDEX_PAIR, QTableWidgetItem(pair))

    def on_start_button_clicked(self):
        self.log('开始连接...')
        self.exchange.start_websocket()
        self.ui.start_button.setEnabled(False)

    def on_stop_button_clicked(self):
        self.exchange.stop_websocket()
        self.ui.stop_button.setEnabled(False)
        self.log('已断开！')

    def on_cancel_orders_button_clicked(self):
        pass

    # ------------------------------ Websocket Signal Connect ------------------------------ #

    def on_connect(self):
        self.is_websocket_connected = True
        self.exchange.subscribe(self.model.pairs)
        self.ui.stop_button.setEnabled(True)
        self.log('Websocket已连接！')

    def on_disconnect(self):
        # 销毁工人线程
        self.destroy_workers()

        self.is_websocket_connected = False
        self.ui.start_button.setEnabled(True)
        self.log('Websocket已断开！')

    def on_error(self, error):
        self.log('Websocket错误：' + str(error))

    def on_subscribe(self, pair):
        self.log(pair + '订阅成功！')

    def on_all_subscribe(self):
        self.log('所有交易对订阅成功！')
        self.ui.stop_button.setEnabled(True)
        self.show_table_data()

        # 创建工人线程
        self.create_workers()

    # ------------------------------ private ------------------------------ #

    # 创建工人线程
    def create_workers(self):
        for pair in self.model.pairs:
            thread = QThread()
            worker = HFTWorker(self.exchange, self.model, pair)
            worker.log_signal.connect(self.log)
            worker.moveToThread(thread)
            thread.started.connect(worker.work)
            thread.start()
            self.workers.append(worker)
            self.threads.append(thread)

    # 销毁工人线程
    def destroy_workers(self):
        for worker in self.workers:
            worker.stop()
        for thread in self.threads:
            thread.quit()
            thread.wait()
        self.workers = []
        self.threads = []

    def log(self, s):
        time_str = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        log_str = time_str + ': ' + s
        print(log_str)
        self.ui.log_edit.appendPlainText(log_str)
