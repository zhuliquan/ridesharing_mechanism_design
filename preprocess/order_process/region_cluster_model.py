#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/12/9
import pandas as pd
import pickle
import matplotlib.pyplot as plt
from sklearn.cluster import MiniBatchKMeans

from preprocess.utility import RegionModel
plt.rcParams["font.sans-serif"] = ["STSong"]
n_cluster = 40
df = pd.read_csv("../raw_data/temp/points.csv")
pick_cluster = MiniBatchKMeans(n_clusters=n_cluster, batch_size=100000).fit(df[["pick_lon", "pick_lat"]].values).predict(df[["pick_lon", "pick_lat"]])
drop_cluster = MiniBatchKMeans(n_clusters=n_cluster, batch_size=100000).fit(df[["drop_lon", "drop_lat"]].values).predict(df[["drop_lon", "drop_lat"]])
plt.figure(figsize=(14, 6))
plt.subplot(1, 2, 1)
# plt.figure(figsize=(7, 6))
plt.scatter(
    x=df.pick_lon.values[:50000],
    y=df.pick_lat.values[:50000],
    c=pick_cluster[:50000],
    cmap="Paired",
    s=10
)
plt.title("出发地聚类结果", fontsize=16)
plt.xticks(fontsize=16)
plt.yticks(fontsize=16)
plt.xlabel("经度", fontsize=16)
plt.ylabel("纬度", fontsize=16)

plt.savefig('./pick_up_location_region.eps', format='eps', dpi=1000)
plt.subplot(1, 2, 2)
# plt.figure(figsize=(7, 6))
plt.scatter(
    x=df.drop_lon.values[:50000],
    y=df.drop_lat.values[:50000],
    c=drop_cluster[:50000],
    cmap="Paired",
    s=10
)
plt.title("目的地聚类结果", fontsize=16)
plt.xticks(fontsize=16)
plt.yticks(fontsize=16)
plt.xlabel("经度", fontsize=16)
plt.ylabel("纬度", fontsize=16)
plt.savefig("./drop_off_location_region.eps", format='eps', dpi=1000)
plt.show()

pick_index2region_id = dict()
drop_index2region_id = dict()
pick_indexes = df.pick_index.values
drop_indexes = df.drop_index.values

for i in range(df.shape[0]):
    pick_index2region_id[pick_indexes[i]] = pick_cluster[i]
    drop_index2region_id[drop_indexes[i]] = drop_cluster[i]

pick_region_model = RegionModel(pick_index2region_id)
drop_region_model = RegionModel(drop_index2region_id)

with open("../../data/Manhattan/order_data/pick_region_model.pkl", "wb") as f:
    pickle.dump(pick_region_model, f)

with open("../../data/Manhattan/order_data/drop_region_model.pkl", "wb") as f:
    pickle.dump(drop_region_model, f)

print(pick_region_model.region_number)
print(drop_region_model.region_number)
