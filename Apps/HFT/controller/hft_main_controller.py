import sys
import threading
import Apps.HFT.conf.hft_conf as conf
import Apps.HFT.model.model as model
import Common.todo.okex_websocket as ws
import Apps.HFT.biz.hft_worker as hft_worker
import Common.exchanges.okex_exchange as okex
from Apps.HFT.view.hft_main import *
from PyQt5.QtWidgets import *

COL_INDEX_PAIR = 0
COL_INDEX_PROFIT = 1
COL_INDEX_PROFIT_CNY = 2
COL_INDEX_SIDE = 3
COL_INDEX_COUNT = 4
COL_INDEX_AMOUNT = 5
COL_INDEX_TOTAL_AMOUNT = 6


class MainController:

    def __init__(self):
        self.workers = []

        # 初始化模型
        self.model = model.Model(conf.model_conf['exchange'], conf.model_conf['username'])

        # 创建交易所对象
        self.exchanges = self.create_exchanges()

        # 创建Websocket对象
        self.websocket_app = ws.OKExWebsocket(
            self.exchanges,
            conf.network_conf['websocket_url'],
            conf.network_conf['proxy_host'],
            conf.network_conf['proxy_port']
        )

        # 初始化界面
        self.app = QApplication(sys.argv)
        self.main_window = QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.main_window)
        self.ui.stop_button.setEnabled(False)

        # connect slot
        self.ui.start_button.clicked.connect(self.on_start_button_clicked)
        self.ui.stop_button.clicked.connect(self.on_stop_button_clicked)
        self.ui.cancel_orders_button.clicked.connect(self.on_cancel_orders_button_clicked)

        # 填充表格
        self.show_table_data()

    # noinspection PyMethodMayBeStatic
    def show(self):
        self.main_window.show()
        sys.exit(self.app.exec_())  # sys.exit()方法能确保主循环安全退出。外部环境能通知主控件怎么结束。

    def create_exchanges(self):
        exchange_list = []
        pairs = self.model.data['pairs']
        for pair in pairs:
            exchange = okex.OKExExchange(
                conf.model_conf['username'],
                pair['pair'],
                self.model.data['api_key'],
                self.model.data['secret_key'],
                conf.network_conf
            )
            exchange_list.append(exchange)
        return exchange_list

    def create_workers(self):
        worker_list = []
        for exchange in self.exchanges:
            worker = hft_worker.HFTWorker(exchange, self.model)
            worker_list.append(worker)
        return worker_list

    def show_table_data(self):
        pairs = self.model.data['pairs']
        table = self.ui.table_widget
        table.setRowCount(len(pairs))
        for row, pair in enumerate(pairs):
            table.setItem(row, COL_INDEX_PAIR, QTableWidgetItem(pair['pair']))

    # noinspection PyMethodMayBeStatic
    def on_close(self):
        print('close')

    # noinspection PyMethodMayBeStatic
    def on_start_button_clicked(self):
        self.workers = self.create_workers()
        # for worker in self.workers:
        #     worker.start()

        # 当前OKB交易对的Websocket暂时不能用
        threading.Thread(target=self.websocket_app.start).start()  # TODO 线程如何结束？
        self.ui.start_button.setEnabled(False)
        self.ui.stop_button.setEnabled(True)

    # noinspection PyMethodMayBeStatic
    def on_stop_button_clicked(self):
        for worker in self.workers:
            worker.stop()
        self.workers.clear()

        # 当前OKB交易对的Websocket暂时不能用
        self.websocket_app.stop()
        self.ui.start_button.setEnabled(True)
        self.ui.stop_button.setEnabled(False)

    # noinspection PyMethodMayBeStatic
    def on_cancel_orders_button_clicked(self):
        self.ui.table_widget.insertRow()
        print('cancel orders')
