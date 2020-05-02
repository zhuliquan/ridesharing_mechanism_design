#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/12/9
"""
这里我们认为订单到来满足泊松过程，具体学习过程可以参考论文  T-Share: A Large-Scale Dynamic Taxi Ridesharing Service (ICDE2013)
位置p，在t时刻，需要学习会有多少订单生成N_p^t, 然后转移矩阵A_p_q^t， 就是t时段从p到q的转移概率，还有t时段单位费率f_t在这一时段单位价钱
我们将一天分成了24个时间段，每一个时间段的过程统计起始点分布，终止点分布，还有平均价格
"""
import pickle
import numpy as np
import pandas as pd
from preprocess.utility import RegionModel

with open("../../data/Manhattan/order_data/pick_region_model.pkl", "rb") as file1:
    pick_region_model: RegionModel = pickle.load(file1)
with open("../../data/Manhattan/order_data/drop_region_model.pkl", "rb") as file2:
    drop_region_model: RegionModel = pickle.load(file2)

weekends = {3, 4, 10, 11, 17, 18, 24, 25}  # 我们对于周末不感兴趣
weekday = set(range(30)) - weekends
unit_fare = np.zeros(shape=(len(weekday), 24), dtype=np.float32)
demand_num_of_time = np.zeros(shape=(len(weekday), 24), dtype=np.int32)
demand_prob_location_of_time = np.zeros(shape=(len(weekday), 24, pick_region_model.region_number), dtype=np.float32)
demand_prob_transfer_of_time = np.zeros(shape=(len(weekday), 24, pick_region_model.region_number, drop_region_model.region_number), dtype=np.float32)

for i, day in enumerate(weekday):  # 学习概率在不同的时刻不同位置的转移概率
    order_data_day = pd.read_csv("../raw_data/temp/Manhattan/order_data_{:03d}.csv".format(day))
    for j in range(24):
        demand = order_data_day[order_data_day.pick_time >= j * 3600]
        demand = demand[demand.pick_time < (j+1) * 3600]
        demand_num_of_time[i, j] = demand.shape[0]
        unit_fare[i, j] = np.mean((demand.order_fare / demand.order_distance).values)
        pick_region_ids = list(map(pick_region_model.get_region_id_by_index, demand.pick_index.values))
        drop_region_ids = list(map(drop_region_model.get_region_id_by_index, demand.drop_index.values))
        df = pd.DataFrame({"pick_region_id": pick_region_ids, "drop_region_id": drop_region_ids})
        for pick_region_id, df_pick in df.groupby(by="pick_region_id"):
            demand_prob_location_of_time[i, j, pick_region_id] = df_pick.shape[0]
            for drop_region_id, df_drop in df_pick.groupby(by="drop_region_id"):
                demand_prob_transfer_of_time[i, j, pick_region_id, drop_region_id] = df_drop.shape[0]
            d_d_min = np.min(demand_prob_transfer_of_time[i, j, pick_region_id])
            d_d_max = np.max(demand_prob_transfer_of_time[i, j, pick_region_id])
            demand_prob_transfer_of_time[i, j, pick_region_id] = (demand_prob_transfer_of_time[i, j, pick_region_id] - d_d_min) / (d_d_max - d_d_min)
        d_min = np.min(demand_prob_location_of_time[i, j])
        d_max = np.max(demand_prob_location_of_time[i, j])
        demand_prob_location_of_time[i, j] = demand_prob_location_of_time[i, j] - d_min / (d_max - d_min)


unit_fare = np.mean(unit_fare, axis=0)  # 1dim 24 每一个时刻单位费用
demand_num_of_time = np.mean(demand_num_of_time, axis=0)  # 1dim 24 每一个时刻订单数目
demand_prob_location_of_time = np.mean(demand_prob_location_of_time, axis=0)  # 2dim 24 * 40  每一个时刻每一个区域的订单数目
demand_prob_transfer_of_time = np.mean(demand_prob_transfer_of_time, axis=0)  # 3dim 24 * 40 * 40 每一个时刻每一个区域转移的概率

for time in range(24):
    demand_prob_location_of_time[time] = demand_prob_location_of_time[time] / np.sum(demand_prob_location_of_time[time])
for time in range(24):
    for pick_region_id in range(pick_region_model.region_number):
        demand_prob_transfer_of_time[time, pick_region_id] = demand_prob_transfer_of_time[time, pick_region_id] / np.sum(demand_prob_transfer_of_time[time, pick_region_id])

np.save("../../data/Manhattan/order_data/unit_fare_model.npy", unit_fare)
np.save("../../data/Manhattan/order_data/demand_model.npy", demand_num_of_time)
np.save("../../data/Manhattan/order_data/demand_location_model.npy", demand_prob_location_of_time)
np.save("../../data/Manhattan/order_data/demand_transfer_model.npy", demand_prob_transfer_of_time)
