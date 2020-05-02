#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/6/26
"""
我们按照如下步骤进行数据清洗
1. 我们首先剔除不合理的数据例如 起始点和终止点都是一致的，还有订单价格过大国小，行驶距离国小等等
2. 我们将订单的起始点和终止点对齐到纽约市地图数据上的网格节点上
3. 我们提取起始点和终止点都在曼哈顿岛上的数据，并合并黄绿出租车
4. 我们按照时间排序，并输出到指定的文件上
"""
import os
import pickle
import osmnx as ox
import pandas as pd
import numpy as np
import networkx as nx
from sklearn.neighbors import BallTree
from setting import SECOND_OF_DAY
result_dir = "../../data/Manhattan/order_data"
new_york_temp_dir = "../raw_data/temp/New_York/"
manhattan_temp_dir = "../raw_data/temp/Manhattan"
green, yellow = "green", "yellow"
chunk_size = 100000


def time2int(time, gap=0):
    _s = time.split(":")
    return str(int(_s[0]) * 60 * 60 + int(_s[1]) * 60 + int(_s[2]) + gap)


def list2str(lis):
    return ",".join(list(map(str, lis)))


def get_nearest_nodes(lon, lat):
    points = np.array([lat.astype(np.float), lon.astype(np.float)]).T
    points_rad = np.deg2rad(points)
    nn = nodes.iloc[tree.query(points_rad, k=1, return_distance=False)[:, 0]].index  # query the tree for nearest node to each point
    return np.array(nn)


if not os.path.exists(new_york_temp_dir):
    os.mkdir(new_york_temp_dir)

if not os.path.exists(manhattan_temp_dir):
    os.mkdir(manhattan_temp_dir)

# 纽约市剔除异常数据
for color in [green, yellow]:
    raw_order_filename = os.path.join("../raw_data/New_York_raw_data", "{0}_trip_data_2016-06.csv".format(color))
    new_york_temp_result_file1 = os.path.join(new_york_temp_dir, "{0}_temp1.csv".format(color))
    cnt = 0
    temp_file = open(new_york_temp_result_file1, "w")
    temp_file.write(",".join(["day", "pick_time", "drop_time", "pick_longitude", "pick_latitude", "drop_longitude", "drop_latitude", "n_riders", "order_distance", "fare_amount", "tip_amount", "total_amount"]) + "\n")
    for csv_iterator in pd.read_table(raw_order_filename, chunksize=chunk_size, iterator=True):
        for line in csv_iterator.values:
            s = line[0].split(',')
            if color == green:
                if -74.15 <= float(s[5]) <= -73.7004 and 40.5774 <= float(s[6]) <= 40.9176 and -74.15 <= float(s[7]) <= -73.7004 and 40.5774 <= float(s[8]) <= 40.9176 and \
                        s[9] != '0' and 0.5 <= float(s[10]) <= 50 and 0 < float(s[11]) <= 100 and float(s[11]) > 2.5:
                    date1 = s[1].split(" ")[0].split("-")[-1]
                    date2 = s[2].split(" ")[0].split("-")[-1]
                    s[1] = time2int(s[1].split(" ")[1])
                    s[2] = time2int(s[2].split(" ")[1], gap=(int(date2) - int(date1)) * SECOND_OF_DAY)
                    if 60 < (int(s[2]) - int(s[1])) <= 2 * 3600 and float(s[10]) * 1000 / (int(s[2]) - int(s[1])) < 40 / 3.6:
                        s = s[1:3] + s[5:12] + s[14:15] + s[18:19]
                        temp_file.write(date1 + "," + ",".join(s) + "\n")
                        cnt += 1
            else:
                if -74.15 <= float(s[5]) <= -73.7004 and 40.5774 <= float(s[6]) <= 40.9176 and -74.15 <= float(s[9]) <= -73.7004 and 40.5774 <= float(s[10]) <= 40.9176 and \
                        s[3] != '0' and 0.5 <= float(s[4]) <= 50 and 0 < float(s[12]) <= 100 and float(s[12]) > 2.5:
                    date1 = s[1].split(" ")[0].split("-")[-1]
                    date2 = s[2].split(" ")[0].split("-")[-1]
                    s[1] = time2int(s[1].split(" ")[1])
                    s[2] = time2int(s[2].split(" ")[1], gap=(int(date2) - int(date1)) * SECOND_OF_DAY)
                    if 60 < (int(s[2]) - int(s[1])) <= 2 * 3600 and float(s[4]) * 1000 / (int(s[2]) - int(s[1])) < 40 / 3.6:
                        s = s[1:3] + s[5:7] + s[9:11] + s[3:5] + s[12:13] + s[15:16] + s[18:19]
                        temp_file.write(date1 + "," + ",".join(s) + "\n")
                        cnt += 1

    print(cnt)
    temp_file.close()

# 纽约市点对齐
NewYork_G = ox.load_graphml("New_York.graph" + "ml", "../../data/New_York_raw_data/")  # 注意：".graph"+"ml" 是不为了飘绿色
nodes = pd.DataFrame({'x': nx.get_node_attributes(NewYork_G, 'x'), 'y': nx.get_node_attributes(NewYork_G, 'y')})
nodes_rad = np.deg2rad(nodes[['y', 'x']].astype(np.float))
tree = BallTree(nodes_rad, metric='haversine')

for color in [green, yellow]:
    new_york_temp_result_file1 = os.path.join(new_york_temp_dir, "{0}_temp1.csv".format(color))
    new_york_temp_result_file2 = os.path.join(new_york_temp_dir, "{0}_temp2.csv".format(color))
    temp_file = open(new_york_temp_result_file2, "w")
    temp_file.write(",".join(["day", "pick_time", "drop_time", "pick_som_id", "drop_osm_id", "n_riders", "order_distance", "tip_amount", "total_amount"]) + "\n")
    cnt = 0
    for csv_iterator in pd.read_table(new_york_temp_result_file1, chunksize=chunk_size, iterator=True):
        data = np.array([list(map(float, line[0].split(","))) for line in csv_iterator.values])
        pick_lon, pick_lat = data[:, 3], data[:, 4]
        drop_lon, drop_lat = data[:, 5], data[:, 6]
        correct_pick_osm_ids = get_nearest_nodes(pick_lon, pick_lat)
        correct_drop_osm_ids = get_nearest_nodes(drop_lon, drop_lat)
        for idx in range(data.shape[0]):
            temp_list = data[idx, :3].tolist() + [correct_pick_osm_ids[idx], correct_drop_osm_ids[idx]] + data[idx, 7:].tolist()
            temp_file.write(list2str(temp_list) + "\n")
            cnt += 1
            if cnt % chunk_size == 0:
                print(cnt)
    print(cnt)
    temp_file.close()

# 提取只在曼哈顿的数据合并黄绿出租车的订单数据
Manhattan_G = ox.load_graphml("Manhattan.graph" + "ml", "../raw_data/Manhattan_raw_data/")
ok_nodes = set(Manhattan_G.nodes)
with open(os.path.join("../../data/Manhattan/network_data/", "osm_id2index.pkl"), "rb") as file:
    osm_id2index = pickle.load(file)
manhattan_temp_result_file1 = open(os.path.join(manhattan_temp_dir, "manhattan_order_temp.csv"), "w")
manhattan_temp_result_file1.write(",".join(["day", "pick_time", "drop_time", "pick_osm_id", "drop_osm_id", "n_riders", "order_distance", "order_fare", "order_tip", "total_fare"]) + "\n")
for color in [green, yellow]:
    temp_color_result_file = os.path.join(new_york_temp_dir, "{0}_temp2.csv".format(color))
    for csv_iterator in pd.read_table(temp_color_result_file, chunksize=chunk_size, iterator=True):
        for line in csv_iterator.values:
            s = line[0].split(",")
            if int(s[3]) not in ok_nodes or int(s[4]) not in ok_nodes or int(s[3]) == int(s[4]):
                continue
            manhattan_temp_result_file1.write(",".join(s) + "\n")
manhattan_temp_result_file1.close()
