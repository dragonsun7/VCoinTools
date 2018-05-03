# -*- coding: utf-8 -*-
__author__ = 'Dragon Sun'


import time
import PyQt5.QtCore as QtCore


class BaseClass(QtCore.QObject):

    def __init__(self):
        QtCore.QObject.__init__(self)

    @staticmethod
    def cale_elapsed(callback, **kwargs):
        """
        用于统计方法执行时间
        :param callback: 要调用的方法
        :param kwargs: 要调用方法使用的参数
        :return: 方法返回值，耗时(秒)
        """
        start = time.time()
        ret = callback(**kwargs)
        end = time.time()
        elapsed = end - start

        if isinstance(ret, tuple):
            l = list(ret)
            l.append(elapsed)
            return tuple(l)
        else:
            return ret, elapsed
