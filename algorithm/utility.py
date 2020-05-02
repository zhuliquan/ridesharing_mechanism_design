#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/10/25
from collections import defaultdict
from typing import List, Set, NoReturn

from agent.vehicle import Vehicle
from env.location import OrderLocation
from env.network import Network
from env.order import Order
from setting import FLOAT_ZERO
from utility import fix_point_length_add

__all__ = ["Mechanism"]


class DispatchedResult:
    __slots__ = ["_orders", "_driver_route", "_driver_reward", "_driver_payoff"]

    def __init__(self):
        self._orders: List[Order] = list()
        self._driver_route = None
        self._driver_reward: float = FLOAT_ZERO
        self._driver_payoff: float = FLOAT_ZERO

    @property
    def orders(self) -> List[Order]:
        return self._orders

    @property
    def driver_route(self) -> List[OrderLocation]:
        return self._driver_route

    @property
    def driver_reward(self) -> float:
        return self._driver_reward

    @property
    def driver_payoff(self) -> float:
        return self._driver_payoff

    def add_order(self, order: Order, reward: float, payoff: float):
        self._orders.append(order)
        self._driver_reward = fix_point_length_add(self._driver_reward, reward)
        self._driver_payoff = fix_point_length_add(self._driver_payoff, payoff)

    def set_route(self, route: List[OrderLocation]):
        self._driver_route = route


class Mechanism:
    """
    分配方法类
    供需比 feasible_vehicle_number / feasible_order_number
    dispatched_orders: 已经得到分配的订单
    dispatched_vehicles: 订单分发中获得订单的车辆集合
    dispatched_result: 分发结果, 包括车辆获得哪些订单和回报
    bidding_time: 投标时间
    running_time: 算法分配运行的时间
    social_welfare：此轮分配的社会福利
    social_cost: 分配订单的车辆的运行成本
    total_driver_rewards: 分配订单车辆的总体支付
    total_driver_payoffs: 分配订单车辆的总效用和
    platform_profit: 平台在此轮运行中的收益
    """
    __slots__ = [
        "_dispatched_orders",
        "_dispatched_vehicles",
        "_dispatched_results",
        "_social_welfare",
        "_social_cost",
        "_total_driver_rewards",
        "_total_driver_payoffs",
        "_platform_profit",
        "_bidding_time",
        "_running_time"]

    def __init__(self):
        self._dispatched_vehicles: Set[Vehicle] = set()
        self._dispatched_orders: Set[Order] = set()
        self._dispatched_results: defaultdict = defaultdict(DispatchedResult)
        self._social_welfare: float = FLOAT_ZERO
        self._social_cost: float = FLOAT_ZERO
        self._total_driver_rewards: float = FLOAT_ZERO
        self._total_driver_payoffs: float = FLOAT_ZERO
        self._platform_profit: float = FLOAT_ZERO
        self._bidding_time: float = FLOAT_ZERO  # 这个是比较细化的时间
        self._running_time: float = FLOAT_ZERO  # 这个是比较细化的时间

    def reset(self):
        self._dispatched_vehicles.clear()
        self._dispatched_orders.clear()
        self._dispatched_results.clear()
        self._social_welfare = FLOAT_ZERO
        self._social_cost = FLOAT_ZERO
        self._total_driver_rewards = FLOAT_ZERO
        self._total_driver_payoffs = FLOAT_ZERO
        self._platform_profit = FLOAT_ZERO
        self._bidding_time = FLOAT_ZERO
        self._running_time = FLOAT_ZERO

    def run(self, vehicles: List[Vehicle], orders: Set[Order], current_time: int, network: Network) -> NoReturn:
        raise NotImplementedError  # 后续代码还需要自己实现

    @property
    def dispatched_vehicles(self) -> Set[Vehicle]:
        return self._dispatched_vehicles

    @property
    def dispatched_orders(self) -> Set[Order]:
        return self._dispatched_orders

    @property
    def dispatched_results(self) -> defaultdict:
        return self._dispatched_results

    @property
    def social_welfare(self) -> float:
        return self._social_welfare

    @property
    def social_cost(self) -> float:
        return self._social_cost

    @property
    def total_driver_rewards(self) -> float:
        return self._total_driver_rewards

    @property
    def total_driver_payoffs(self) -> float:
        return self._total_driver_payoffs

    @property
    def platform_profit(self) -> float:
        return self._platform_profit

    @property
    def bidding_time(self) -> float:
        return self._bidding_time

    @property
    def running_time(self) -> float:
        return self._running_time
