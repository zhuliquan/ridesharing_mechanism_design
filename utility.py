# !/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/3/6
import pickle
import time
import numpy as np
from functools import wraps
from decimal import Decimal
from inspect import signature

from setting import VALUE_EPS, POINT_LENGTH


def save_result(result_file):
    """
    保存函数运行结果的装饰器
    :param result_file: 需要保存结果的文件名称
    :return:
    """

    def outer_decorator(func):
        def inner_decorator(*args, **kwargs):
            result = func(args, kwargs)
            with open(result_file, "wb") as file:
                pickle.dump(result, file)
            return result

        return inner_decorator

    return outer_decorator


def force_type_check(func):
    """
    用于强制类型检查的装饰器
    :param func:
    :return:
    """
    sig = signature(func)

    def decorate_func(*args, **kwargs):

        bound_arguments = sig.bind(*args, **kwargs)

        for param, value in bound_arguments.arguments.items():
            if not isinstance(value, func.__annotations__[param]):
                raise Exception("{0} should be {1}, but you give {2}".format(param, func.__annotations__[param], type(value)))
        for param, value in bound_arguments.kwargs.items():
            if not isinstance(value, func.__annotations__[param]):
                raise Exception("{0} should be {1}, but you give {2}".format(param, func.__annotations__[param], type(value)))

        return func(*args, **kwargs)

    return decorate_func


def print_execute_time(func):
    """
    用于求解运行时间的装饰器
    :param func:
    :return:
    """

    def decorate_func(*args, **kwargs):
        start_time = time.clock()
        result = func(*args, **kwargs)
        print("{0} has elapsed {1} s".format(func.__name__, time.clock() - start_time))
        return result

    return decorate_func


def equal(float_value1: float, float_value2: float):
    """
    用于判断两个浮点数相等
    :param float_value1: 第一个浮点数
    :param float_value2: 第二个浮点数
    :return:
    """
    return abs(float_value1 - float_value2) <= VALUE_EPS


def is_enough_small(value: float, eps: float) -> bool:
    """
    如果值过小(小于等于eps)就返回True
    :param value: 距离
    :param eps: 评判足够小的刻度，小于等于这个值就是足够小了
    :return:
    """
    return value < eps or equal(value, eps)  # 由于浮点数有精度误差必须这么写


def plot_vehicles_on_network(vehicles, network):
    import osmnx as ox
    vehicle_nodes = set()
    for vehicle in vehicles:
        vehicle_nodes.add(network.index2osm_id[vehicle.location.osm_index])
    nc = ['r' if node in vehicle_nodes else 'none' for node in network.graph.nodes()]
    ox.plot_graph(network.graph, node_color=nc)


def singleton(cls):
    _instance = {}

    @wraps(cls)
    def _func(*args, **kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]

    return _func


def load_bin_data(file_name: str):
    s = file_name.split('.')
    if s[-1] == "pkl":
        with open(file_name, "rb") as file:
            data = pickle.load(file)
    elif s[-1] == "npy":
        data = np.load(file_name)
    elif s[-1] == "graphml":
        import osmnx as ox
        s = file_name.split("/")
        data = ox.load_graphml(filename=s[-1], folder="/".join(s[:-1]))
    else:
        raise Exception("给定拓展名{0}，不知道如何处理".format(s[-1]))
    return data


def save_bin_data(file_name: str, data):
    s = file_name.split('.')
    if s[-1] == "pkl":
        with open(file_name, "wb") as file:
            pickle.dump(data, file)
    elif s[-1] == "npy":
        np.save(file_name, data)
    else:
        raise Exception("给定拓展名{0}，不知道如何处理".format(s[-1]))


def fix_point_length_add(value1: float, value2: float):
    return np.round(float(Decimal(str(value1)) + Decimal(str(value2))), POINT_LENGTH)


def fix_point_length_sub(value1: float, value2: float):
    return np.round(float(Decimal(str(value1)) - Decimal(str(value2))), POINT_LENGTH)

