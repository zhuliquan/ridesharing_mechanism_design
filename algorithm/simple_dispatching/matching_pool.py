#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/11/14
from typing import Dict
from agent.utility import OrderBid
from agent.vehicle import Vehicle
from env.order import Order
from utility import fix_point_length_sub


class MatchingPairPool:
    __slots__ = ["_pool", "_bids", "vehicle_number", "order_number"]

    def __init__(self, bids: Dict[Order, Dict[Vehicle, OrderBid]]):
        self._pool = list()
        self.order_number = 0
        feasible_vehicles = set()
        for order, order_bids in bids.items():
            self.order_number += 1
            for vehicle, order_bid in order_bids.items():
                feasible_vehicles.add(vehicle)
                self._pool.append((vehicle, order, fix_point_length_sub(order.order_fare, order_bid.additional_cost)))

        self._pool.sort(key=lambda x: x[2], reverse=True)  # 按照社会福利进行排序
        self._bids = bids
        self.vehicle_number = len(feasible_vehicles)

    def get_vehicle_order_pair_bid(self, vehicle: Vehicle, order: Order):
        return self._bids[order][vehicle]

    def __iter__(self):
        return iter(self._pool)
