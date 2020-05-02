#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/10/28
from typing import NoReturn, Union

from setting import FLOAT_ZERO

__all__ = ["GeoLocation", "OrderLocation", "PickLocation", "DropLocation", "VehicleLocation"]


class GeoLocation:
    """
    地理位置类
    """
    __slots__ = ["_osm_index"]

    def __init__(self, osm_index: int):
        """
        :param osm_index: open street map id 字典的索引
        """
        self._osm_index = osm_index

    def __repr__(self):
        return "{0:5}".format(self._osm_index)

    def __hash__(self):
        return hash(self._osm_index)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            raise Exception("{0} is not {1}".format(other.__class__, self.__class__))
        return other._osm_index == self._osm_index

    @property
    def osm_index(self) -> int:
        return self._osm_index

    def to_file_index(self) -> int:
        return self._osm_index


class OrderLocation(GeoLocation):
    __slots__ = ["_belong_order"]

    def __init__(self, osm_index: int):
        """
        :param osm_index:
        """
        super().__init__(osm_index)
        self._belong_order = None

    def __hash__(self):
        return hash(self._belong_order.order_id)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            raise Exception("{0} is not {1}".format(other.__class__, self.__class__))
        return self._belong_order.order_id == other._belong_order.order_id

    @property
    def belong_order(self):
        return self._belong_order

    def set_belong_order(self, order) -> NoReturn:
        self._belong_order = order


class PickLocation(OrderLocation):
    __slots__ = []

    def __init__(self, osm_index: int):
        super().__init__(osm_index)

    def __hash__(self):
        return hash((self._belong_order.order_id, "P"))

    def __eq__(self, other):
        return isinstance(other, PickLocation) and super().__eq__(other)

    def __repr__(self):
        return "({0},{1:<5})".format("PICK", self._belong_order.order_id)


class DropLocation(OrderLocation):
    __slots__ = []

    def __init__(self, osm_index: int):
        super().__init__(osm_index)

    def __hash__(self):
        return hash((self._belong_order.order_id, "D"))

    def __eq__(self, other):
        return isinstance(other, DropLocation) and super().__eq__(other)

    def __repr__(self):
        return "({0}, {1:<5})".format("DROP", self._belong_order.order_id)


class VehicleLocation(GeoLocation):
    """
    由于车辆很有可能行驶到两个节点之间啊，所以车辆的位置始终表示成为
    （地理节点， 一段距离， 下一个地理节点）的形式
    表示车辆处于从当前节点到下一个节点还有行驶一段距离的位置
    """
    __slots__ = ["_goal_index", "_is_between", "_driven_distance"]

    def __init__(self, osm_index: int, goal_index=None, is_between=False, driven_distance=FLOAT_ZERO):
        super().__init__(osm_index)
        self._goal_index = goal_index
        self._is_between = is_between  # is_between 为True表示车辆在两个节点之间，False表示不再两个节点
        self._driven_distance = driven_distance  # driven_distance 表示车辆在osm_index到goal_index节点之间已经行驶的距离

    def __repr__(self):
        return "({0:<5} driven distance:{1} goal index:{2})".format(self._osm_index, self._driven_distance, self._goal_index)

    @property
    def goal_index(self) -> Union[int, None]:
        return self._goal_index

    @property
    def driven_distance(self) -> float:
        return self._driven_distance

    @property
    def is_between(self) -> bool:
        return self._is_between

    def reset(self) -> NoReturn:
        """
        当车辆不在两个节点之间，而就在一个节点之上的时候就回触发这个函数
        :return:
        """
        self._goal_index = None
        self._is_between = False
        self._driven_distance = FLOAT_ZERO

    def set_location(self, osm_index: int, driven_distance=FLOAT_ZERO, goal_index=None) -> NoReturn:
        if goal_index is None or osm_index == goal_index:
            self._osm_index = osm_index
            if self._goal_index is not None:  # 不为空才需要重新设定
                self.reset()
        else:
            self._osm_index = osm_index
            self._is_between = True
            self._driven_distance = driven_distance
            self._goal_index = goal_index

    def increase_driven_distance(self, distance: float):
        self._driven_distance += distance

    def decrease_driven_distance(self, distance: float):
        self._driven_distance -= distance
