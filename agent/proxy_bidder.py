#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/10/27
from typing import Set, Dict, List
from agent.utility import OrderBid, VehicleType
from algorithm.route_planning.planner import RoutePlanner
from algorithm.route_planning.utility import get_route_info, get_route_cost_by_route_info, get_route_profit_by_route_info
from env.location import OrderLocation
from env.network import Network
from env.order import Order
from utility import fix_point_length_sub

__all__ = ["ProxyBidder", "AdditionalCostBidder", "AdditionalProfitBidder"]


class ProxyBidder:
    __slots__ = []

    def get_bid(self, vehicle_type: VehicleType, route_planner: RoutePlanner, old_route: List[OrderLocation], order: Order, current_time: int, network: Network, **other_info) -> OrderBid:
        """
        如果投标不合理就会返回None
        :param vehicle_type: 车辆当前信息
        :param route_planner: 路线规划器
        :param old_route: 车辆行驶路线
        :param order: 订单
        :param current_time: 当前时间
        :param network: 路网
        :return:
        """
        raise NotImplementedError

    def get_bids(self, vehicle_type: VehicleType, route_planner: RoutePlanner, old_route: List[OrderLocation], orders: Set[Order], current_time: int, network: Network, **other_info) -> Dict[Order, OrderBid]:
        """
        :param vehicle_type: 车辆当前信息
        :param route_planner: 路线规划器
        :param old_route: 车辆行驶路线
        :param orders: 订单集合
        :param current_time: 当前时间
        :param network: 路网
        :return:
        """
        raise NotImplementedError


class AdditionalCostBidder(ProxyBidder):
    """
    利用优化量的增值作为投标的代理投标者, 这里的增量既可以是成本
    """
    __slots__ = []

    def __init__(self):
        super(AdditionalCostBidder, self).__init__()

    def get_bid(self, vehicle_type: VehicleType, route_planner: RoutePlanner, old_route: List[OrderLocation], order: Order, current_time: int, network: Network, **other_info) -> OrderBid:
        planning_result = route_planner.planning(vehicle_type, old_route, order, current_time, network)
        if planning_result.is_feasible:
            new_cost = planning_result.route_cost
            if "old_cost" in other_info:
                old_cost = other_info["old_cost"]
            else:
                old_route_info = get_route_info(vehicle_type, old_route, current_time, network)
                old_cost = get_route_cost_by_route_info(old_route_info, vehicle_type.unit_cost)

            additional_cost = fix_point_length_sub(new_cost, old_cost)
            bid = OrderBid(additional_cost, planning_result.route, additional_cost)
        else:
            bid = None
        return bid

    def get_bids(self, vehicle_type: VehicleType, route_planner: RoutePlanner,  old_route: List[OrderLocation], orders: Set[Order], current_time: int, network: Network, **other_info) -> Dict[Order, OrderBid]:
        old_route_info = get_route_info(vehicle_type, old_route, current_time, network)
        order_bids = dict()
        if old_route_info.is_feasible:
            old_cost = get_route_cost_by_route_info(old_route_info, vehicle_type.unit_cost)
            for order in orders:
                bid = self.get_bid(vehicle_type, route_planner, old_route, order, current_time, network, old_cost=old_cost)
                if bid is not None:
                    order_bids[order] = bid
        else:
            raise Warning("这里存在路线规划问题")
        return order_bids


class AdditionalProfitBidder(ProxyBidder):
    """
    利用优化量的增值作为投标的代理投标者, 这里的增量既可以是平台利润
    """
    __slots__ = []

    def __init__(self):
        super(AdditionalProfitBidder, self).__init__()

    def get_bid(self, vehicle_type: VehicleType, route_planner: RoutePlanner, old_route: List[OrderLocation], order: Order, current_time: int, network: Network, **other_info) -> OrderBid:
        planning_result = route_planner.planning(vehicle_type, old_route, order, current_time, network)
        if planning_result.is_feasible:
            new_profit = planning_result.route_profit
            new_cost = planning_result.route_cost
            if "old_profit" in other_info and "old_cost" in other_info:
                old_profit = other_info["old_profit"]
                old_cost = other_info["old_cost"]
            else:
                old_route_info = get_route_info(vehicle_type, old_route, current_time, network)
                old_profit = other_info["old_profit"] if "old_profit" in other_info else get_route_profit_by_route_info(old_route_info, vehicle_type.unit_cost)
                old_cost = other_info["old_cost"] if "old_cost" in other_info else get_route_cost_by_route_info(old_route_info, vehicle_type.unit_cost)

            additional_profit = fix_point_length_sub(new_profit, old_profit)
            additional_cost = fix_point_length_sub(new_cost, old_cost)
            bid = OrderBid(additional_profit, planning_result.route, additional_cost)
        else:
            bid = None
        return bid

    def get_bids(self, vehicle_type: VehicleType, route_planner: RoutePlanner, old_route: List[OrderLocation], orders: Set[Order], current_time: int, network: Network, **other_info) -> Dict[Order, OrderBid]:
        old_route_info = get_route_info(vehicle_type, old_route, current_time, network)
        order_bids = dict()
        if old_route_info.is_feasible:
            old_profit = get_route_profit_by_route_info(old_route_info, vehicle_type.unit_cost)
            old_cost = get_route_cost_by_route_info(old_route_info, vehicle_type.unit_cost)
            for order in orders:
                bid = self.get_bid(vehicle_type, route_planner, old_route, order, current_time, network, old_profit=old_profit, old_cost=old_cost)
                if bid is not None:
                    order_bids[order] = bid
        else:
            raise Warning("这里存在路线规划问题")
        return order_bids
