#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/11/7
from typing import List, Dict
from agent.utility import VehicleType
from algorithm.route_planning.optimizer import Optimizer
from algorithm.route_planning.utility import PlanningResult
from algorithm.route_planning.utility import RouteInfo
from algorithm.route_planning.utility import generate_route_by_insert_pick_drop_location, pre_check_need_to_planning, get_route_info
from env.location import OrderLocation, PickLocation, VehicleLocation, GeoLocation
from env.network import Network
from env.order import Order
from setting import FLOAT_ZERO, INT_ZERO, POS_INF
from utility import is_enough_small

__all__ = ["RoutePlanner", "InsertingPlanner", "ReschedulingPlanner"]


class RoutePlanner:
    __slots__ = ["_optimizer", "_corresponding_optimal_distance"]

    def __init__(self, optimizer: Optimizer):
        """
        :param optimizer: 路规划优化器
        """
        self._optimizer = optimizer
        self._corresponding_optimal_distance = POS_INF

    def reset(self):
        self._optimizer.reset()
        self._corresponding_optimal_distance = POS_INF

    def planning(self, vehicle_info: VehicleType, old_route: List[OrderLocation], order: Order, current_time: int, network: Network) -> PlanningResult:
        """
        利用车辆类型和已有的行驶路线规划将新订单插入后的行驶路线
        :param vehicle_info: 车辆信息
        :param old_route: 行驶路线
        :param order: 订单
        :param current_time: 当前时间
        :param network: 路网
        ------
        注意：
        这里面所有操作都不可以改变自身原有的变量的值 ！！！！！
        """
        raise NotImplementedError

    def summary_planning_result(self) -> PlanningResult:
        optimal_route = self._optimizer.optimal_route
        optimal_route_info = self._optimizer.optimal_route_info
        return PlanningResult(optimal_route, optimal_route_info)


class InsertingPlanner(RoutePlanner):
    """
    这个路线规划框架是 微软亚洲研究院 在 ICDE2013 中的论文里面采用的方法
    论文名称是 T-Share: A Large-Scale Dynamic Taxi Ridesharing Service T-Share
    该方法是保证原有的订单起始点的相对顺序不变，然后将新订单的起始位置和结束位置插入到原先的行驶路线中。
    时间复杂度为 O(n^2*m) n为原先订单起始位置数目，m为进行优化的时间复度
    进阶版本： 我们还采用了An Efﬁcient Insertion Operator in Dynamic Ridesharing Services (ICDE2019) 里面的方法去剪枝 使得算法复杂度
    这种插入方法可以用于最小化成本，不可以做到最大化利润！！！！
    """
    __slots__ = ["optimal_i", "optimal_j"]

    def reset(self):
        super(InsertingPlanner, self).reset()
        self.optimal_i = -1
        self.optimal_j = -1

    def __init__(self, optimizer: Optimizer):
        """
        :param optimizer: 路径优化器可以争对每一个输入的行驶路线优化内部的最优路径 选项MaximizeProfitOptimizer/MinimizeCostOptimizer
        """
        super(InsertingPlanner, self).__init__(optimizer)
        self.optimal_i = -1
        self.optimal_j = -1

    def planning1(self, vehicle_type: VehicleType, old_route: List[OrderLocation], order: Order, current_time: int, network: Network):
        n = len(old_route)
        for i in range(n + 1):
            for j in range(i, n + 1):
                new_route = generate_route_by_insert_pick_drop_location(old_route, order, i, j)
                new_route_info = get_route_info(vehicle_type, new_route, current_time, network)
                self._optimizer.optimize(new_route, new_route_info, vehicle_type.unit_cost)

    def planning2(self, vehicle_type: VehicleType, old_route: List[OrderLocation], order: Order, current_time: int, network):

        def _recursion(pre_loc: GeoLocation, k1: int, k2: int, seats: int, drive_dists: float, result: List[int]):
            if k1 == len(old_route) and k2 == len(rem_list):
                if drive_dists - vehicle_type.service_driven_distance < self._corresponding_optimal_distance:
                    self._corresponding_optimal_distance = drive_dists - vehicle_type.service_driven_distance
                    self.optimal_i = result[0]
                    self.optimal_j = result[1]
            elif is_enough_small((drive_dists - vehicle_type.service_driven_distance), self._corresponding_optimal_distance):
                if k1 == len(old_route):  # 只可以插入新的订单节点
                    locations = [(k1, k2 + 1, rem_list[k2])]
                elif k2 == 2:  # 只可以插入老的路线的节点
                    locations = [(k1 + 1, k2, old_route[k1])]
                else:
                    locations = [(k1, k2 + 1, rem_list[k2]), (k1 + 1, k2, old_route[k1])]

                for n_k1, n_k2, o_loc in locations:
                    b_o: Order = o_loc.belong_order
                    arr = drive_dists + network.get_shortest_distance(pre_loc, o_loc)
                    if isinstance(o_loc, PickLocation):
                        dll = (b_o.request_time + b_o.wait_time - current_time) * vehicle_type.vehicle_speed + vehicle_type.service_driven_distance
                        if seats < b_o.n_riders or not network.is_smaller_bound_distance(arr, dll):
                            continue
                        if n_k2 != k2:
                            result[k2] = k1
                        pick_up_dists_dict[b_o] = arr
                        _recursion(o_loc, n_k1, n_k2, seats - b_o.n_riders, arr, result)
                        pick_up_dists_dict.pop(b_o)
                    else:
                        dll = (pick_up_dists_dict[b_o] if b_o in pick_up_dists_dict else b_o.pick_up_distance) + b_o.detour_distance + b_o.order_distance
                        if not network.is_smaller_bound_distance(arr, dll):
                            continue
                        if n_k2 != k2:
                            result[k2] = k1
                        _recursion(o_loc, n_k1, n_k2, seats + b_o.n_riders, arr, result)

        pick_up_dists_dict: Dict[Order, float] = dict()
        rem_list = [order.pick_location, order.drop_location]

        _recursion(vehicle_type.location, 0, 0, vehicle_type.available_seats, vehicle_type.service_driven_distance, [-1, -1])
        if self._corresponding_optimal_distance < POS_INF:
            new_route = generate_route_by_insert_pick_drop_location(old_route, order, self.optimal_i, self.optimal_j)
            new_route_info = RouteInfo(True, self._corresponding_optimal_distance, {})
            self._optimizer.optimize(new_route, new_route_info, vehicle_type.unit_cost)  # 优化器进行优化

    def planning(self, vehicle_type: VehicleType, old_route: List[OrderLocation], order: Order, current_time: int, network: Network) -> PlanningResult:
        self.reset()  # 优化器初始化！！！！
        if pre_check_need_to_planning(vehicle_type, order, current_time, network):  # 人数都不满足要求不用往后执行
            self.planning2(vehicle_type, old_route, order, current_time, network)
        return super(InsertingPlanner, self).summary_planning_result()


class ReschedulingPlanner(RoutePlanner):
    """
    这个路线规划框架是 Mohammad Asghari 在 SIGSPATIAL-16 中论文里面采用的方法
    论文名称是 Price-aware Real-time Ride-sharing at Scale An Auction-based Approach
    该方法可以允许打乱原先的行驶路线的订单接送顺序，插入新订单的的起始位置。
    时间复杂度为 O(n!m) n为原先订单起始位置数目，m为进行优化的时间复度
    这一种方法是可以完全使用最小化成本比和最大化利润两种优化方案
    """
    __slots__ = []

    def __init__(self, optimizer: Optimizer):
        super().__init__(optimizer)

    def planning(self, vehicle_type: VehicleType, old_route: List[OrderLocation], order: Order, current_time: int, network: Network) -> PlanningResult:

        def _generate_remain_loc_list() -> List[OrderLocation]:
            """
            构造remain_list列表，只包含订单的起始点或者单独的订单终点
            """
            _order_set = set()
            _rem_loc_list = list()
            for order_location in old_route:  # 人数都不满足要求不用往后执行
                if isinstance(order_location, PickLocation):  # order_location 是一个订单的起始点直接加入
                    _rem_loc_list.append(order_location)
                    _order_set.add(order_location.belong_order)
                elif order_location.belong_order not in _order_set:  # 如果这一单是只有起始点的就直接加入
                    _rem_loc_list.append(order_location)
            _rem_loc_list.append(order.pick_location)
            return _rem_loc_list

        def _recursion(_cur_loc_list: List[OrderLocation], _rem_loc_list: List[OrderLocation], seats: int, drive_dists: float):
            """
            递归函数，递归探索最优路劲
            :param _cur_loc_list: 当前已经探索的订单起始地
            :param _rem_loc_list: 当前还没有探索的订单起始地
            :param seats: 当前剩余座位数目
            :param drive_dists: 当前行驶的距离
            """
            if len(_rem_loc_list) == INT_ZERO:
                self._optimizer.optimize(_cur_loc_list.copy(), RouteInfo(True, drive_dists - old_dists, detour_ratios_dict.copy()), unit_cost)
                self._corresponding_optimal_distance = min(self._corresponding_optimal_distance, self._optimizer.optimal_route_info.route_distance)
            elif is_enough_small(drive_dists - old_dists, self._corresponding_optimal_distance):
                for i, o_loc in enumerate(_rem_loc_list):
                    v2o_dist = (network.get_shortest_distance(v_loc, o_loc) if len(_cur_loc_list) == INT_ZERO else network.get_shortest_distance(_cur_loc_list[-1], o_loc))
                    arr = drive_dists + v2o_dist
                    belong_o: Order = o_loc.belong_order
                    _cur_loc_list.append(o_loc)
                    if isinstance(o_loc, PickLocation):
                        dll = (belong_o.request_time + belong_o.wait_time - current_time) * avg_speed + old_dists
                        if seats - belong_o.n_riders >= INT_ZERO and network.is_smaller_bound_distance(arr, dll):
                            # 人数满足要求且不超过最大等待时间
                            _rem_list_copy = _rem_loc_list[:i] + _rem_loc_list[i + 1:]
                            _rem_list_copy.append(belong_o.drop_location)
                            pick_up_dists_dict[belong_o] = arr
                            _recursion(_cur_loc_list, _rem_list_copy, seats - belong_o.n_riders, arr)
                            pick_up_dists_dict.pop(belong_o)
                    else:
                        real_detour_dist = arr - (pick_up_dists_dict[belong_o] if belong_o in pick_up_dists_dict else belong_o.pick_up_distance) - belong_o.order_distance
                        if network.is_smaller_bound_distance(FLOAT_ZERO, real_detour_dist) and network.is_smaller_bound_distance(real_detour_dist, belong_o.detour_distance):
                            # 绕路满足要求
                            _rem_list_copy = _rem_loc_list[:i] + _rem_loc_list[i + 1:]
                            detour_ratios_dict[belong_o] = (real_detour_dist if real_detour_dist >= FLOAT_ZERO else FLOAT_ZERO) / belong_o.order_distance
                            _recursion(_cur_loc_list, _rem_list_copy, seats + belong_o.n_riders, arr)
                    _cur_loc_list.pop()

        self.reset()  # 优化器初始化！！！！
        if pre_check_need_to_planning(vehicle_type, order, current_time, network):  # 人数都不满足要求不用往后执行
            pick_up_dists_dict: Dict[Order, float] = dict()
            detour_ratios_dict: Dict[Order, float] = dict()
            avg_speed: float = vehicle_type.vehicle_speed
            old_dists: float = vehicle_type.service_driven_distance
            unit_cost: float = vehicle_type.unit_cost
            v_loc: VehicleLocation = vehicle_type.location
            _recursion(list(), _generate_remain_loc_list(), vehicle_type.available_seats, vehicle_type.service_driven_distance)
        return super(ReschedulingPlanner, self).summary_planning_result()
