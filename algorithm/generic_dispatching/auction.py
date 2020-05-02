#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/10/26
import time
from typing import List, Set, NoReturn

from agent.vehicle import Vehicle
from algorithm.utility import Mechanism
from env.network import Network
from env.order import Order
from utility import is_enough_small, fix_point_length_add, fix_point_length_sub


class SecondPriceSequenceAuction(Mechanism):
    """
    每一个时刻，将订单按照订单价格排序，然后按照每一个商品按照贯序拍卖的形式进行拍卖,
    这种方式适合使用成本作为投标方式的拍卖
    """

    __slots__ = []

    def __init__(self):
        super(SecondPriceSequenceAuction, self).__init__()

    def run(self, vehicles: List[Vehicle], orders: Set[Order], current_time: int, network: Network) -> NoReturn:
        self.reset()  # 清空结果

        # 临时存放车辆信息
        temp_vehicle_roue = {vehicle: vehicle.route for vehicle in vehicles}

        t1 = time.clock()
        order_by_fare_orders = sorted(orders, key=lambda _order: _order.order_fare, reverse=True)  # 按照订单的估值进行排序
        for order in order_by_fare_orders:

            t2 = time.clock()
            order_bids = []
            for vehicle in vehicles:
                order_bid = vehicle.proxy_bidder.get_bid(vehicle.vehicle_type, vehicle.route_planner, temp_vehicle_roue[vehicle], order, current_time, network)
                if order_bid is not None and is_enough_small(order_bid.additional_cost, order.order_fare):
                    order_bids.append((vehicle, order_bid))
            self._bidding_time += (time.clock() - t2)

            if len(order_bids) < 1:  # 压根没有人投标
                continue

            order_bids.sort(key=lambda x: x[1].additional_cost)   # 按照完成订单的成本进行排序
            winner_vehicle, winner_bid = order_bids[0]  # 获胜车辆和与之对应的投标
            if len(order_bids) > 1:
                _, max_loser_bid = order_bids[1]
            else:
                max_loser_bid = winner_bid

            additional_cost = winner_bid.additional_cost
            driver_reward = max_loser_bid.additional_cost  # 平台支付给司机的回报
            driver_payoff = fix_point_length_sub(driver_reward, additional_cost)
            self._dispatched_vehicles.add(winner_vehicle)
            self._dispatched_orders.add(order)
            self._dispatched_results[winner_vehicle].add_order(order, driver_reward, driver_payoff)
            self._dispatched_results[winner_vehicle].set_route(winner_bid.bid_route)
            self._social_welfare = fix_point_length_add(self._social_welfare, fix_point_length_sub(order.order_fare, additional_cost))
            self._social_cost = fix_point_length_add(self._social_cost, additional_cost)
            self._total_driver_rewards = fix_point_length_add(self._total_driver_rewards, driver_reward)
            self._total_driver_payoffs = fix_point_length_add(self._total_driver_payoffs, driver_payoff)
            self._platform_profit = fix_point_length_add(self._platform_profit, fix_point_length_sub(order.order_fare, driver_reward))
            temp_vehicle_roue[winner_vehicle] = winner_bid.bid_route  # 车辆信息暂时更新

        self._running_time += (time.clock() - t1 - self._bidding_time)


second_price_sequence_auction = SecondPriceSequenceAuction()
