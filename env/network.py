#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/11/3
"""
用于统一接口
"""
import numpy as np
from typing import List, Union
from setting import FIRST_INDEX, FLOAT_ZERO, DISTANCE_EPS
from env.graph import BaseGraph
from env.location import OrderLocation, VehicleLocation, GeoLocation, PickLocation, DropLocation
from utility import is_enough_small, singleton

__all__ = ["Network"]


@singleton
class Network:
    __slots__ = ["_graph"]

    base_graph = {}

    def __init__(self, graph: BaseGraph):
        self._graph = graph

    def get_shortest_distance(self, location1: GeoLocation, location2: GeoLocation) -> float:
        if isinstance(location1, VehicleLocation) and isinstance(location2, OrderLocation):
            return self.compute_vehicle_to_order_distance(location1, location2)
        else:
            return self._graph.get_shortest_distance_by_osm_index(location1.osm_index, location2.osm_index)

    def generate_random_locations(self, locations_number: int, location_type) -> List[Union[DropLocation, PickLocation, VehicleLocation]]:
        return self._graph.generate_random_locations(locations_number, location_type)

    def can_move_to_goal_index(self, vehicle_location: VehicleLocation, order_location: OrderLocation) -> bool:
        return self._graph.can_move_to_goal_index(vehicle_location, order_location)

    def compute_vehicle_to_order_distance(self, vehicle_location: VehicleLocation, order_location: OrderLocation) -> float:
        """
        计算车辆与当前订单之间的距离
        情景是下面的情况:
                            / order_location \
                    distance_a             distance_b
                        /     distance_c       \
        location.osm_index-----vehicle------location.goal_index
        :param vehicle_location: 车辆位置
        :param order_location: 订单的位置
        :return: rest_pick_up_distance: 接乘客还需要行走的距离
        ------
        注意：
        这个函数不可以修改 vehicle_location的值
        """
        distance_a = self._graph.get_shortest_distance_by_osm_index(vehicle_location.osm_index, order_location.osm_index)  # 意义看文档
        if vehicle_location.is_between:
            if self.can_move_to_goal_index(vehicle_location, order_location):  # 车无法通过goal_index到达order_location
                distance_b = self._graph.get_shortest_distance_by_osm_index(vehicle_location.goal_index, order_location.osm_index)  # 意义看文档
                distance_c = self._graph.get_shortest_distance_by_osm_index(vehicle_location.osm_index, vehicle_location.goal_index)  # 意义看文档
                vehicle_to_order_distance = distance_c - vehicle_location.driven_distance + distance_b
            else:
                vehicle_to_order_distance = distance_a + vehicle_location.driven_distance
        else:
            vehicle_to_order_distance = distance_a

        return round(vehicle_to_order_distance)  # 精确到 m

    def drive_on_random(self, vehicle_location: VehicleLocation, could_drive_distance: float) -> float:
        return self._graph.move_to_random_index(vehicle_location, could_drive_distance)

    def drive_on_route(self, vehicle_location: VehicleLocation, vehicle_route: List[OrderLocation], could_drive_distance: float):
        """
        在一个时间间隔内，车辆按照自己的路线进行行驶
        :param vehicle_location: 车俩当前的位置
        :param vehicle_route: 车辆当前的行驶路线
        :param could_drive_distance: 车辆可行行驶的距离
        ------
        注意：
        这个函数会修改vehicle_location的值
        行驶距离一定不可以小于could_drive_distance
        """
        if vehicle_location.is_between:  # 当前车辆在两点之间
            if self.can_move_to_goal_index(vehicle_location, vehicle_route[FIRST_INDEX]):  # 当前车辆需要向location.goal_index行驶
                vehicle_to_goal_distance = self._graph.get_shortest_distance_by_osm_index(vehicle_location.osm_index, vehicle_location.goal_index) - vehicle_location.driven_distance
                vehicle_to_goal_distance = round(vehicle_to_goal_distance)
                # 判断是否可以到location.goal_index
                # 1. vehicle 到 goal_index 的距离远远小于could_drive_distance
                # 2. vehicle 到 goal_index 的距离只比could_drive_distance大DISTANCE_EPS
                if is_enough_small(vehicle_to_goal_distance - could_drive_distance, DISTANCE_EPS):  # 是否可以继续行驶
                    pre_drive_distance = vehicle_to_goal_distance
                    vehicle_location.set_location(vehicle_location.goal_index)  # 由于不在两点之间了需要重置goal_index和相应的一些设置
                else:
                    pre_drive_distance = could_drive_distance
                    vehicle_location.increase_driven_distance(could_drive_distance)  # 还在之前的两个节点之间只需要修改行驶距离就可以，只不过是向goal_index方向行驶
            else:
                # 判断是否可以回到上一个出发节点
                # 1. vehicle 到 osm_index 的距离远远小于should_drive_distance
                # 2. vehicle 到 osm_index 的距离只是比could_drive_distance大DISTANCE_EPS
                if is_enough_small(vehicle_location.driven_distance - could_drive_distance, DISTANCE_EPS):  # 是否可以继续行驶
                    pre_drive_distance = vehicle_location.driven_distance
                    vehicle_location.reset()  # 又回到osm_index上
                else:
                    pre_drive_distance = could_drive_distance
                    vehicle_location.decrease_driven_distance(could_drive_distance)  # 还在之前的两个节点之间只需要修改行驶距离就可以，只不过是向osm_index
        else:
            pre_drive_distance = FLOAT_ZERO

        could_drive_distance -= pre_drive_distance
        if not vehicle_location.is_between and not is_enough_small(could_drive_distance, FLOAT_ZERO):
            # 如果车辆不在两点之间而就在一个点上 或者 车辆的可行使距离还有很多的情况下
            # 第一个订单节点的位置有两种可能性第一种订单节点在车辆处于两个节点中任何一个或者是在别的位置
            for covered_index, order_location in enumerate(vehicle_route):  # 现在开始探索路线规划的各个节点
                vehicle_to_order_distance = self._graph.get_shortest_distance_by_osm_index(vehicle_location.osm_index, order_location.osm_index)
                if is_enough_small(vehicle_to_order_distance - could_drive_distance, DISTANCE_EPS):  # 当此订单节点是可以到达的情况
                    could_drive_distance -= vehicle_to_order_distance  # 更新当前车辆需要行驶的距离
                    vehicle_location.set_location(order_location.osm_index)  # 更新车辆坐标

                    if covered_index == FIRST_INDEX:
                        vehicle_to_order_distance += pre_drive_distance
                    yield True, covered_index, order_location, np.round(vehicle_to_order_distance)

                    if is_enough_small(could_drive_distance, FLOAT_ZERO):  # 如果车辆多行驶了一点距离我们包容这种情况，就当车辆可以到对应的节点上
                        break
                else:  # 订单节点路长过大无法到达的情况, 需要进行精细调整
                    target_index = order_location.osm_index
                    vehicle_to_target_distance = self._graph.move_to_target_index(vehicle_location, target_index, could_drive_distance, is_random_drive=False)
                    if covered_index == FIRST_INDEX:  # 如果是第一个订单就是不可达的那么要考虑之前行驶的距离
                        vehicle_to_target_distance += pre_drive_distance
                    yield False, covered_index - 1, order_location, round(vehicle_to_target_distance)
                    break
        else:  # 车辆一开始就把所有可以运行的距离都运行，车辆根本就不可能到任何一个订单节点
            yield False, -1, None, round(pre_drive_distance)

    @staticmethod
    def is_smaller_bound_distance(distance: float, bound_distance: float):
        """
        检查distance是否比bound_distance小，这里面距离是比较模糊的小，我们认为distance 只要比 bound_distance + DISTANCE_EPS小就可以
        :param distance:
        :param bound_distance:
        :return:
        """
        return is_enough_small(round(distance), round(bound_distance + DISTANCE_EPS))
