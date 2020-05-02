#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/11/4
import os
import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
import numpy as np
import pickle

from setting import GEO_DATA_FILE
graph = ox.load_graphml("Manhattan.graphml", "../raw_data/Manhattan_raw_data")
edges_distance = []
for edge in graph.edges(data=True):
    edges_distance.append(np.round(edge[2]["length"]))
    if edge[2]["oneway"]:
        edges_distance.append(np.round(edge[2]["length"]))
plt.hist(edges_distance, bins=5, histtype="stepfilled", alpha=0.6)
plt.show()

# 绘制图像看最长的道路
with open("../../data/Manhattan/network_data/index2osm_id.pkl", "rb") as file:
    index2osm_id = pickle.load(file)
node_number = len(graph.nodes)
base_folder = "../../data/Manhattan/network_data"
shortest_distance = np.load(os.path.join(base_folder, GEO_DATA_FILE["shortest_distance_file"]))
shortest_path = np.load(os.path.join(base_folder, GEO_DATA_FILE["shortest_path_file"]))
max_l = -np.inf
max_i = 0
max_j = 0
for i in range(node_number):
    for j in range(node_number):
        if shortest_path[i, j] == j and i != j and shortest_distance[i, j] != np.inf and max_l < shortest_distance[i, j]:
            max_i = i
            max_j = j
            max_l = shortest_distance[i, j]
print(max_l, max_i, max_j)
origin = index2osm_id[max_i]
destination = index2osm_id[max_j]
route = nx.shortest_path(graph, origin, destination)
ox.plot_graph_route(graph, route)
