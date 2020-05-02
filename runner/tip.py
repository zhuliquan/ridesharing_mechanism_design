#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2020/1/2
"""
这个函数可以用于从实际的
"""
import numpy as np
import pandas as pd
from setting import MIN_REQUEST_TIME, MAX_REQUEST_TIME
from setting import WAIT_TIMES, DETOUR_RATIOS
from setting import POINT_LENGTH
from setting import SHORTEST_DISTANCE_FILE


def create_real_road_orders_data_file(output_file: str, *args, **kwargs):
    """
    实际路网环境中的订单生成和时间流逝
    :return:
    """
    # 这个是由真实的订单数据的生成需要的结果
    shortest_distance = np.load(SHORTEST_DISTANCE_FILE)
    order_data = pd.read_csv("../preprocess/raw_data/temp/Manhattan/order_data_{0:03d}.csv".format(0))
    order_data = order_data[(MIN_REQUEST_TIME <= order_data.pick_time) & (order_data.pick_time < MAX_REQUEST_TIME)]
    order_data = order_data[shortest_distance[order_data.pick_index, order_data.drop_index] != np.inf]
    order_data = order_data[shortest_distance[order_data.pick_index, order_data.drop_index] >= 1000.0]  # 过于短的或者订单的距离是无穷大
    order_data["wait_time"] = np.random.choice(WAIT_TIMES, size=order_data.shape[0])
    order_data["order_distance"] = shortest_distance[order_data.pick_index, order_data.drop_index]
    order_data["detour_ratio"] = np.random.choice(DETOUR_RATIOS, size=order_data.shape[0])
    order_data.drop(columns=["order_tip", "total_fare"], axis=1, inplace=True)
    order_data = order_data.rename(columns={'pick_time': 'request_time'})
    order_data["request_time"] = order_data["request_time"].values.astype(np.int32)
    order_data["order_fare"] = np.round(order_data["order_fare"].values, POINT_LENGTH)
    order_data = order_data[["request_time", "wait_time", "pick_index", "drop_index", "order_distance", "order_fare", "detour_ratio"]]
    order_data.to_csv(output_file, index=False)
