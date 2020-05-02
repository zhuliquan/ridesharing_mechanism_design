#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/12/9
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
weekends = {3, 4, 10, 11, 17, 18, 24, 25}
weekday = set(range(30)) - weekends
for i, day in enumerate(weekday):
    r, c = i // 5, i % 5
    df = pd.read_csv("../raw_data/temp/Manhattan/order_data_{:03d}.csv".format(day))
    num = np.zeros(shape=24)
    for j in range(24):
        d = df[(df.pick_time >= j * 3600) & (df.pick_time < (j + 1) * 3600)]
        num[j] = d.shape[0]
    plt.subplot(6, 5, i+1)
    plt.plot(num)
    plt.xlim()
    # ax[r][c].hist(df.pick_time.values)

plt.show()

# f, ax = plt.subplots(5, 5)
# for i, day in enumerate(weekday):
#     r, c = i // 5, i % 5
#     df = pd.read_csv("../raw_data/temp/Manhattan/order_data_{:03d}.csv".format(day))
#     unit_fare = np.zeros(shape=24)
#     for j in range(24):
#         d = df[(df.pick_time >= j * 3600) & (df.pick_time < (j + 1) * 3600)]
#         unit_fare[j] = np.mean((d["order_fare"] / d["order_distance"]).values)
#     ax[r][c].plot(unit_fare)
# plt.show()
#
# plt.figure()
# demand_model = np.load("../../data/Manhattan/order_data/demand_model.npy")
# plt.plot(range(len(demand_model)), demand_model, 'r-d', linewidth=3, markersize=10, markerfacecolor='k', markeredgewidth=3)
# plt.xlim([0, 23])
# plt.xlabel("Hour of Day")
# plt.ylabel("Number of Query")
# plt.grid(True)
# plt.show()
#
# plt.figure()
# unit_fare = np.load("../../data/Manhattan/order_data/unit_fare_model.npy")
# plt.plot(range(len(unit_fare)), unit_fare, 'r-d', linewidth=3, markersize=10, markerfacecolor='k', markeredgewidth=3)
# plt.xlabel("Hour of Day")
# plt.ylabel("Unit Fare of Day ($/mile)")
# plt.xlim([0, 23])
#
# plt.grid(True)
# plt.show()
#
# plt.figure()
# demand_location_model = np.load("../../data/Manhattan/order_data/demand_location_model.npy")
# plt.plot(range(len(demand_location_model[0])), demand_location_model[0], "r-d", linewidth=3, markersize=10, markerfacecolor='k', markeredgewidth=3)
# plt.plot(range(len(demand_location_model[23])), demand_location_model[23], "b-d", linewidth=3, markersize=10, markerfacecolor='k', markeredgewidth=3)
# plt.xlabel("Pick up Region of Id")
# plt.grid(True)
# plt.show()
#
# plt.figure()
# demand_transfer_model = np.load("../../data/Manhattan/order_data/demand_transfer_model.npy")
# drop_transfer = demand_transfer_model[0].T * demand_location_model[0]
# drop_transfer = np.sum(drop_transfer, axis=0)
# plt.plot(range(len(drop_transfer)), drop_transfer, "r-o",  linewidth=3, markersize=10, markerfacecolor='k', markeredgewidth=3)
# drop_transfer = demand_transfer_model[1].T * demand_location_model[1]
# drop_transfer = np.sum(drop_transfer, axis=0)
# plt.plot(range(len(drop_transfer)), drop_transfer, "b-o",  linewidth=3, markersize=10, markerfacecolor='k', markeredgewidth=3)
# plt.xlabel("Drop off Region of Id")
# plt.grid(True)
# plt.show()
