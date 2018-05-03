# -*- coding: utf-8 -*-
__author__ = 'Dragon Sun'

# Websocket框架

import websocket
from Common.exchanges.base_exchange import *


class WebsocketExchange(BaseExchange):

    on_connect_signal = QtCore.pyqtSignal()
    on_disconnect_signal = QtCore.pyqtSignal()
    on_error_signal = QtCore.pyqtSignal(object)

    def __init__(self, api_key, secret_key,
                 url=None, proxy_host=None, proxy_port=None, ping_interval=10, ping_timeout=5):

        BaseExchange.__init__(self, api_key, secret_key, proxy_host, proxy_port)
        self.websocket_start_is_ui_trigger = True  # 启动websocket是否从UI触发(如果是，则出现错误时不重新连接)

        # 创建Websocket线程对象
        self.websocket_thread = QtCore.QThread()
        self.websocket_worker = OKExWebsocketWorker(
            url, proxy_host, proxy_port, ping_interval, ping_timeout, self._on_websocket_dispatch_message)
        self.websocket_worker.moveToThread(self.websocket_thread)
        self.websocket_worker.open_signal.connect(self._on_websocket_open)
        self.websocket_worker.error_signal.connect(self._on_websocket_error)
        self.websocket_thread.started.connect(self.websocket_worker.work)

    def start_websocket(self):
        """
        连接Websocket
        :return: void
        """
        self.websocket_start_is_ui_trigger = True
        self._start_websocket()

    def stop_websocket(self):
        """
        断开Websocket
        :return: void
        """
        if self.websocket_thread.isRunning():
            self.websocket_worker.websocket_app.close()
            time.sleep(1)
            self.websocket_thread.quit()
            self.on_disconnect_signal.emit()

    # ------------------------------ 重载方法 ------------------------------ #

    def _on_websocket_dispatch_message(self, message):
        pass

    # ------------------------------ 私有方法 ------------------------------ #

    def _start_websocket(self):
        if not self.websocket_thread.isRunning():
            self.websocket_thread.start()

    def _on_websocket_open(self):
        self.websocket_start_is_ui_trigger = False
        self.on_connect_signal.emit()

    def _on_websocket_error(self, error):
        # 出现错误重新连接
        self.websocket_thread.quit()
        time.sleep(1)
        if not self.websocket_start_is_ui_trigger:
            self._start_websocket()
        self.on_error_signal.emit(error)


class OKExWebsocketWorker(QtCore.QObject):
    # 信号
    open_signal = QtCore.pyqtSignal()
    error_signal = QtCore.pyqtSignal(object)

    def __init__(self, url, proxy_host=None, proxy_port=None, ping_interval=10, ping_timeout=5, message_callback=None):
        QtCore.QObject.__init__(self)
        self.websocket_app = None
        self.url = url
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.message_callback = message_callback

    def work(self):
        # 创建App不能放在初始化方法中(也就是说每次线程启动实际上是新建了一个WebSocketApp)
        websocket.enableTrace(False)
        self.websocket_app = websocket.WebSocketApp(
            self.url,
            on_open=self.on_open,
            on_error=self.on_error,
            on_message=self.on_message,
            on_ping=self.on_ping,
            on_pong=self.on_pong
        )
        self.websocket_app.run_forever(
            http_proxy_host=self.proxy_host,
            http_proxy_port=self.proxy_port,
            ping_interval=self.ping_interval,
            ping_timeout=self.ping_timeout
        )

    def on_open(self, websocket_app):
        self.open_signal.emit()

    def on_error(self, websocket_app, error):
        self.error_signal.emit(error)

    def on_message(self, websocket_app, message):
        # 这是在线程中处理
        if self.message_callback is not None:
            self.message_callback(message)

    def on_ping(self, websocket_app, data):
        pass

    def on_pong(self, websocket_app, data):
        pass
