#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/11/27
import numpy as np
from typing import Set
from collections import defaultdict
from utility import is_enough_small

"""
这个算法是来自滴滴的论文 Order Dispatch in Price-aware Ridesharing VLDB2018
"""


class Edge:
    __slots__ = ["p1", "p2", "distance"]

    def __init__(self, p1_index: int, p2_index: int, distance: float):
        self.p1 = p1_index
        self.p2 = p2_index
        self.distance = distance

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            raise Exception("类型不一致")
        else:
            return self.p1 == other.p1 and self.p2 == other.p2

    def __hash__(self):
        return hash((self.p1, self.p2))

    def __lt__(self, other):
        return self.distance < other.distance


def merge_point(p1: int, p2: int):
    covered_points.add(p1)
    covered_points.add(p2)
    point_children[p1].add(p2)


def check_merge_point_cluster(p1: int, p2: int):
    for p3 in point_children[p2]:
        if not is_enough_small(shortest_distance[p1, p3], threshold_distance):
            return False
    return True


def merge_point_cluster(p1: int, p2: int):
    """
    将以p2为中心的点集移动到p1的点上
    :param p1:
    :param p2:
    :return:
    """
    for p3 in point_children[p2]:
        point_children[p1].add(p3)
    point_children[p1].add(p2)
    # point_children.pop(p2)  # 以后不存在p2了


shortest_distance = np.load("../../data/Manhattan/network_data/shortest_distance.npy")
point_children: defaultdict = defaultdict(set)  # 第i个节点的孩子
covered_points: Set[int] = set()  # 已经被处理的节点

threshold_distance = 50.0
edges = [Edge(i, j, shortest_distance[i, j]) for i in range(shortest_distance.shape[0]) for j in range(shortest_distance.shape[1]) if 0 < shortest_distance[i, j] <= threshold_distance]
edges.sort()
print(edges[-1].distance)
for edge in edges:
    if edge.p1 not in covered_points and edge.p2 not in covered_points:
        merge_point(edge.p1, edge.p2)
    elif edge.p1 in point_children and edge.p2 in point_children:
        if check_merge_point_cluster(edge.p1, edge.p2):
            merge_point_cluster(edge.p1, edge.p2)
    elif edge.p1 in point_children and edge.p2 not in covered_points:
        merge_point(edge.p1, edge.p2)

center_points = set()
print(len(point_children))
for point in range(shortest_distance.shape[0]):
    if point in point_children:
        center_points.add(point)
    elif point not in covered_points:
        center_points.add(point)
print(len(center_points))
