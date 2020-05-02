#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/2/19
import osmnx as ox

raw_graph = ox.graph_from_place("Manhattan, New York City, New York, USA", network_type="drive")
graph_project = ox.project_graph(raw_graph)
ox.plot_graph(graph_project)
ox.save_graphml(raw_graph, filename="Manhattan.graphml", folder="../raw_data/Manhattan_raw_data")

raw_graph = ox.graph_from_place("New York City, New York, USA", network_type="drive")
graph_project = ox.project_graph(raw_graph)
ox.plot_graph(graph_project)
ox.save_graphml(raw_graph, filename="New_York.graphml", folder="../raw_data/New_York_raw_data")

graph = ox.graph_from_place("Chicago, USA", network_type="drive")
graph_project = ox.project_graph(graph)
ox.plot_graph(graph_project)
ox.save_graphml(graph, filename="Chicago.graphml", folder="../raw_data/Chicago_raw_data")

graph = ox.graph_from_place("HaiKou, China", network_type="drive")
graph_project = ox.project_graph(graph)
ox.plot_graph(graph_project)
ox.save_graphml(graph, filename="Hai_Kou.graphml", folder="../raw_data/Hai_Kou_raw_data")

graph = ox.graph_from_place("Shanghai, China", which_result=2, network_type='drive')
graph_project = ox.project_graph(graph)
ox.plot_graph(graph_project)
ox.save_graphml(graph, filename="Shang_Hai.graphml", folder="../raw_data/Shang_Hai_raw_data")
