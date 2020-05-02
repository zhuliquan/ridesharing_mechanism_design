#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/11/7
from typing import List, Dict
import numpy as np
from agent.utility import VehicleType
from setting import FLOAT_ZERO, INT_ZERO, POS_INF, NEG_INF, POINT_LENGTH, DISTANCE_EPS
from env.location import OrderLocation, PickLocation, VehicleLocation
from env.network import Network
from env.order import Order
from setting import FIRST_INDEX
from utility import fix_point_length_add, fix_point_length_sub


class RouteInfo:
    """
    路线信息类，包含当前路线是否可行，路线行驶距离，路线的总体绕路比
    """
    __slots__ = ["_is_feasible", "_route_distance", "_order_detour_ratios", "_route_cost", "_route_profit"]

    def __init__(self, is_feasible: bool, route_distance: float, order_detour_ratios: Dict[Order, float]):
        self._is_feasible = is_feasible
        self._route_distance = route_distance
        self._order_detour_ratios = order_detour_ratios
        self._route_cost = None
        self._route_profit = None

    @property
    def is_feasible(self) -> bool:
        return self._is_feasible

    @property
    def route_distance(self) -> float:
        return self._route_distance

    @property
    def order_detour_ratios(self) -> Dict[Order, float]:
        return self._order_detour_ratios

    @property
    def route_cost(self) -> float:
        return self._route_cost

    @property
    def route_profit(self) -> float:
        return self._route_profit

    @route_cost.setter
    def route_cost(self, value: float):
        self._route_cost = value

    @route_profit.setter
    def route_profit(self, value: float):
        self._route_profit = value


class PlanningResult:
    """
    优化返回优化的结果
    """
    __slots__ = ["_route", "_route_cost", "_route_profit", "_is_feasible"]

    def __init__(self, route: List[OrderLocation], route_info: RouteInfo):
        if route is None or route_info is None or not route_info.is_feasible:  # 规划结果不可行
            self._is_feasible = False
        else:
            self._is_feasible = True
            self._route = route
            self._route_cost = route_info.route_cost
            self._route_profit = route_info.route_profit

    @property
    def is_feasible(self) -> bool:
        return self._is_feasible

    @property
    def route(self) -> List[OrderLocation]:
        return self._route

    @property
    def route_cost(self) -> float:
        return self._route_cost

    @property
    def route_profit(self) -> float:
        return self._route_profit


def get_route_info(vehicle_type: VehicleType, route: List[OrderLocation], current_time: int, network: Network) -> RouteInfo:
    """
    一个模拟器，模拟车辆按照一个行驶路线行走，注意这个只是一个模拟器，不会修改车辆任何值，每一次yield 出当前行驶到订单位置，和行驶的距离
    更具当前车的信息，求解一个新的行驶路线的一些信息（每一个订单的绕路比，行驶长度，可行性）
    如果是 在一个时刻 可用的座位数目小于零 或者 不满足接送距离 或者 不满足绕路比 或者 起点数大于结束数 就是不可行 如果行驶长度就是零
    :param vehicle_type：车辆信息
    :param route：行驶路线
    :param current_time: 当前时间
    :param network: 路网
    :return info: 行驶路线信息
    ------
    注意：
    这里面所有操作都不可以改变车辆的实际的值，所有过程都是模拟，车辆实际还没有运行到这些点！！！！！！！
    """
    if len(route) == INT_ZERO:  # 如果是空的行驶路线
        return RouteInfo(True, FLOAT_ZERO, dict())
    old_dists: float = vehicle_type.service_driven_distance
    cur_dists: float = vehicle_type.service_driven_distance
    cur_seats: int = vehicle_type.available_seats
    avg_speed: float = vehicle_type.vehicle_speed

    pick_up_dists_dict: Dict[Order, float] = dict()  # 记录每一个订单在被接到时行驶的距离
    detour_ratios_dict: Dict[Order, float] = dict()  # 记录每一个订单的绕路比
    for i in range(len(route)):
        if i == FIRST_INDEX:
            vehicle_to_order_distance = network.get_shortest_distance(vehicle_type.location, route[i])
        else:
            vehicle_to_order_distance = network.get_shortest_distance(route[i-1], route[i])

        cur_dists += vehicle_to_order_distance
        belong_order: Order = route[i].belong_order
        if isinstance(route[i], PickLocation):
            cur_seats -= belong_order.n_riders
            if cur_seats < 0:  # 座位数目是不可行的
                break
            # 计算接送时间，判断是否可以接到订单
            dll_dists = (belong_order.request_time + belong_order.wait_time - current_time) * avg_speed + old_dists
            if network.is_smaller_bound_distance(cur_dists, dll_dists + DISTANCE_EPS):  # 计算到达时间是否超出于其的要求
                pick_up_dists_dict[belong_order] = cur_dists  # 更新接乘客已经行驶的里程
            else:  # 无法满足最大等待时间
                break
        else:
            cur_seats += belong_order.n_riders
            # 计算绕路比，判断绕路比是否可以满足要求
            real_detour_dist = cur_dists - (pick_up_dists_dict[belong_order] if belong_order in pick_up_dists_dict else belong_order.pick_up_distance) - belong_order.order_distance  # 计算绕路比距离
            if network.is_smaller_bound_distance(FLOAT_ZERO, real_detour_dist + DISTANCE_EPS) and network.is_smaller_bound_distance(real_detour_dist, belong_order.detour_distance + DISTANCE_EPS):
                detour_ratios_dict[belong_order] = (real_detour_dist if real_detour_dist >= FLOAT_ZERO else FLOAT_ZERO) / belong_order.order_distance
            else:  # 无法满足绕路比, 或者绕路比是有问题的路径规划
                break
    else:
        return RouteInfo(True, cur_dists - old_dists, detour_ratios_dict)

    return RouteInfo(False, POS_INF, dict())


def get_route_cost_by_route_info(route_info: RouteInfo, unit_cost: float) -> float:
    """
    结果会保留后两位
    """
    if route_info.is_feasible:
        cost = np.round(unit_cost * route_info.route_distance, POINT_LENGTH)
    else:
        cost = POS_INF
    return cost


def compute_discount_fare(order: Order, detour_ratio: float, discount=0.00025) -> float:
    """
    计算乘客打折费用, 为了激励乘客愿意接受绕路，给予费用上的打折优惠
    :param order: 订单
    :param detour_ratio: 订单的绕路比
    :param discount: 折扣因子 如果是0表示不打折。如果是1 表示完全打折
    """
    return order.order_fare * (1.0 - discount * detour_ratio * detour_ratio)


def get_route_profit_by_route_info(route_info: RouteInfo, unit_cost: float) -> float:
    """
    结果会保留后两位
    """
    if route_info.is_feasible:
        fare = sum([compute_discount_fare(order, detour_ratio) for order, detour_ratio in route_info.order_detour_ratios.items()])
        cost = unit_cost * route_info.route_distance
        profit = fix_point_length_sub(fare, cost)
    else:
        profit = NEG_INF
    return profit


def generate_route_by_insert_pick_drop_location(route: List[OrderLocation], order: Order, i: int, j: int) -> List[OrderLocation]:
    """
    在行驶路线route的i，j处插入订单的起始/终止地生成新的行驶路线
    :param route: 原始路西
    :param order: 订单
    :param i: 起始地的插入点
    :param j: 终止点的插入点
    :return:
    """
    return route[:i] + [order.pick_location] + route[i:j] + [order.drop_location] + route[j:]


def pre_check_need_to_planning(vehicle_type: VehicleType, order: Order, current_time: int, network: Network) -> bool:
    """
    预先检查还有没有必要去进行优化，如果接送距离过大是不用接送的
    :param vehicle_type: 车辆信息
    :param order: 订单
    :param current_time：当前时间
    :param network: 路网
    :return:
    """
    upper_time = order.request_time + order.wait_time - current_time
    vehicle_pick_up_distance = network.compute_vehicle_to_order_distance(vehicle_type.location, order.pick_location)
    if network.is_smaller_bound_distance(vehicle_pick_up_distance, upper_time * vehicle_type.vehicle_speed):
        return True
    else:
        return False
