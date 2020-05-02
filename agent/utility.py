#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/11/13
from typing import List
import numpy as np
from env.location import OrderLocation, VehicleLocation


class OrderBid:
    """
    用户投标
    bid_value: 投标价值
    bid_route: 投标对应的行驶路线
    additional_cost: 插入订单之后对应的新增成本
    """
    __slots__ = ["_bid_value", "_bid_route", "_additional_cost"]

    def __init__(self, _bid_value: float, _bid_route: List[OrderLocation], _additional_cost: float):
        self._bid_value = _bid_value
        self._bid_route = _bid_route
        self._additional_cost = _additional_cost

    @property
    def bid_value(self) -> float:
        return self._bid_value

    @property
    def bid_route(self) -> List[OrderLocation]:
        return self._bid_route

    @property
    def additional_cost(self) -> float:
        return self._additional_cost


class VehicleType:
    """
    vehicle 用这个类与外界进行交互
    """
    __slots__ = ["_location", "_available_seats", "_unit_cost", "_service_driven_distance", "_random_driven_distance", "_assigned_order_number"]

    vehicle_speed: float = None  # 车辆的平均速度
    could_drive_distance: float = None  # 一个分配时间可以行驶的距离

    def __init__(self, location: VehicleLocation, available_seats: int, unit_cost: float, service_driven_distance: float, random_driven_distance: float):
        self._location = location
        self._available_seats = available_seats
        self._unit_cost = unit_cost
        self._service_driven_distance = service_driven_distance
        self._random_driven_distance = random_driven_distance
        self._assigned_order_number = 0  # 已经分配的订单数目

    @property
    def assigned_order_number(self) -> int:
        return self._assigned_order_number

    @assigned_order_number.setter
    def assigned_order_number(self, value: int):
        self._assigned_order_number = value

    @property
    def location(self) -> VehicleLocation:
        return self._location

    @property
    def available_seats(self) -> int:
        return self._available_seats

    @available_seats.setter
    def available_seats(self, seats: int):
        self._available_seats = seats

    @property
    def unit_cost(self) -> float:
        return self._unit_cost

    @property
    def service_driven_distance(self) -> float:
        return self._service_driven_distance

    @service_driven_distance.setter
    def service_driven_distance(self, distance: float):
        self._service_driven_distance = distance

    @property
    def random_driven_distance(self) -> float:
        return self._random_driven_distance

    @random_driven_distance.setter
    def random_driven_distance(self, distance: float):
        self._random_driven_distance = distance

    @classmethod
    def set_vehicle_speed(cls, vehicle_speed: float):
        cls.vehicle_speed = np.round(vehicle_speed)

    @classmethod
    def set_could_drive_distance(cls, could_drive_distance: float):
        could_drive_distance = np.round(could_drive_distance)
        cls.could_drive_distance = could_drive_distance
