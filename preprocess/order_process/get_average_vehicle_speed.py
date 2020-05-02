#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/11/28
import osmnx as ox
import pandas as pd
from setting import FLOAT_ZERO
from setting import MILE_TO_M
"""
直接通过已经筛选好的订单数据里面的运行历程除去时间计算平均值得到
"""
average_vehicle_speed = FLOAT_ZERO
for file_name in ["../raw_data/temp/Manhattan/order_data_{:03d}.csv".format(i) for i in range(30)]:
    csv_data = pd.read_csv(file_name)
    vehicle_speed = csv_data["order_distance"] / csv_data["order_time"] * MILE_TO_M * 3.6
    average_vehicle_speed += vehicle_speed.mean()

print(average_vehicle_speed / 30)
