#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/12/12
from collections import defaultdict
from typing import Dict

import numpy as np


class RegionModel:
    """
    这个类可以根据输入的类坐标位置，返回区域编号
    也可以根据区域编号返回这个区域内所有的坐标编号
    也可以随机返回这个区域内的一个随机的一个坐标号
    """
    __slots__ = ["index2region_id", "region_id2index", "region_number"]

    def __init__(self, index2region_id: Dict[int, int]):
        self.index2region_id = index2region_id
        self.region_id2index = defaultdict(list)
        for index, region_id in self.index2region_id.items():
            self.region_id2index[region_id].append(index)

        for region_id in self.region_id2index:
            self.region_id2index[region_id] = list(set(self.region_id2index[region_id]))

        self.region_number = len(self.region_id2index)

    def get_region_id_by_index(self, index: int):
        return self.index2region_id[index]

    def get_all_index_by_region_id(self, region_id: int):
        return self.region_id2index[region_id]

    def get_rand_index_by_region_id(self, region_id: int):
        return np.random.choice(self.region_id2index[region_id])