#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/11/9
from typing import Set, NoReturn, List

from agent.vehicle import Vehicle
from algorithm.utility import Mechanism
from env.network import Network
from env.order import Order
from env.location import OrderLocation, PickLocation
from utility import singleton
from setting import VEHICLE_SPEED

__all__ = ["Platform"]


def merge_orders(order1: Order, order2: Order, current_time: int, network: Network):
    """
    往order1的路线上插入order2路线
    :param order1:
    :param order2:
    :param current_time:
    :param network:
    :return:
    """
    routes = [
        [order1.pick_location, order2.pick_location, order1.drop_location, order2.drop_location],
        [order1.pick_location, order2.pick_location, order2.drop_location, order1.drop_location],
        [order1.pick_location, order1.drop_location, order2.pick_location, order2.drop_location]
    ]
    for route in routes:
        temp_dist = 0
        temp_pick_dist = dict()
        for index, order_location in enumerate(route):
            belong_order: Order = order_location.belong_order
            if index == 0:
                between_dist = 0.0
            else:
                between_dist = network.get_shortest_distance(route[index-1], route[index])

            temp_dist += between_dist
            if isinstance(order_location, PickLocation):
                if network.is_smaller_bound_distance(temp_dist, (belong_order.request_time + belong_order.wait_time - current_time) * VEHICLE_SPEED):
                    temp_pick_dist[belong_order] = temp_dist
                else:
                    break
            else:
                if not network.is_smaller_bound_distance(temp_dist - temp_pick_dist[belong_order], belong_order.detour_distance + belong_order.order_distance):
                    break
        else:
            return True

    return False


@singleton
class Platform:
    """
    平台
    dispatching_mechanism: 平台的运行的机制
    """
    __slots__ = ["_dispatching_mechanism", "_order_pool"]

    def __init__(self, dispatching_mechanism: Mechanism):
        self._order_pool: Set = set()
        self._dispatching_mechanism: Mechanism = dispatching_mechanism

    def collect_orders(self,  new_orders: Set[Order], current_time: int) -> NoReturn:
        """
        收集这一轮的新订单同时剔除一些已经过期的订单
        :param new_orders: 新的订单集合
        :param current_time: 当前时间
        :return:
        """
        unused_orders = set([order for order in self._order_pool if order.request_time + order.wait_time < current_time])  # 找到已经过期的订单
        self._order_pool -= unused_orders
        self._order_pool |= new_orders

    def remove_dispatched_orders(self) -> NoReturn:
        """
        从订单池子中移除已经得到分发的订单
        :return:
        """
        self._order_pool -= self._dispatching_mechanism.dispatched_orders

    def round_based_process(self, vehicles: List[Vehicle], new_orders: Set[Order], current_time: int, network: Network) -> NoReturn:
        """
        一轮运行过程
        :param vehicles: 车辆
        :param new_orders: 新产生的订单
        :param current_time:  当前时间
        :param network:  环境
        :return:
        """
        #  收集新的订单
        self.collect_orders(new_orders, current_time)

        # 匹配定价
        self._dispatching_mechanism.run(vehicles, self._order_pool, current_time, network)

        # 移除已经分配的订单
        self.remove_dispatched_orders()

    @property
    def order_pool(self) -> Set[Order]:
        return self._order_pool

    @property
    def vehicle_pool(self) -> Set[Vehicle]:
        return self._vehicle_pool

    @property
    def dispatching_mechanism(self) -> Mechanism:
        return self._dispatching_mechanism

    def reset(self):
        """
        平台重置
        """
        self._order_pool.clear()  # 清空订单
        self._dispatching_mechanism.reset()  # 机制自动清空

    @staticmethod
    def merge_orders(new_orders: Set[Order], current_time: int, network: Network):
        n: int = len(new_orders)
        temp_orders = list(new_orders)
        cnt = 0
        for i in range(n):
            for j in range(n):
                if i != j and merge_orders(temp_orders[i], temp_orders[j], current_time, network):
                    cnt += 1
        print(cnt / (n * (n - 1)))

    def get_current_vehicle_number(self):
        return len(self._vehicle_pool)

    def get_current_order_number(self):
        return len(self._order_pool)
