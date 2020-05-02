#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/10/22
"""
车辆可以被分为两类
第1类：
    出租车，这一类车辆是没有固定的目的地和结束时间
第2类：
    私家车，这一类车辆是一种固定的目的地和结束时间的车辆
"""
from typing import List, NoReturn, Dict, Set
import pandas as pd

from agent.proxy_bidder import ProxyBidder
from algorithm.route_planning.planner import RoutePlanner
from algorithm.route_planning.utility import PlanningResult
from agent.utility import OrderBid, VehicleType
from setting import FIRST_INDEX, FLOAT_ZERO, INT_ZERO
from env.location import DropLocation, PickLocation, VehicleLocation, OrderLocation
from env.network import Network
from env.order import Order
from utility import fix_point_length_add

__all__ = ["Vehicle"]


class Vehicle:
    """
    车辆
    vehicle_id: 车辆id
    location: 车辆当前位置
    available_seats:  车辆剩下的位置数目
    unit_cost: 车俩的单位行驶成本
    route: 车辆的自身的行驶路线 实质上就是包含一系列订单的起始位置的序列
    random_driven_distance: 车辆随机行驶的距离
    service_driven_distance: 车辆为了服务行驶的距离
    is_activated: 车辆是否已经激活
    """
    __slots__ = ["_vehicle_id", "_is_activated", "_route",  "_vehicle_type", "_finish_orders_number", "_earn_reward", "_earn_payoff"]
    proxy_bidder: ProxyBidder = None  # 车辆的代理投标者
    route_planner: RoutePlanner = None  # 车辆的路线规划器

    def __init__(self, vehicle_id: int, location: VehicleLocation, available_seats: int, unit_cost: float):
        self._vehicle_id: int = vehicle_id  # 车辆唯一标识
        self._is_activated: bool = True  # 车辆是否处于激活状态，默认车是激活状态
        self._route = list()  # 车辆的行驶路线
        self._vehicle_type = VehicleType(
            location=location,  # 车辆当前的位置
            available_seats=available_seats,  # 剩下的座位数目
            unit_cost=unit_cost,  # 单位行驶成本
            service_driven_distance=FLOAT_ZERO,  # 车俩为了服务行驶的距离
            random_driven_distance=FLOAT_ZERO  # 车辆随机行驶的距离
        )
        self._finish_orders_number: int = INT_ZERO
        self._earn_reward: float = FLOAT_ZERO
        self._earn_payoff: float = FLOAT_ZERO

    @staticmethod
    def set_vehicle_speed(vehicle_speed: float) -> NoReturn:
        VehicleType.set_vehicle_speed(vehicle_speed)

    @staticmethod
    def set_could_drive_distance(could_drive_distance: float) -> NoReturn:
        VehicleType.set_could_drive_distance(could_drive_distance)

    @classmethod
    def set_proxy_bidder(cls, proxy_bidder: ProxyBidder) -> NoReturn:
        cls.proxy_bidder = proxy_bidder

    @classmethod
    def set_route_planner(cls, route_planner: RoutePlanner) -> NoReturn:
        cls.route_planner = route_planner

    @property
    def assigned_order_number(self) -> int:
        return self.vehicle_type.assigned_order_number

    @property
    def vehicle_id(self) -> int:
        return self._vehicle_id

    @property
    def is_activated(self) -> bool:
        """
        返回当前车俩是否存货
        :return:
        """
        return self._is_activated

    @property
    def vehicle_type(self) -> VehicleType:
        """
        返回车辆类型 （包括车辆的位置，单位成本，可用座位，服务行驶距离，随机行驶距离）
        :return:
        """
        return self._vehicle_type

    @property
    def unit_cost(self) -> float:
        """
        返回单位成本
        :return:
        """
        return self._vehicle_type.unit_cost

    @property
    def available_seats(self) -> int:
        """
        返回车辆当前剩余的座位
        :return:
        """
        return self._vehicle_type.available_seats

    @property
    def route(self) -> List[OrderLocation]:
        """
        返回车俩行驶路线
        :return:
        """
        return self._route

    @property
    def location(self) -> VehicleLocation:
        """
        返回车辆的当前的位置
        :return:
        """
        return self._vehicle_type.location

    @property
    def service_driven_distance(self) -> float:
        """
        返回车俩为了服务行驶的距离
        :return:
        """
        return self._vehicle_type.service_driven_distance

    @property
    def random_driven_distance(self) -> float:
        """
        返回车辆随机行驶的距离
        :return:
        """
        return self._vehicle_type.random_driven_distance

    @property
    def could_drive_distance(self) -> float:
        """
        返回车辆在一个时刻可以移动的距离，这个距离是最小值其实车辆可能行驶更多距离
        :return:
        """
        return VehicleType.could_drive_distance

    @property
    def vehicle_speed(self) -> float:
        """
        返回车辆速度
        :return:
        """
        return VehicleType.vehicle_speed

    @property
    def finish_orders_number(self) -> int:
        return self._finish_orders_number

    @property
    def earn_reward(self) -> float:
        return self._earn_reward

    @property
    def earn_profit(self) -> float:
        return self._earn_payoff

    @property
    def have_service_mission(self) -> bool:
        """
        返回当前车辆是否有服务订单的任务在身
        :return:
        """
        return len(self.route) != INT_ZERO

    def get_bid(self, order: Order, current_time: int, network: Network) -> OrderBid:
        order_bid = self.proxy_bidder.get_bid(self._vehicle_type, self.route_planner, self._route, order, current_time, network)
        return order_bid

    def get_bids(self, orders: Set[Order], current_time: int, network: Network) -> Dict[Order, OrderBid]:
        order_bids = self.proxy_bidder.get_bids(self._vehicle_type, self.route_planner, self._route, orders, current_time, network)
        return order_bids

    def route_planning(self, order: Order, current_time: int, network: Network) -> PlanningResult:
        return self.route_planner.planning(self._vehicle_type, self.route, order, current_time, network)

    def drive_on_random(self, network: Network) -> NoReturn:
        """
        车辆在路上随机行驶
        :param network: 路网
        :return:
        ------
        注意：
        不要那些只可以进去，不可以出来的节点
        如果车辆就正好在一个节点之上，那么随机选择一个节点到达，如果不是这些情况就在原地保持不动
        """
        self.increase_random_distance(network.drive_on_random(self.location, self.could_drive_distance))

    def drive_on_route(self, current_time: int, network: Network) -> List[Order]:
        """
        车辆自己按照自己的行驶路线
        :param current_time: 当前时间
        :param network: 路网
        """
        un_covered_location_index = FIRST_INDEX  # 未完成订单坐标的最小索引
        g = network.drive_on_route(self.location, self.route, self.could_drive_distance)  # 开启车辆位置更新的生成器
        now_time: float = current_time
        _finish_orders: List[Order] = list()  # 这一轮完成的订单
        for is_access, covered_index, order_location, vehicle_to_order_distance in g:
            # is_access 表示是否可以到达 order_location
            # covered_index 表示车辆当前覆盖的路线规划列表索引
            # order_location 表示当前可以访问的订单位置
            # vehicle_to_order_distance 表示车辆到 order_location 可以行驶的距离

            self.increase_service_distance(vehicle_to_order_distance)  # 更新车辆服务行驶的距离
            now_time = now_time + vehicle_to_order_distance / self.vehicle_speed
            un_covered_location_index = covered_index + 1  # 更新未完成订单的情况
            if is_access:  # 如果当前订单是可以到达的情况
                belong_order: Order = order_location.belong_order
                if isinstance(order_location, PickLocation):
                    belong_order.set_pick_status(self.service_driven_distance, int(now_time))  # 更新当前订单的接送行驶距离
                    self.decrease_available_seats(belong_order.n_riders)
                if isinstance(order_location, DropLocation):
                    belong_order.set_drop_status(self.service_driven_distance, int(now_time))
                    self.increase_available_seats(belong_order.n_riders)
                    self._finish_orders_number += 1
                    _finish_orders.append(belong_order)
        if un_covered_location_index != FIRST_INDEX:  # 只有有变化才更新路径
            self.set_route(self.route[un_covered_location_index:])
        return _finish_orders

    def set_route(self, route: List[OrderLocation]) -> NoReturn:
        self._route = route

    def decrease_available_seats(self, n_riders: int) -> NoReturn:
        self._vehicle_type.available_seats -= n_riders

    def increase_available_seats(self, n_riders: int) -> NoReturn:
        self._vehicle_type.available_seats += n_riders

    def increase_earn_reward(self, reward: float):
        self._earn_reward = fix_point_length_add(self._earn_reward, reward)

    def increase_earn_profit(self, profit: float):
        self._earn_payoff = fix_point_length_add(self._earn_payoff, profit)

    def increase_service_distance(self, additional_distance: float) -> NoReturn:
        self._vehicle_type.service_driven_distance += additional_distance

    def increase_random_distance(self, additional_distance: float) -> NoReturn:
        self._vehicle_type.random_driven_distance += additional_distance

    def __repr__(self):
        return "id: {0} location: {1} available_seats: {2} unit_cost: {3} route: {4}". \
            format(self.vehicle_id, self.location, self.available_seats, self.unit_cost, self.route)

    def __hash__(self):
        return hash(self.vehicle_id)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            raise Exception("{0} is not {1}".format(other.__class__, self.__class__))
        return isinstance(other, self.__class__) and self.vehicle_id == other.vehicle_id

    @classmethod
    def load_vehicles_data(cls, vehicle_speed: float, time_slot: int, proxy_bidder: ProxyBidder, route_planner: RoutePlanner, input_file) -> List:
        """
        用于导入已经生成的车辆数据，并加工用于模拟
        :param vehicle_speed: 车辆速度
        :param time_slot: 表示
        :param proxy_bidder: 代理投标者
        :param route_planner: 路线规划器
        :param input_file: 路网
        :return:
        """
        cls.set_vehicle_speed(vehicle_speed)  # 初初始化车辆速度
        cls.set_could_drive_distance(vehicle_speed * time_slot)  # 初始化车辆的行驶
        cls.set_proxy_bidder(proxy_bidder)
        cls.set_route_planner(route_planner)
        vehicle_raw_data = pd.read_csv(input_file)
        vehicle_number = vehicle_raw_data.shape[0]
        vehicles = []
        for vehicle_id in range(vehicle_number):
            each_vehicle_data = vehicle_raw_data.iloc[vehicle_id, :]
            vehicles.append(cls(vehicle_id, VehicleLocation(int(each_vehicle_data["location_index"])), each_vehicle_data["seats"], each_vehicle_data["unit_cost"]))
        return vehicles
