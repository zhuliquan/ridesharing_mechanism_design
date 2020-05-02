#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/11/7
""""
这个类属于路线规划类的辅助类
"""
from typing import NoReturn, List

from algorithm.route_planning.utility import RouteInfo
from algorithm.route_planning.utility import get_route_cost_by_route_info, get_route_profit_by_route_info
from setting import POS_INF, NEG_INF
from env.location import OrderLocation

__all__ = ["MaximizeProfitOptimizer", "MinimizeCostOptimizer", "Optimizer"]


class Optimizer:
    __slots__ = ["_optimal_value", "_optimal_route", "_optimal_route_info"]

    def __init__(self, best_value: float):
        self._optimal_value = best_value
        self._optimal_route = None
        self._optimal_route_info = None

    def reset(self):
        self._optimal_route = None
        self._optimal_route_info = None

    def optimize(self, route: List[OrderLocation], route_info: RouteInfo, unit_cost: float, **other_info) -> NoReturn:
        """
        不断记录新的最优优化值
        :param route: 行驶路线
        :param route_info: 路线规划信息
        :param unit_cost: 单位成本
        :return:
        """
        raise NotImplementedError

    @property
    def optimal_value(self) -> float:
        return self._optimal_value

    @property
    def optimal_route(self) -> List[OrderLocation]:
        return self._optimal_route

    @property
    def optimal_route_info(self) -> RouteInfo:
        return self._optimal_route_info


class MinimizeCostOptimizer(Optimizer):
    __slots__ = []

    def __init__(self):
        super(MinimizeCostOptimizer, self).__init__(POS_INF)  # 这里面cost是要去进行优化的目标

    def reset(self) -> NoReturn:
        """
        初始化优化器保存的最优值
        由于需要最小化成本，所以将最优值初始化为无穷大，将路线规划初始化空的序列
        """
        super(MinimizeCostOptimizer, self).reset()
        self._optimal_value = POS_INF

    def optimize(self, route: List[OrderLocation], route_info: RouteInfo, unit_cost: float, **other_info) -> NoReturn:
        if route_info.is_feasible:
            route_info.route_cost = get_route_cost_by_route_info(route_info, unit_cost)
            if self._optimal_value > route_info.route_cost:  # 这里不考虑浮点数精度问题，如果只是一点变好是没有必要优化的
                self._optimal_value = route_info.route_cost
                self._optimal_route = route
                self._optimal_route_info = route_info


class MaximizeProfitOptimizer(Optimizer):
    __slots__ = []

    def __init__(self):
        super(MaximizeProfitOptimizer, self).__init__(NEG_INF)  # 这里面profit是要去进行优化的目标

    def reset(self) -> NoReturn:
        """
        初始化优化器保存的最优值
        由于需要最大化利润，所以将最优值初始化为无穷小，将路线规划初始化空的序列
        """
        super(MaximizeProfitOptimizer, self).reset()
        self._optimal_value = NEG_INF

    def optimize(self, route: List[OrderLocation], route_info: RouteInfo, unit_cost: float, **other_info) -> NoReturn:
        if route_info.is_feasible:
            route_info.route_profit = get_route_profit_by_route_info(route_info, unit_cost)
            route_info.route_cost = get_route_cost_by_route_info(route_info, unit_cost)
            if self._optimal_value < route_info.route_profit:  # 这里不考虑浮点数精度问题，如果只是一点变好是没有必要优化的
                self._optimal_value = route_info.route_profit
                self._optimal_route = route
                self._optimal_route_info = route_info
