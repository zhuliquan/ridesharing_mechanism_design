#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/10/26
import time
from typing import Set, List, Tuple, NoReturn


from agent.vehicle import Vehicle
from algorithm.route_planning.utility import pre_check_need_to_planning, get_route_info, get_route_cost_by_route_info
from algorithm.utility import Mechanism
from setting import FLOAT_ZERO, NEG_INF
from env.network import Network
from env.order import Order
from utility import is_enough_small, fix_point_length_sub, fix_point_length_add

__all__ = ["nearest_vehicle_dispatching", "sparp_mechanism"]


class NearestVehicleDispatching(Mechanism):
    """
    每一个订单按照最近的车辆匹配原则
    """

    __slots__ = []

    def __init__(self):
        super(NearestVehicleDispatching, self).__init__()

    def run(self, vehicles: List[Vehicle], orders: Set[Order], current_time: int, network: Network) -> NoReturn:
        self.reset()  # 清空结果

        # 临时存放车辆信息
        temp_vehicle_roue = {vehicle: vehicle.route for vehicle in vehicles}

        t1 = time.clock()
        sort_by_time_orders = sorted(orders, key=lambda _order: _order.request_time)  # 按时间排序
        for order in sort_by_time_orders:
            t2 = time.clock()
            vehicle_distances: List[Tuple[Vehicle, float]] = list()
            for vehicle in vehicles:
                if pre_check_need_to_planning(vehicle.vehicle_type, order, current_time, network):  # 只记录了合理的车辆而不合理的都没有进行记录
                    vehicle_distances.append((vehicle, network.compute_vehicle_to_order_distance(vehicle.location, order.pick_location)))
            self._bidding_time += (time.clock() - t2)

            vehicle_distances.sort(key=lambda x: x[1])  # 接的距离越小越好
            for vehicle, distance in vehicle_distances:
                planing_result = vehicle.route_planner.planning(vehicle.vehicle_type, temp_vehicle_roue[vehicle], order, current_time, network)
                if not planing_result.is_feasible:
                    continue
                old_route_info = get_route_info(vehicle.vehicle_type, temp_vehicle_roue[vehicle], current_time, network)
                old_cost = get_route_cost_by_route_info(old_route_info, vehicle.unit_cost)
                additional_cost = fix_point_length_sub(planing_result.route_cost, old_cost)
                if is_enough_small(additional_cost, order.order_fare):
                    self._dispatched_vehicles.add(vehicle)
                    self._dispatched_orders.add(order)
                    self._dispatched_results[vehicle].add_order(order, additional_cost, FLOAT_ZERO)
                    self._dispatched_results[vehicle].set_route(planing_result.route)
                    self._social_welfare = fix_point_length_add(self._social_welfare, fix_point_length_sub(order.order_fare, additional_cost))
                    self._social_cost = fix_point_length_add(self._social_cost, additional_cost)
                    self._total_driver_rewards = fix_point_length_add(self._total_driver_rewards, additional_cost)
                    self._platform_profit = fix_point_length_add(self._platform_profit, fix_point_length_sub(order.order_fare, additional_cost))
                    temp_vehicle_roue[vehicle] = planing_result.route  # 车辆信息暂时更新
                    break
        self._running_time += (time.clock() - t1 - self._bidding_time)


class SPARPMechanism(Mechanism):
    """
    SPARP 是 Mohammad Asghari 在 SIGSPATIAL-17 中论文里面采用的方法
    论文名称是 An On-line Truthful and Individually Rational Pricing Mechanism for Ride-sharing
    这里面使用 使用平台收益作为投标，使用二级拍卖的方式决定支付，同时设置了保留价格保证平台收益
    平台赚取信息费，司机投标表示从这个平台可以获取的收入，而司机还需要支付平台一定的钱取获得这一部分收入
    """
    __slots__ = []

    def __init__(self):
        super(SPARPMechanism, self).__init__()

    def run(self, vehicles: List[Vehicle], orders: Set[Order], current_time: int, network: Network) -> NoReturn:
        self.reset()  # 清空结果

        # 临时存放车辆信息
        temp_vehicle_roue = {vehicle: vehicle.route for vehicle in vehicles}

        t1 = time.clock()
        sort_by_time_orders = sorted(orders, key=lambda _order: _order.request_time)  # 按时间排序
        for order in sort_by_time_orders:
            t2 = time.clock()
            order_bids = []
            max_cost = NEG_INF
            for vehicle in vehicles:
                order_bid = vehicle.proxy_bidder.get_bid(vehicle.vehicle_type, vehicle.route_planner, temp_vehicle_roue[vehicle], order, current_time, network)
                if order_bid is not None:
                    order_bids.append((vehicle, order_bid))
                    max_cost = max(max_cost, order_bid.additional_cost)
            self._bidding_time += (time.clock() - t2)

            if len(order_bids) < 1:  # 压根没有人投标
                continue

            order_bids.sort(key=lambda x: x[1].bid_value, reverse=True)  # 按照社会福利排序
            reverse_price = fix_point_length_sub(order.order_fare, max_cost)  # 平台的保留价格
            winner_vehicle, winner_bid = order_bids[0]  # 胜利司机与其相对应的投标
            pair_social_welfare = winner_bid.bid_value  # 平台的社会福利
            if is_enough_small(FLOAT_ZERO, pair_social_welfare) and is_enough_small(reverse_price, pair_social_welfare):
                if len(order_bids) > 1:
                    _, max_loser_bid = order_bids[1]
                    driver_payment = max_loser_bid.bid_value  # 司机支付给平台的钱
                    if not is_enough_small(reverse_price, driver_payment):  # TODO 这个原始论文存在问题，不应该是driver payment < 0 才做这个事情， 还有reverse price 还有小于0的情况，原始论文也是没有考虑的
                        driver_payment = reverse_price
                else:
                    driver_payment = FLOAT_ZERO  # 司机无法给平台支付
                additional_cost = winner_bid.additional_cost  # 司机完成任务成本
                driver_reward = fix_point_length_sub(fix_point_length_add(pair_social_welfare, additional_cost), driver_payment)  # 司机的收入
                driver_payoff = fix_point_length_sub(driver_reward, additional_cost)   # 司机的利润
                self._dispatched_vehicles.add(winner_vehicle)
                self._dispatched_orders.add(order)
                self._dispatched_results[winner_vehicle].add_order(order, driver_reward, driver_payoff)
                self._dispatched_results[winner_vehicle].set_route(winner_bid.bid_route)
                self._social_welfare = fix_point_length_add(self._social_welfare, pair_social_welfare)
                self._social_cost = fix_point_length_add(self._social_cost, additional_cost)
                self._total_driver_rewards = fix_point_length_add(self._total_driver_rewards, driver_reward)
                self._total_driver_payoffs = fix_point_length_add(self._total_driver_payoffs, driver_payoff)
                self._platform_profit = fix_point_length_add(self._platform_profit, driver_payment)
                temp_vehicle_roue[winner_vehicle] = winner_bid.bid_route  # 车辆信息暂时更新

        self._running_time += (time.clock() - t1 - self._bidding_time)


nearest_vehicle_dispatching = NearestVehicleDispatching()
sparp_mechanism = SPARPMechanism()
