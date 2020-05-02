#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/1/23
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# car_type 车辆类型
# product_company 生产企业
# driving_mode 驱动型式
# transmission 变速器类型
# engine_style 发动机类型
# power 额定功率
# pair_social_welfare 车辆净重量
# max_weight 车辆最大重量
# Suburban_fuel_consumption 市郊油耗
# Urban_fuel_consumption 市区油耗
# Comprehensive_fuel_consumption 综合油耗


raw_data = pd.read_csv("./raw_data/vehicle_fuel_consumption_info.csv", error_bad_lines=False, encoding="gb18030")
print(raw_data.shape)
export_data = raw_data[raw_data["车辆型号"] != "NULL"]
export_data = export_data[export_data["生产企业"] != "NULL"]
export_data = export_data[export_data["驱动型式"] != "NULL"]
export_data = export_data[export_data["变速器类型"] != "NULL"]
export_data = export_data[export_data["发动机型号"] != "NULL"]
export_data = export_data[export_data["额定功率"] != 0]
export_data = export_data[export_data["车辆净重量"] >= 870]
export_data = export_data[export_data["车辆最大重量"] >= 870]
export_data = export_data[export_data["市郊油耗"] != 0]
export_data = export_data[export_data["市区油耗"] != 0]
export_data = export_data[export_data["综合油耗"] != 0]
print(export_data.shape)

# # 添加座位信息

# n = export_data.shape[0]
# car_info = export_data.sort_values(by="pair_social_welfare")
# seats = np.zeros(shape=(n,), dtype=np.int8)
# car_info["seats"] = seats
# car_info["pair_social_welfare"].hist()
# plt.show()
# car_info.to_csv("./data/vehicle_data/fuel_consumption_and_seats.csv", index=False)

