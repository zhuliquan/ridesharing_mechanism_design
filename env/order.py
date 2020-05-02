#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/10/22
"""
TODO 本文之探讨只有一个乘客订单的情况, 后续可能要加入多个乘客的情况
"""
from typing import Set

import pandas as pd

from env.location import PickLocation, DropLocation
from setting import FLOAT_ZERO, INT_ZERO

__all__ = ["Order"]


class Order:
    """
    订单类
    order_id: 订单编号
    pick_location: 起始地
    drop_location: 终止地
    request_time: 请求时间
    wait_time:    等待时间
    order_distance: 订单行程距离
    order_fare: 订单费用
    detour_ratio: 最大可以容忍的绕路比
    n_riders: 订单的乘客数目
    """
    __slots__ = [
        "_order_id",
        "_pick_location",
        "_drop_location",
        "_request_time",
        "_wait_time",
        "_order_distance",
        "_order_fare",
        "_detour_distance",
        "_n_riders",
        "_pick_up_distance",
        "_belong_vehicle",
        "_have_finish",
        "_real_pick_up_time",
        "_real_order_distance",
        "_real_service_time",
        "_real_detour_ratio",
        "_real_wait_time",
    ]

    order_generator = None  # 设置订单生成器

    def __init__(self, order_id: int, pick_location: PickLocation, drop_location: DropLocation, request_time: int, wait_time: int, order_distance: float, order_fare: float, detour_ratio: float, n_riders=1):
        self._order_id: int = order_id
        self._pick_location: PickLocation = pick_location
        self._pick_location.set_belong_order(self)  # 反向设置，方便定位
        self._drop_location: DropLocation = drop_location
        self._drop_location.set_belong_order(self)  # 方向设置，方便定位
        self._request_time: int = request_time
        self._wait_time: int = wait_time
        self._order_distance: float = order_distance
        self._order_fare: float = order_fare
        self._detour_distance: float = detour_ratio * order_distance  # 最大绕路距离
        self._n_riders: int = n_riders
        self._pick_up_distance: float = FLOAT_ZERO  # 归属车辆为了接这一单已经行驶的距离
        self._belong_vehicle = None  # 订单归属车辆
        self._have_finish = False  # 订单已经被完成了
        self._real_pick_up_time: int = INT_ZERO  # 车俩实际配分配的时间
        self._real_wait_time: int = INT_ZERO  # 实际等待时间
        self._real_service_time: int = INT_ZERO  # 车辆实际被服务的时间
        self._real_order_distance: float = FLOAT_ZERO  # 车辆被完成过程中多少距离是
        self._real_detour_ratio: float = FLOAT_ZERO  # 实际绕路比例

    @classmethod
    def load_orders_data(cls, start_time: int, time_slot: int, input_file: str):
        """
        从输入的csv文件中读取订单文件并逐个返回到外界
        :param start_time: 起始时间
        :param time_slot: 间隔时间
        :param input_file: csv输入文件
        :return:
        """
        chunk_size = 10000
        order_id = 0
        current_time = start_time
        each_time_slot_orders: Set[Order] = set()
        for csv_iterator in pd.read_table(input_file, chunksize=chunk_size, iterator=True):  # 这么弄主要是为了防止order_data过大
            for line in csv_iterator.values:
                # ["request_time", "wait_time", "pick_index", "drop_index", "order_distance", "order_fare", "detour_ratio"]
                each_order_data = line[0].split(',')
                request_time = int(each_order_data[0])
                wait_time = int(each_order_data[1])
                pick_index = int(each_order_data[2])
                drop_index = int(each_order_data[3])
                order_distance = float(each_order_data[4])
                order_fare = float(each_order_data[5])
                detour_ratio = float(each_order_data[6])
                order = cls(
                    order_id=order_id,
                    pick_location=PickLocation(pick_index),
                    drop_location=DropLocation(drop_index),
                    request_time=request_time,
                    wait_time=wait_time,
                    order_distance=order_distance,
                    order_fare=order_fare,
                    detour_ratio=detour_ratio,
                )
                if request_time < current_time + time_slot:
                    each_time_slot_orders.add(order)
                else:
                    current_time += time_slot
                    yield current_time, each_time_slot_orders
                    each_time_slot_orders.clear()
                    each_time_slot_orders.add(order)
                order_id += 1
        if len(each_time_slot_orders) != 0:
            yield current_time + time_slot, each_time_slot_orders

    def __hash__(self):
        return hash(self._order_id)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            raise Exception("{0} is not {1}".format(other.__class__, self.__class__))
        return other._order_id == self._order_id

    def __repr__(self):
        return "(order_id: {0}, detour_ratio: {1})".format(self._order_id, self._detour_distance / self._order_distance)

    @property
    def order_id(self) -> int:
        return self._order_id

    @property
    def pick_location(self) -> PickLocation:
        return self._pick_location

    @property
    def drop_location(self) -> DropLocation:
        return self._drop_location

    @property
    def request_time(self) -> int:
        return self._request_time

    @property
    def wait_time(self) -> int:
        return self._wait_time

    @property
    def order_distance(self) -> float:
        return self._order_distance

    @property
    def order_fare(self) -> float:
        return self._order_fare

    @property
    def detour_distance(self) -> float:
        return self._detour_distance

    @property
    def pick_up_distance(self) -> float:
        return self._pick_up_distance

    @property
    def n_riders(self) -> int:
        return self._n_riders

    @property
    def belong_vehicle(self):
        return self._belong_vehicle

    @property
    def real_pick_up_time(self) -> int:
        return self._real_pick_up_time

    @property
    def real_order_distance(self) -> float:
        return self._real_order_distance

    @property
    def real_detour_ratio(self) -> float:
        return self._real_detour_ratio

    @property
    def real_wait_time(self) -> int:
        return self._real_wait_time

    @property
    def real_service_time(self) -> int:
        return self._real_service_time

    @property
    def turnaround_time(self) -> int:
        return self._real_wait_time + self._real_service_time

    def set_belong_vehicle(self, vehicle=None):
        self._belong_vehicle = vehicle

    def set_pick_status(self, pick_up_distance: float, real_pick_up_time: int):
        self._pick_up_distance = pick_up_distance
        self._real_pick_up_time = real_pick_up_time
        self._real_wait_time = real_pick_up_time - self._request_time

    def set_drop_status(self, drop_off_distance: float, real_finish_time: int):
        self._real_order_distance = drop_off_distance - self._pick_up_distance
        self._real_detour_ratio = self._real_order_distance / self._order_distance - 1.0
        self._real_service_time = real_finish_time - self._request_time - self._real_wait_time  # 这个订单被完成花费的时间
