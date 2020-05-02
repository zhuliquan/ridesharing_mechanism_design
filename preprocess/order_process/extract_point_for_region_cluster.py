#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/12/8
import pickle

import osmnx as ox
import pandas as pd

with open("../../data/Manhattan/network_data/osm_id2index.pkl", "rb") as f:
    osm_id2index = pickle.load(f)
with open("../../data/Manhattan/network_data/index2osm_id.pkl", "rb") as f:
    index2osm_id = pickle.load(f)
G = ox.load_graphml("Manhattan.graphml", "../raw_data/Manhattan_raw_data")

nodes = G.nodes(data=True)
index2point = {osm_id2index[node[0]]: (node[1]["x"], node[1]['y']) for node in nodes}

point_file = open("../raw_data/temp/points.csv", "w")
point_file.write("pick_index,drop_index,pick_lon,pick_lat,drop_lon,drop_lat\n")
weekends = {3, 4, 10, 11, 17, 18, 24, 25}  # 我们对于周末不感兴趣
weekday = set(range(30)) - weekends
for day in weekday:
    df = pd.read_csv("../raw_data/temp/Manhattan/order_data_{0:03d}.csv".format(day))
    pick_indexes = df.pick_index.values
    drop_indexes = df.drop_index.values
    for i in range(len(pick_indexes)):
        p = pick_indexes[i]
        d = drop_indexes[i]
        p_point = index2point[p]
        d_point = index2point[d]
        point_file.write("{0},{1},{2},{3},{4},{5}\n".format(p, d, p_point[0], p_point[1], d_point[0], d_point[1]))
point_file.close()
