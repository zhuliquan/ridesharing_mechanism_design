#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/10/26
import time
from collections import defaultdict
from typing import List, Tuple, Set, NoReturn

from agent.vehicle import Vehicle
from algorithm.utility import Mechanism
from algorithm.simple_dispatching.matching_graph import MaximumWeightMatchingGraph, BipartiteGraph
from algorithm.simple_dispatching.matching_pool import MatchingPairPool
from env.network import Network
from env.order import Order
from utility import is_enough_small, fix_point_length_sub, fix_point_length_add

__all__ = ["vcg_mechanism", "greedy_mechanism"]


class VCGMechanism(Mechanism):
    """
    使用二部图匹配决定分配，利用vcg价格进行支付，主要基vcg机制理论, 最大化社会福利 pair_social_welfare = sum{order.order_fare} - sum{bid.additional_cost}
    """

    __slots__ = ["graph"]

    def __init__(self):
        super(VCGMechanism, self).__init__()

    @staticmethod
    def _build_graph(vehicles: List[Vehicle], orders: Set[Order], current_time: int, network: Network, graph_type) -> BipartiteGraph:
        feasible_vehicles = set()
        feasible_orders = set()
        bids = dict()

        for vehicle in vehicles:
            order_bids = vehicle.get_bids(orders, current_time, network)
            order_bids = {order: order_bid for order, order_bid in order_bids.items() if is_enough_small(order_bid.additional_cost, order.order_fare)}  # 这里可以保证订单的合理性
            if len(order_bids) > 0:
                feasible_vehicles.add(vehicle)
                bids[vehicle] = order_bids
            for order in order_bids:
                feasible_orders.add(order)

        graph = graph_type(feasible_vehicles, feasible_orders)
        for vehicle, order_bids in bids.items():
            for order, order_bid in order_bids.items():
                graph.add_edge(vehicle, order, fix_point_length_sub(order.order_fare, order_bid.additional_cost))
        graph.bids = bids

        return graph

    def driver_pricing(self, bipartite_graph: BipartiteGraph, match_pairs: List[Tuple[Vehicle, Order]], social_welfare: float):
        for winner_vehicle, corresponding_order in match_pairs:
            # 计算VCG价格
            bipartite_graph.temporarily_remove_vehicle(winner_vehicle)  # 临时性的删除一个车辆
            social_welfare_without_winner, _ = bipartite_graph.maximal_weight_matching(return_match=False)  # 计算没有这辆车时候的社会福利
            bipartite_graph.recovery_remove_vehicle()  # 恢复被删除的车辆
            winner_bid = bipartite_graph.get_vehicle_order_pair_bid(winner_vehicle, corresponding_order)
            additional_cost = winner_bid.additional_cost
            # driver_reward = min(fix_point_length_add(additional_cost, fix_point_length_sub(social_welfare, social_welfare_without_winner)), corresponding_order.order_fare)
            driver_reward = fix_point_length_add(additional_cost, fix_point_length_sub(social_welfare, social_welfare_without_winner))
            driver_payoff = fix_point_length_sub(driver_reward, additional_cost)

            # 保存结果
            self._dispatched_vehicles.add(winner_vehicle)
            self._dispatched_orders.add(corresponding_order)
            self._dispatched_results[winner_vehicle].add_order(corresponding_order, driver_reward, driver_payoff)
            self._dispatched_results[winner_vehicle].set_route(winner_bid.bid_route)
            self._social_cost = fix_point_length_add(self._social_cost, additional_cost)
            self._total_driver_rewards = fix_point_length_add(self._total_driver_rewards, driver_reward)
            self._total_driver_payoffs = fix_point_length_add(self._total_driver_payoffs, driver_payoff)
            self._platform_profit = fix_point_length_add(self._platform_profit, fix_point_length_sub(corresponding_order.order_fare, driver_reward))
        self._social_welfare = fix_point_length_add(self._social_welfare, social_welfare)

    def run(self, vehicles: List[Vehicle], orders: Set[Order], current_time: int, network: Network) -> NoReturn:
        self.reset()  # 清空结果
        # 构建图
        t1 = time.clock()
        main_graph = self._build_graph(vehicles, orders, current_time, network, MaximumWeightMatchingGraph)
        self._bidding_time = (time.clock() - t1)  # 统计投标时间
        # 订单分配与司机定价
        for sub_graph in main_graph.get_sub_graphs():
            sub_social_welfare, sub_match_pairs = sub_graph.maximal_weight_matching(return_match=True)  # 胜者决定
            self.driver_pricing(sub_graph, sub_match_pairs, sub_social_welfare)  # 司机定价并统计结果
        self._running_time = (time.clock() - t1 - self._bidding_time)


class GreedyMechanism(Mechanism):
    """
    使用贪心算法分配，使用临界价格进行支付，主要基于Myerson理论进行设计的机制, 最大化社会福利 pair_social_welfare = sum{order.order_fare} - sum{bid.additional_cost}
    """
    __slots__ = []

    def __init__(self):
        super(GreedyMechanism, self).__init__()

    @staticmethod
    def _build_matching_pool(vehicles: List[Vehicle], orders: Set[Order], current_time: int, network: Network):
        bids = defaultdict(dict)
        for vehicle in vehicles:
            order_bids = vehicle.get_bids(orders, current_time, network)
            order_bids = {order: order_bid for order, order_bid in order_bids.items() if is_enough_small(order_bid.additional_cost, order.order_fare)}  # 这里可以保证订单的合理性
            for order, order_bid in order_bids.items():
                bids[order][vehicle] = order_bid

        bids = {order: order_bids for order, order_bids in bids.items() if len(order_bids) >= 2}  # 这里是为了避免monopoly vehicle
        pool = MatchingPairPool(bids)
        return pool

    def _order_matching(self, pool: MatchingPairPool) -> List[Tuple[Vehicle, Order]]:
        match_pairs = list()
        for vehicle_order_pair in pool:
            if len(self._dispatched_vehicles) == pool.vehicle_number or len(self._dispatched_orders) == pool.order_number:
                break
            dispatched_vehicle, dispatched_order, _ = vehicle_order_pair
            if dispatched_vehicle in self._dispatched_vehicles or dispatched_order in self._dispatched_orders:
                continue
            self._dispatched_vehicles.add(dispatched_vehicle)  # 重要的事情：这一段代码必须写在这里不然会出问题的
            self._dispatched_orders.add(dispatched_order)
            match_pairs.append((dispatched_vehicle, dispatched_order))
        return match_pairs

    def _driver_pricing(self, pool: MatchingPairPool, match_pairs: List[Tuple[Vehicle, Order]]) -> NoReturn:
        for winner_vehicle, corresponding_order in match_pairs:
            # 计算临界价格
            dispatched_vehicles_without_winner = set()
            dispatched_orders_without_winner = set()
            dispatched_vehicles_without_winner.add(winner_vehicle)  # 首先就将改车辆排除
            winner_bid = pool.get_vehicle_order_pair_bid(winner_vehicle, corresponding_order)
            driver_reward = winner_bid.additional_cost
            for vehicle_order_pair in pool:  # 剔除已经胜利的车辆重新匹配
                if len(dispatched_vehicles_without_winner) == pool.vehicle_number or len(dispatched_orders_without_winner) == pool.order_number:
                    break
                dispatched_vehicle, dispatched_order, pair_social_welfare = vehicle_order_pair
                if dispatched_vehicle in dispatched_vehicles_without_winner or dispatched_order in dispatched_orders_without_winner:  # 剔除已经分配的订单
                    continue
                driver_reward = max(driver_reward, fix_point_length_sub(corresponding_order.order_fare, pair_social_welfare))
                dispatched_vehicles_without_winner.add(dispatched_vehicle)
                dispatched_orders_without_winner.add(dispatched_order)
                if corresponding_order == dispatched_order:  # 循环终止条件
                    break
            driver_reward = min(corresponding_order.order_fare, driver_reward)
            driver_payoff = fix_point_length_sub(driver_reward, winner_bid.additional_cost)
            # 保存结果
            self._social_welfare = fix_point_length_add(self._social_welfare, fix_point_length_sub(corresponding_order.order_fare, winner_bid.additional_cost))
            self._social_cost = fix_point_length_add(self._social_cost, winner_bid.additional_cost)
            self._dispatched_results[winner_vehicle].add_order(corresponding_order, driver_reward, driver_payoff)
            self._dispatched_results[winner_vehicle].set_route(winner_bid.bid_route)
            self._total_driver_rewards = fix_point_length_add(self._total_driver_rewards, driver_reward)
            self._total_driver_payoffs = fix_point_length_add(self._total_driver_payoffs, driver_payoff)
            self._platform_profit = fix_point_length_add(self._platform_profit, fix_point_length_sub(corresponding_order.order_fare, driver_reward))

    def run(self, vehicles: List[Vehicle], orders: Set[Order], current_time: int, network: Network) -> NoReturn:
        self.reset()  # 清空结果

        # 构建资源池
        t1 = time.clock()
        pool = self._build_matching_pool(vehicles, orders, current_time, network)
        self._bidding_time += (time.clock() - t1)

        # 订单分配与司机定价
        match_pairs = self._order_matching(pool)  # 胜者决定
        self._driver_pricing(pool, match_pairs)  # 司机定价并记录结果
        self._running_time += (time.clock() - t1 - self._bidding_time)


# 对外的接口
vcg_mechanism = VCGMechanism()
greedy_mechanism = GreedyMechanism()
