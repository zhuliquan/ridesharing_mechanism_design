#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/2/21
import array
import os

import networkx as nx
import numpy as np

from setting import DISTANCE_EPS, VEHICLE_SPEED
from setting import GEO_BASE_FILE
from setting import GRAPH_DATA_FILE, OSM_ID2INDEX_FILE, INDEX2OSM_ID_FILE
from setting import SHORTEST_DISTANCE_FILE, SHORTEST_PATH_FILE, ACCESS_INDEX_FILE, ADJACENT_INDEX_FILE
from setting import ADJACENT_LOCATION_DRIVEN_DISTANCE_FILE, ADJACENT_LOCATION_OSM_INDEX_FILE, ADJACENT_LOCATION_GOAL_INDEX_FILE
from setting import TIME_SLOT
from utility import is_enough_small
from utility import print_execute_time
from utility import save_bin_data, load_bin_data


@print_execute_time
def create_multi_di_graph():
    multi_graph = nx.MultiDiGraph()
    multi_graph.add_nodes_from(graph.nodes(data=True))
    for u, v, d in graph.edges(data=True):
        if d["oneway"]:
            multi_graph.add_edge(u, v, length=d["length"])
        else:
            multi_graph.add_edge(u, v, length=d["length"])
            multi_graph.add_edge(v, u, length=d["length"])
    return multi_graph


@print_execute_time
def compute_shortest_distance():
    """
    shortest_distance 用于查询任意两点之间的最短路径长度 单位长度m
    1. i==j, shortest_distance[i,j] = 0;
    2. i不可以到达j, shortest_distance[i, j] = np.inf
    """
    shortest_distance = np.ones(shape=(node_number, node_number), dtype=np.float32) * np.inf
    for lengths in nx.all_pairs_dijkstra_path_length(di_graph, weight="length"):
        index_i = osm_id2index[lengths[0]]
        for osm_id_j, distance in lengths[1].items():
            index_j = osm_id2index[osm_id_j]
            shortest_distance[index_i, index_j] = np.round(distance)
        print(index_i)
    save_bin_data(os.path.join("..", SHORTEST_DISTANCE_FILE), shortest_distance)


@print_execute_time
def compute_shortest_path():
    """
    shortest_path 记录两点按照最短路径走下一步会到哪个节点
    1. shortest_distance[i, j] == 0.0, shortest_path[i, j] = -1;
    2. shortest_distance[i, j] == np.inf, shortest_path[i, j] = -2;
    """
    shortest_distance = load_bin_data(os.path.join("..", SHORTEST_DISTANCE_FILE))
    shortest_path = np.ones(shape=(node_number, node_number), dtype=np.int16) * -2
    access_index = [array.array('h') for _ in range(node_number)]  # 可以到达的节点
    adjacent_index = [array.array('h') for _ in range(node_number)]  # 周围相邻的节点
    for paths in nx.all_pairs_dijkstra_path(di_graph, weight="length"):
        index_i = osm_id2index[paths[0]]
        s_access_index = set()
        s_adjacent_index = set()
        for osm_id_j, path in paths[1].items():
            index_j = osm_id2index[osm_id_j]
            if index_i == index_j:
                shortest_path[index_i, index_j] = -1
            elif shortest_distance[index_i, index_j] == np.inf:
                shortest_path[index_i, index_j] = -2
            else:
                next_index = osm_id2index[path[1]]
                shortest_path[index_i, index_j] = next_index
                s_access_index.add(index_j)
                s_adjacent_index.add(next_index)

        for j in s_access_index:
            access_index[index_i].append(j)
        for j in s_adjacent_index:
            adjacent_index[index_i].append(j)
        print(index_i)
    save_bin_data(os.path.join("..", SHORTEST_PATH_FILE), shortest_path)
    save_bin_data(os.path.join("..", ACCESS_INDEX_FILE), access_index)
    save_bin_data(os.path.join("..", ADJACENT_INDEX_FILE), adjacent_index)


@print_execute_time
def compute_shortest_path_time_slot():
    """
    这些文件用于车辆随机更新
    :return:
    """
    shortest_distance = load_bin_data(SHORTEST_DISTANCE_FILE)
    adjacent_location_osm_index = [array.array('h') for _ in range(node_number)]  # 一个时间间隔可以到达的节点
    adjacent_location_driven_distance = [array.array('f') for _ in range(node_number)]  # 一个时间间隔到达某一个节点之后还多行驶的一段距离
    adjacent_location_goal_index = [array.array('h') for _ in range(node_number)]  # 一个时间间隔到达某一个节点之后多行驶朝向方向

    if not os.path.exists(GEO_BASE_FILE + "/{0}".format(TIME_SLOT)):
        os.mkdir(GEO_BASE_FILE + "/{0}".format(TIME_SLOT))

    for paths in nx.all_pairs_dijkstra_path(di_graph, weight="length"):
        index_i = osm_id2index[paths[0]]
        for osm_id_j, path in paths[1].items():
            index_j = osm_id2index[osm_id_j]
            if index_i == index_j or shortest_distance[index_i, index_j] == np.inf:  # 1. 压根没有后续节点的情况
                continue
            if not is_enough_small(could_drive_distance - shortest_distance[index_i, index_j], DISTANCE_EPS):
                # 2. 由于index_i 到 index_j的距离太小了车不会停在index_j上
                continue

            simulated_could_drive_distance = could_drive_distance  # 用于模拟车辆行驶
            for prv_path_osm_id, cur_path_osm_id in zip(path[:-1], path[1:]):
                prv_path_index = osm_id2index[prv_path_osm_id]
                cur_path_index = osm_id2index[cur_path_osm_id]
                two_index_distance = shortest_distance[prv_path_index, cur_path_index]

                if is_enough_small(two_index_distance - simulated_could_drive_distance, DISTANCE_EPS):
                    simulated_could_drive_distance -= two_index_distance
                    if is_enough_small(simulated_could_drive_distance, DISTANCE_EPS):
                        adjacent_location_osm_index[index_i].append(cur_path_index)
                        adjacent_location_driven_distance[index_i].append(0.0)
                        adjacent_location_goal_index[index_i].append(cur_path_index)
                        break
                else:
                    adjacent_location_osm_index[index_i].append(prv_path_index)
                    adjacent_location_driven_distance[index_i].append(simulated_could_drive_distance)
                    adjacent_location_goal_index[index_i].append(cur_path_index)
                    break
        print(index_i)
    save_bin_data(os.path.join("..", ADJACENT_LOCATION_OSM_INDEX_FILE), adjacent_location_osm_index)
    save_bin_data(os.path.join("..", ADJACENT_LOCATION_DRIVEN_DISTANCE_FILE), adjacent_location_driven_distance)
    save_bin_data(os.path.join("..", ADJACENT_LOCATION_GOAL_INDEX_FILE), adjacent_location_goal_index)


if __name__ == '__main__':
    could_drive_distance = np.round(VEHICLE_SPEED * TIME_SLOT)  # 车辆在一个时间间隔内可以行驶的距离

    # load raw data
    graph = load_bin_data(GRAPH_DATA_FILE)

    # osm_id2index = {}
    # index2osm_id = {}
    # for i, osm_id in enumerate(graph.nodes):
    #     osm_id2index[osm_id] = i
    #     index2osm_id[i] = osm_id

    # save_bin_data(os.path.join("..", OSM_ID2INDEX_FILE), osm_id2index)
    # save_bin_data(os.path.join("..", INDEX2OSM_ID_FILE), index2osm_id)

    osm_id2index = load_bin_data(os.path.join("..", OSM_ID2INDEX_FILE))
    index2osm_id = load_bin_data(os.path.join("..", INDEX2OSM_ID_FILE))
    node_number = len(osm_id2index)
    di_graph = create_multi_di_graph()
    # 计算最短路径长度矩阵
    compute_shortest_distance()

    # 得到下到一个节点的需要经过的节点
    compute_shortest_path()

    # 计算到一个节点过程中一分钟可以到哪些节点
    # compute_shortest_path_time_slot()
