#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/11/14
import os
import pickle
import osmnx as ox
import pandas as pd
from setting import GEO_DATA_FILE

result_dir = "../../data/Hai_Kou/order_data"
temp_dir = "../raw_data/temp/Hai_Kou/"
eps = 0.001


def time2int(time_str):
	_s = time_str.split(":")
	return str(int(_s[0]) * 60 * 60 + int(_s[1]) * 60 + int(_s[2]))


def list2str(lis):
	return ",".join(list(map(str, lis)))


# 筛选需要的字段
for file_index in range(1, 9):
	raw_order_filename = os.path.join("../raw_data/Hai_Kou_raw_data", "dwv_order_make_haikou_{0}.txt".format(file_index))
	temp1_file = open(os.path.join(temp_dir, "order_make_haikou_{0}.csv".format(file_index)), "w")
	with open(raw_order_filename, "r") as file:
		idx = 0
		for line in file:
			info = line.split('\t')
			if idx == 0:
				info = list(map(lambda x: x.split('.')[1], info))
				idx += 1
			new_info = [info[12]] + info[19:21] + info[17:19] + [info[14]] + [info[10]] + [info[13]]
			temp1_file.write(",".join(new_info) + '\n')
	temp1_file.close()

# 文件进行分割
date2file = dict()
for file_index in range(1, 9):
	with open(os.path.join(temp_dir, "order_make_haikou_{0}.csv".format(file_index)), "r") as file:
		idx = 0
		for line in file:
			info = line.split(',')
			if idx == 0:
				idx += 1
				continue
			info_date = info[0].split(' ')[0]
			info_time = info[0].split(' ')[1]
			if info_date not in date2file:
				date2file[info_date] = open(os.path.join(temp_dir, "temp1_order_make_haikou_{0}.csv".format(info_date)), "w")
				date2file[info_date].write("pick_time,pick_lon,pick_lat,drop_lon,drop_lat,n_riders,order_time,order_distance,order_fare\n")
			info = [time2int(info_time)] + info[1:5] + ["1"] + info[5:]
			date2file[info_date].write(",".join(info))

for date, file in date2file.items():
	file.close()

# 按时间排序且点对齐
G = ox.load_graphml("Hai_Kou.graph" + "ml", "../raw_data/Hai_Kou_raw_data")  # 注意：".graph"+"ml" 是不为了飘绿色
osm_id2index_file = GEO_DATA_FILE["osm_id2index_file"]
with open("../../data/Hai_Kou/network_data/" + osm_id2index_file, "rb") as file:
	osm_id2index = pickle.load(file)

dates = pd.date_range("2017-05-01", "2017-10-31")
dates = list(map(lambda _date: str(_date).split()[0], dates))
for date in dates:
	temp2_file = open(os.path.join(temp_dir, "temp2_order_make_haikou_{0}.csv".format(date)), "w")
	temp2_file.write("pick_time,pick_index,drop_index,n_riders,order_time,order_distance,order_fare\n")
	order_data = pd.read_csv(os.path.join(temp_dir, "temp1_order_make_haikou_{0}.csv".format(date)))
	order_data.sort_values(by=["pick_time"], inplace=True)
	order_data = order_data.values
	pick_lon = order_data[:, 1]
	pick_lat = order_data[:, 2]
	drop_lon = order_data[:, 3]
	drop_lat = order_data[:, 4]
	correct_pick_osm_ids = ox.get_nearest_nodes(G, pick_lon, pick_lat, method="balltree")
	correct_drop_osm_ids = ox.get_nearest_nodes(G, drop_lon, drop_lat, method="balltree")
	correct_pick_indexes = list(map(lambda osm_id: osm_id2index[osm_id], correct_pick_osm_ids))
	correct_drop_indexes = list(map(lambda osm_id: osm_id2index[osm_id], correct_drop_osm_ids))
	for idx in range(order_data.shape[0]):
		correct_corr_index = [correct_pick_indexes[idx], correct_drop_indexes[idx]]
		temp_list = [int(order_data[idx, 0])] + correct_corr_index + [int(order_data[idx, 5])] + order_data[idx, 6:].tolist()
		temp2_file.write(list2str(temp_list) + "\n")
	temp2_file.close()

dates = pd.date_range("2017-05-01", "2017-10-31")
dates = list(map(lambda _date: str(_date).split()[0], dates))
for i, date in enumerate(dates):
	order_data = pd.read_csv(os.path.join(temp_dir, "temp2_order_make_haikou_{0}.csv".format(date)))
	order_data["order_time"] = order_data["order_time"] * 60
	order_data.to_csv(os.path.join(result_dir, "order_data_{0:03}.csv".format(i)), sep=",", index=False)
