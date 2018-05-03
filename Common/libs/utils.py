# -*- coding: utf-8 -*-
__author__ = 'Dragon Sun'


NOT_FOUND = -1


def arr_index(arr, item):
    """
    查找数组中第一个item的索引值，如果没有找到则返回 NOT_FOUND
    :param arr: 数组
    :param item: 要查找的元素
    :return: 索引值/NOT_FOUND
    """
    try:
        return arr.index(item)
    except ValueError:
        return NOT_FOUND
