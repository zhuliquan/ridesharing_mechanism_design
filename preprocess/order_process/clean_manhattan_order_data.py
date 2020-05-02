#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/12/11
import os
import pickle
from setting import MILE_TO_M
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

manhattan_order_data = pd.read_csv("../raw_data/temp/Manhattan/manhattan_order_temp.csv")

# 首先转换osm_id -> index
with open(os.path.join("../../data/Manhattan/network_data/", "osm_id2index.pkl"), "rb") as file:
    osm_id2index = pickle.load(file)
manhattan_order_data["pick_index"] = np.array(list(map(lambda osm_id: osm_id2index[osm_id], manhattan_order_data["pick_osm_id"].values)))
manhattan_order_data["drop_index"] = np.array(list(map(lambda osm_id: osm_id2index[osm_id], manhattan_order_data["drop_osm_id"].values)))
manhattan_order_data = manhattan_order_data.drop(columns=["pick_osm_id", "drop_osm_id"], axis=1)

# 求解订单行驶时间, 并修改相关标签名
manhattan_order_data["order_time"] = manhattan_order_data["drop_time"] - manhattan_order_data["pick_time"]
manhattan_order_data = manhattan_order_data.drop(["drop_time"], axis=1)

# 剔除距离上比较奇怪的数据
shortest_distance = np.load("../../data/Manhattan/network_data/shortest_distance.npy")
manhattan_order_data = manhattan_order_data[shortest_distance[manhattan_order_data.pick_index, manhattan_order_data.drop_index] != np.inf]
manhattan_order_data = manhattan_order_data[np.abs(manhattan_order_data.order_distance * MILE_TO_M - shortest_distance[manhattan_order_data.pick_index, manhattan_order_data.drop_index]) / (shortest_distance[manhattan_order_data.pick_index, manhattan_order_data.drop_index]) <= 1.0]
manhattan_order_data = manhattan_order_data[manhattan_order_data.order_distance * MILE_TO_M <= shortest_distance[manhattan_order_data.pick_index, manhattan_order_data.drop_index] * 2]
manhattan_order_data = manhattan_order_data[manhattan_order_data.order_distance < 15]

# 将订单的尺度变成剔除奇怪的时间
manhattan_order_data = manhattan_order_data[manhattan_order_data.order_time < 6000]

# 将订单的行驶距离不合理的剔除
manhattan_order_data = manhattan_order_data[(manhattan_order_data.order_distance * MILE_TO_M / manhattan_order_data.order_time >= 4 / 3.6) &
                                            (manhattan_order_data.order_distance * 1000 / manhattan_order_data.order_time <= 40 / 3.6)]

# 将订单的价格不合理的剔除
manhattan_order_data = manhattan_order_data[(manhattan_order_data.order_fare - 2.5) / manhattan_order_data.order_distance > 1.3]
manhattan_order_data = manhattan_order_data[(manhattan_order_data.order_fare - 2.5) / manhattan_order_data.order_distance < 10]

# 保存订单数据
for day, df_day in manhattan_order_data.groupby("day"):
    day = int(day)
    df_day = df_day.sort_values(by="pick_time", axis=0, ascending=True)
    df_day.drop(columns=["day"], axis=1, inplace=True)
    df_day.to_csv("../raw_data/temp/Manhattan/order_data_{:03d}.csv".format(day-1), index=False)
