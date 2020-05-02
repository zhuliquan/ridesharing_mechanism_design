#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/11/7
from array import array
from typing import List, Tuple, Union

import numpy as np

from setting import FLOAT_ZERO, DISTANCE_EPS
from setting import INT_ZERO
from env.location import OrderLocation, VehicleLocation
from utility import is_enough_small
from utility import singleton

__all__ = ["BaseGraph", "RoadGraph", "GridGraph"]


class BaseGraph:
    """
    我的交通路网图的接口
    """
    __slots__ = []
    generate_graph_function = None  # 生成图的函数

    @classmethod
    def set_generate_graph_function(cls, function):
        cls.generate_graph_function = function

    @classmethod
    def generate_graph(cls):
        return cls.generate_graph_function()

    def get_shortest_distance_by_osm_index(self, osm_index1: int, osm_index2: int) -> float:
        raise NotImplementedError

    def get_shortest_path_by_osm_index(self, osm_index1: int, osm_index2: int) -> int:
        raise NotImplementedError

    def can_move_to_goal_index(self, vehicle_location: VehicleLocation, order_location: OrderLocation) -> bool:
        raise NotImplementedError

    def generate_random_locations(self, location_number: int, location_type) -> List[Union[OrderLocation, VehicleLocation]]:
        raise NotImplementedError

    def move_to_target_index(self, vehicle_location: VehicleLocation, target_index: int, could_drive_distance: float, is_random_drive=True) -> float:
        """
        模拟一个车辆真实得尝试向某一个可以到达的目标节点前进的过程
        :param vehicle_location:
        :param target_index:
        :param could_drive_distance:
        :param is_random_drive: 如果是random_drive就不会考虑一定要形式到could_drive_distance, is_random_drive 是真的
        :return:
        ------
        注意：这个函数会修改vehicle_location的值, 确保车辆一定是在一个点上的，而不是在两个节点之间
        """
        if vehicle_location.is_between:
            raise Exception("车辆不是固定在一个点上的无法继续进行后续的计算")
        real_drive_distance = self.get_shortest_distance_by_osm_index(vehicle_location.osm_index, target_index)  # 实际行驶的距离
        if is_enough_small(real_drive_distance - could_drive_distance, DISTANCE_EPS):  # 可以到target_index的情况
            vehicle_location.set_location(target_index)
        else:
            real_drive_distance = FLOAT_ZERO
            while not is_enough_small(could_drive_distance, DISTANCE_EPS):  # 需要行驶的距离已经过小了的情况
                next_index = self.get_shortest_path_by_osm_index(vehicle_location.osm_index, target_index)
                vehicle_to_next_distance = self.get_shortest_distance_by_osm_index(vehicle_location.osm_index, next_index)  # 因为只是移动一个格子, 所以只是移动一个小格子
                if is_enough_small(vehicle_to_next_distance - could_drive_distance, DISTANCE_EPS):
                    real_drive_distance += vehicle_to_next_distance
                    could_drive_distance -= vehicle_to_next_distance
                    vehicle_location.set_location(next_index)
                    if is_enough_small(could_drive_distance, FLOAT_ZERO):
                        break
                else:
                    real_drive_distance += could_drive_distance
                    vehicle_location.set_location(vehicle_location.osm_index, could_drive_distance, next_index)
                    break
            else:  # 正常退出情况需要更新此时车辆的位置
                if not is_random_drive:  # 不是随机行驶
                    real_drive_distance += could_drive_distance
                    next_index = self.get_shortest_path_by_osm_index(vehicle_location.osm_index, target_index)
                    vehicle_location.set_location(vehicle_location.osm_index, could_drive_distance, next_index)

        return real_drive_distance

    def move_to_random_index(self, vehicle_location: VehicleLocation, could_drive_distance: float) -> float:
        raise NotImplementedError


@singleton
class RoadGraph(BaseGraph):
    """
    实际的交通路网图
    shortest_distance: 两个节点最短路径距离矩阵
    shortest_path: 两个节点最短路径矩阵  shortest_path[i,j]->k 表示i到j的最短路径需要经过k
    access_index: 表示车辆在某一个节点上可以到达的节点
    adjacent_location_osm_index: 保存车辆下一个时间间隔可以到达的节点
    adjacent_location_driven_distance: 保存车辆下一个时间间隔可以到达的节点 还会多行驶的一段距离
    adjacent_location_goal_index: 保存车辆下一个时间间隔可以到达的节点 多行驶距离的朝向节点
    index2location: 用于与底层的数据进行转换对接，自己坐标的运动体系index->osm_id->(longitude, latitude)
    index2osm_id: 用于与底层的数据进行转换啊对接，自己坐标的运动体系index->osm_id
    raw_graph: 真实的图
    """
    __slots__ = ["_shortest_distance", "_shortest_path", "_access_osm_index", "_adjacent_location_osm_index", "_adjacent_location_driven_distance", "_adjacent_location_goal_index", "_index_set"]

    def __init__(self, shortest_distance: np.ndarray, shortest_path: np.ndarray, access_index: List[array]):
        """
        :param shortest_distance: 两个节点最短路径距离矩阵
        :param shortest_path: 两个节点最短路径矩阵  shortest_path[i,j]->k 表示i到j的最短路径需要经过k
        :param access_index: 表示车辆在某一个节点上可以到达的节点
        # :param adjacent_location_osm_index: 保存车辆下一个时间间隔可以到达的节点
        # :param adjacent_location_driven_distance: 保存车辆下一个时间间隔可以到达的节点 还会多行驶的一段距离
        # :param adjacent_location_goal_index: 保存车辆下一个时间间隔可以到达的节点 多行驶距离的朝向节点
        ------
        注意：
        shortest_distance 用于查询任意两点之间的最短路径长度 单位长度m
        1. i==j, shortest_length[i,j] = 0;
        2. i不可以到达j, shortest_length[i, j] = np.inf

        shortest_path 用于记录两点按照最短路径走下一步会到哪个节点
        1. shortest_distance[i, j] == 0.0, shortest_path[i, j] = -1;
        2. shortest_distance[i, j] == np.inf, shortest_path[i, j] = -2;
        """
        self._shortest_distance = shortest_distance
        self._shortest_path = shortest_path
        self._access_osm_index = access_index
        self._index_set = np.array(list(range(shortest_distance.shape[0])), dtype=np.int16)

    def _get_random_osm_index(self) -> int:
        """
        随机生成一个osm_index
        :return:
        """
        return np.random.choice(self._index_set)

    def get_shortest_distance_by_osm_index(self, osm_index1: int, osm_index2: int) -> float:
        return self._shortest_distance[osm_index1, osm_index2]

    def get_shortest_path_by_osm_index(self, osm_index1: int, osm_index2: int) -> int:
        return self._shortest_path[osm_index1, osm_index2]

    def can_move_to_goal_index(self, vehicle_location: VehicleLocation, order_location: OrderLocation) -> bool:
        """
        当车辆正在两个节点之间的时候，判断车辆是否经过vehicle_location的目标节点到订单节点
        情景是下面的情况：
                            / order_location \
                    distance_a             distance_b
                        /     distance_c       \
        location.osm_index-----vehicle------location.goal_index

        如果是 distance_c - self.between_distance + distance_b < distance_a + self.between_distance 或者
        不可以从goal_index 到 location.osm_index 或者
        那么返回 true
        :param vehicle_location: 车辆位置
        :param order_location: 订单的位置
        :return 返回一个bool值 为真表示可以从goal_index到达目标节点，而不可以则要从osm_index到达目标节点
        ------
        注意：
        这个函数不可以修改 vehicle_location的值
        """
        distance_a = self._shortest_distance[vehicle_location.osm_index, order_location.osm_index]  # 意义看文档
        distance_b = self._shortest_distance[vehicle_location.goal_index, order_location.osm_index]  # 意义看文档
        distance_c = self._shortest_distance[vehicle_location.osm_index, vehicle_location.goal_index]  # 意义看文档
        reverse_distance_c = self._shortest_distance[vehicle_location.goal_index, vehicle_location.osm_index]
        if reverse_distance_c == np.inf or (distance_b != np.inf and is_enough_small(distance_c - vehicle_location.driven_distance + distance_b, distance_a + vehicle_location.driven_distance)):
            # 用于判断车是否从goal_index到order_location 或者不可以反向行驶
            return True
        else:
            return False

    def generate_random_locations(self, location_number: int, location_type) -> List[Union[OrderLocation, VehicleLocation]]:
        """
        用于返回一个随机车辆位置列表
        :return:
        """
        locations_index = np.random.choice(self._index_set, location_number)
        return [location_type(locations_index[i]) for i in range(location_number)]

    def move_to_random_index(self, vehicle_location: VehicleLocation, could_drive_distance: float) -> float:
        """
        :param vehicle_location:  车辆当前的位置
        :param could_drive_distance 车辆可以行驶的距离
        ------
        注意： 这个函数会修改vehicle_location的值!!!!!!
        在一个时间间隔内，车辆随机路网上行驶
        """
        real_drive_distance = FLOAT_ZERO  # 车辆实际行驶的距离
        if vehicle_location.is_between:  # 车辆处于两个节点之间
            # 首先车辆行驶两节点之间的距离
            vehicle_to_goal_distance = self.get_shortest_distance_by_osm_index(vehicle_location.osm_index, vehicle_location.goal_index) - vehicle_location.driven_distance

            if is_enough_small(vehicle_to_goal_distance - could_drive_distance, DISTANCE_EPS):  # 可以到goal_index上
                vehicle_location.set_location(vehicle_location.goal_index)  # 更新车辆位置
                real_drive_distance += vehicle_to_goal_distance  # 增加车辆行驶的距离
                could_drive_distance -= vehicle_to_goal_distance  # 减小车辆可以行驶的距离
            else:  # 不可以行驶动goal_index上
                vehicle_location.increase_driven_distance(could_drive_distance)  # 这样车辆还是会在两节点之间但是需要修改已经行驶的距离
                real_drive_distance += could_drive_distance  # 得到车辆当前行驶的距离
                could_drive_distance = FLOAT_ZERO

        # 如果车辆还有可行驶的距离探索可达节点
        if not is_enough_small(could_drive_distance, DISTANCE_EPS):
            if len(self._access_osm_index[vehicle_location.osm_index]) == INT_ZERO:  # 车当前的节点不可以到任何节点，那么就凭空移动，帮助其摆脱陷阱
                target_index = self._get_random_osm_index()
                vehicle_location.set_location(target_index)  # 凭空迁移
            else:
                target_index = np.random.choice(self._access_osm_index[vehicle_location.osm_index])
                real_drive_distance += self.move_to_target_index(vehicle_location, target_index, could_drive_distance)

        return np.round(real_drive_distance)


@singleton
class GridGraph(BaseGraph):
    """
    网格路网图
    图是由一个个的方格组成的
    图的大小是 graph_size * graph_size

    每一个方格都是如下图所示
    |----|
    |    | grid_size * grid_size
    |----|
    """
    __slots__ = ["_graph_size", "_grid_size", "_x_list", "_y_list", "_directions"]

    def __init__(self, graph_size: int, grid_size: float):
        """
        :param graph_size: 表示网格横向，纵向得数目
        :param grid_size: 表示每一个网络方格的大小
        """
        self._graph_size = graph_size
        self._grid_size = grid_size
        self._x_list = [i for i in range(graph_size + 1)]
        self._y_list = [j for j in range(graph_size + 1)]
        self._directions = [(1, INT_ZERO), (INT_ZERO, 1), (-1, INT_ZERO), (INT_ZERO, -1)]

    def _convert_index_to_xy(self, osm_index: int) -> Tuple[int, int]:
        return osm_index // self._graph_size, osm_index % self._graph_size

    def _convert_xy_to_index(self, x: int, y: int) -> int:
        return x * self._graph_size + y

    def _get_shortest_distance_by_xy(self, x1: int, y1: int, x2: int, y2: int) -> float:
        return (np.abs(x1 - x2) + np.abs(y1 - y2)) * self._grid_size

    def _get_random_osm_index(self) -> int:
        """
        随机生成一个osm_index
        :return:
        """
        random_x = np.random.choice(self._x_list)
        random_y = np.random.choice(self._y_list)
        return self._convert_xy_to_index(random_x, random_y)

    def _get_best_next_xy(self, now_x: int, now_y: int, target_x: int, target_y: int) -> Tuple[int, int]:
        """
        获取从（now_x, now_y） 到 （goal_x, target_y） 最优下一点最优节点
        :param now_x: 当前节点x
        :param now_y: 当前节点y
        :param target_x: 目标节点x
        :param target_y: 目标节点y
        :return:
        """
        next_xy_lists = [(now_x + direction[0], now_y + direction[1]) for direction in self._directions if 0 <= now_x + direction[0] <= self._graph_size and 0 <= now_y + direction[1] <= self._graph_size]
        next_xy_lists = [(next_x, next_y, self._get_shortest_distance_by_xy(next_x, next_y, target_x, target_y)) for next_x, next_y in next_xy_lists]
        next_xy_lists.sort(key=lambda x: x[2])
        return next_xy_lists[0][0], next_xy_lists[0][1]

    def get_shortest_distance_by_osm_index(self, osm_index1: int, osm_index2: int) -> float:
        x1, y1 = self._convert_index_to_xy(osm_index1)
        x2, y2 = self._convert_index_to_xy(osm_index2)
        return self._get_shortest_distance_by_xy(x1, y1, x2, y2)

    def get_shortest_path_by_osm_index(self, osm_index1: int, osm_index2: int) -> int:
        x1, y1 = self._convert_index_to_xy(osm_index1)
        x2, y2 = self._convert_index_to_xy(osm_index2)
        n_x, n_y = self._get_best_next_xy(x1, y1, x2, y2)
        return self._convert_xy_to_index(n_x, n_y)

    def can_move_to_goal_index(self, vehicle_location: VehicleLocation, order_location: OrderLocation) -> bool:
        """
        当车辆正在两个节点之间的时候，判断车辆是否经过vehicle_location的目标节点到订单节点
        情景是下面的情况：
                            / order_location \
                    distance_a             distance_b
                        /     distance_c       \
        location.osm_index-----vehicle------location.goal_index

        如果是 distance_c - self.between_distance + distance_b < distance_a + self.between_distance 或者
        不可以从goal_index 到 location.osm_index 或者
        那么返回 true
        :param vehicle_location: 车辆位置
        :param order_location: 订单的位置
        :return 返回一个bool值 为真表示可以从goal_index到达目标节点，而不可以则要从osm_index到达目标节点
        ------
        注意：
        这个函数不可以修改 vehicle_location的值
        """
        distance_a = self.get_shortest_distance_by_osm_index(vehicle_location.osm_index, order_location.osm_index)  # 意义看文档
        distance_b = self.get_shortest_distance_by_osm_index(vehicle_location.goal_index, order_location.osm_index)  # 意义看文档
        distance_c = self.get_shortest_distance_by_osm_index(vehicle_location.osm_index, vehicle_location.goal_index)  # 意义看文档
        # 用于判断车是否从goal_index到order_location
        diff_distance = (distance_c - vehicle_location.driven_distance + distance_b) - (distance_a + vehicle_location.driven_distance)
        return is_enough_small(diff_distance, FLOAT_ZERO)

    def generate_random_locations(self, location_number: int, location_type) -> List[Union[OrderLocation, VehicleLocation]]:
        """
        用于放回一组地理位置
        :return:
        """
        xs = np.random.choice(self._x_list, location_number)
        ys = np.random.choice(self._y_list, location_number)
        locations_index = [self._convert_xy_to_index(xs[i], ys[i]) for i in range(location_number)]
        return [location_type(locations_index[i]) for i in range(location_number)]

    def move_to_random_index(self, vehicle_location: VehicleLocation, could_drive_distance: float) -> float:
        """
        :param vehicle_location:  车辆当前的位置
        :param could_drive_distance: 车辆可行行驶的距离
        ------
        注意： 这个函数会修改vehicle_location的值!!!!!!
        在一个时间间隔内，车辆随机路网上行驶
        """
        real_drive_distance = FLOAT_ZERO
        if vehicle_location.is_between:  # 车辆处于两个节点之间
            vehicle_to_goal_distance = self.get_shortest_distance_by_osm_index(vehicle_location.osm_index, vehicle_location.goal_index) - vehicle_location.driven_distance
            if is_enough_small(vehicle_to_goal_distance - could_drive_distance, DISTANCE_EPS):
                # 当可以将车移动到goal_index上的时候
                vehicle_location.set_location(vehicle_location.goal_index)
                real_drive_distance += vehicle_to_goal_distance  # 得到车辆当前行驶的距离
                could_drive_distance -= vehicle_to_goal_distance
            else:  # 不可以行驶动goal_index上
                vehicle_location.increase_driven_distance(could_drive_distance)  # 这样车辆还是会在两节点之间但是需要修改已经行驶的距离
                real_drive_distance += could_drive_distance  # 得到车辆当前行驶的距离
                could_drive_distance = FLOAT_ZERO

        if not is_enough_small(could_drive_distance, DISTANCE_EPS):  # 还可以继续行驶
            target_index = self._get_random_osm_index()
            if target_index != vehicle_location.osm_index:
                real_drive_distance += self.move_to_target_index(vehicle_location, target_index, could_drive_distance)

        return np.round(real_drive_distance)
