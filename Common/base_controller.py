# -*- coding: utf-8 -*-
__author__ = 'Dragon Sun'

import re
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class BaseController(QObject):

    def traverse(self, obj: QObject, callback=None):
        for child in obj.children():
            if callback is not None:
                callback(child)

            if len(child.children()) > 0:
                self.traverse(child, callback)

    @staticmethod
    def traverse_set_empty(obj: QObject):
        if isinstance(obj, QLabel):
            if not re.match(r'label_?', obj.objectName()):
                obj.setText('')

        # if isinstance(obj, QComboBox):
        #     obj.clear()

        if isinstance(obj, QPlainTextEdit):
            obj.clear()

    @staticmethod
    def set_sign_color(obj: QWidget, value):
        style = 'color: rgb(16, 128, 64);' if value >= 0 else 'color: rgb(252, 1, 7);'
        obj.setStyleSheet(style)

    def set_label_numeric_value(self, label: QLabel, value, decimal_digits,
                                sign_color=False, is_green=False, is_red=False):
        fmt = '%.{0}f'.format(decimal_digits)
        s = fmt % value
        label.setText(s)
        if sign_color:
            self.set_sign_color(label, value)
        elif is_green:
            label.setStyleSheet('color: rgb(16, 128, 64);')
        elif is_red:
            label.setStyleSheet('color: rgb(252, 1, 7);')
        else:
            label.setStyleSheet('color: rgb(0, 0, 0);')
