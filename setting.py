#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/11/4
import numpy as np
import os

# 将一些常数实现为单例，节约空间
POINT_LENGTH = 2  # 计算小数点后面保留的精度
VALUE_EPS = 1E-8  # 浮点数相等的最小精度
FLOAT_ZERO = 0.0
INT_ZERO = 0
FIRST_INDEX = INT_ZERO
POS_INF = np.PINF
NEG_INF = np.NINF
MILE_TO_KM = 1.609344
MILE_TO_M = 1609.344
SECOND_OF_DAY = 86_400  # 24 * 60 * 60 一天有多少秒

# real_transport 和 grid_transport 实验都可以使用的数据 ######################################################################################################################
# 实验得环境 为"ROAD_MODE"表示真实的路网环境 为"GRID_MODE"表示虚拟网格环境
ROAD_MODE = "ROAD_MODE"
GRID_MODE = "GRID_MODE"
EXPERIMENTAL_MODE = ROAD_MODE
# 一组参数实验的重复次数
MAX_REPEATS = 1
# 订单分配算法的执行时间间隔 单位 s. 如果是路网环境 [10 15 20 25 30], 如果是网格环境 默认为1.
TIME_SLOT = 60
# 距离精度误差, 表示一个车辆到某一个点的距离小于这一个数, 那么就默认这个车已经到这个点上了 单位 m. 如果是实际的路网一般取10m, 如果是网格环境一般取0.
DISTANCE_EPS = 10
# 模拟一天的时刻最小值/最大值 单位 s.
# 如果是路网环境 MIN_REQUEST_TIME <= request_time < MAX_REQUEST_TIME 并且有 MAX_REQUEST_TIME - MIN_REQUEST_TIME 并且可以整除 TIME_SLOT.
# 如果是网格环境 MIN_REQUEST_TIME = 0, MIN_REQUEST_TIME = 500.
MIN_REQUEST_TIME, MAX_REQUEST_TIME = 19 * 60 * 60, 20 * 60 * 60
# 投标策略 "ADDITIONAL_COST" 以成本量的增加量作为投标 "ADDITIONAL_PROFIT" 以利润的增加量作为投标量
ADDITIONAL_COST_STRATEGY = "ADDITIONAL_COST_STRATEGY"
ADDITIONAL_PROFIT_STRATEGY = "ADDITIONAL_PROFIT_STRATEGY"
BIDDING_STRATEGY = ADDITIONAL_COST_STRATEGY
# 路线规划的目标 "MINIMIZE_COST" 最小化成本 "MAXIMIZE_PROFIT" 最大化利润
MINIMIZE_COST = "MINIMIZE_COST"
MAXIMIZE_PROFIT = "MAXIMIZE_PROFIT"
ROUTE_PLANNING_GOAL = MINIMIZE_COST
# 路线规划的方案 "INSERTING" 新的订单起始点直接插入而不改变原有订单起始位置顺序  "RESCHEDULING" 原有订单的起始位置进行重排
INSERTING = "INSERTING"
RESCHEDULING = "RESCHEDULING"
ROUTE_PLANNING_METHOD = INSERTING
# 平台使用的订单分发方式
NEAREST_DISPATCHING = "NEAREST-DISPATCHING"  # 通用的最近车辆分配算法
VCG_MECHANISM = "SWMOM-VCG"  # vcg 机制 这是一个简单的分配机制
GM_MECHANISM = "SWMOM-GM"  # gm 机制 这是一个简单的分配机制
SPARP_MECHANISM = "SPARP"  # SPARP 机制 这是一个通用分配机制
SEQUENCE_AUCTION = "SWMOM-SASP"  # 贯序拍卖机制 这是一个通用分配机制
DISPATCHING_METHOD = SPARP_MECHANISM

# 车辆设定 ##########
# 实验环境中的车辆数目
VEHICLE_NUMBER = 1800
# 实验环境中的车辆速度 单位 m/s. 对于任意的环境 VEHICLE_SPEED * TIME_SLOT >> DISTANCE_EPS. 纽约市规定是 (MILE_TO_KM * 25 / 3.6) m/s ≈ 10 m/s
# 但是根据资料纽约市的车辆速度只有7.2mph ~ 9.1mph 约等于 4.0 m/s (http://mini.eastday.com/a/190331120732879.html)
VEHICLE_SPEED = 4.0
# 车辆空余位置的选择范围  TODO 这个以后可能会修改, 添加更多的选择
N_SEATS = [4]


# 与 REAL 相关的配置 ###################################################################################################################################
# 与地理相关的数据存放点
New_York = "New_York"
Hai_Kou = "Hai_Kou"
Manhattan = "Manhattan"
GEO_NAME = Manhattan
GEO_BASE_FILE = "../data/{0}/network_data".format(GEO_NAME)
GRAPH_DATA_FILE = "../raw_data/{0}_raw_data/{0}.graphml".format(GEO_NAME)
OSM_ID2INDEX_FILE = os.path.join(GEO_BASE_FILE, "osm_id2index.pkl")
INDEX2OSM_ID_FILE = os.path.join(GEO_BASE_FILE, "index2osm_id.pkl")
SHORTEST_DISTANCE_FILE = os.path.join(GEO_BASE_FILE, "shortest_distance.npy")
SHORTEST_PATH_FILE = os.path.join(GEO_BASE_FILE, "shortest_path.npy")
ADJACENT_INDEX_FILE = os.path.join(GEO_BASE_FILE, "adjacent_index.pkl")
ACCESS_INDEX_FILE = os.path.join(GEO_BASE_FILE, "access_index.pkl")
ADJACENT_LOCATION_OSM_INDEX_FILE = os.path.join(GEO_BASE_FILE, "{0}/adjacent_location_osm_index.pkl".format(TIME_SLOT))
ADJACENT_LOCATION_DRIVEN_DISTANCE_FILE = os.path.join(GEO_BASE_FILE, "{0}/adjacent_location_driven_distance.pkl".format(TIME_SLOT))
ADJACENT_LOCATION_GOAL_INDEX_FILE = os.path.join(GEO_BASE_FILE, "{0}/adjacent_location_goal_index.pkl".format(TIME_SLOT))

# 订单数据存放地址
ORDER_BASE_FILE = "../data/{0}/order_data".format(GEO_NAME)
DEMAND_MODEL_FILE = os.path.join(ORDER_BASE_FILE, "demand_model.npy")
PICK_REGION_MODEL_FILE = os.path.join(ORDER_BASE_FILE, "pick_region_model.pkl")
DROP_REGION_MODEL_FILE = os.path.join(ORDER_BASE_FILE, "drop_region_model.pkl")
DEMAND_LOCATION_MODEL_FILE = os.path.join(ORDER_BASE_FILE, "demand_location_model.npy")
DEMAND_TRANSFER_MODEL_FILE = os.path.join(ORDER_BASE_FILE, "demand_transfer_model.npy")
UNIT_FARE_MODEL_FILE = os.path.join(ORDER_BASE_FILE, "unit_fare_model.npy")

# 订单缩放比
ORDER_NUMBER_RATIO = 1.0  # 就是实际生产出来的订单数目乘于一个比例
# 车辆油耗与座位数据存放地址
FUEL_CONSUMPTION_DATA_FILE = "../data/vehicle_data/fuel_consumption_and_seats.csv"
# 直接与此常数相乘可以得到单位距离的成本 $/m/(单位油耗)
VEHICLE_FUEL_COST_RATIO = 2.5 / 6.8 / MILE_TO_M
# 乘客最大绕路比可选范围
DETOUR_RATIOS = [0.25, 0.50, 0.75, 1.00]
# 乘客最大等待时间可选范围 单位 s
WAIT_TIMES = [3 * 60, 4 * 60, 5 * 60, 6 * 60, 7 * 60, 8 * 60]

# GRID 相关的设定 ######################################################################################################################################
# 网格的规模，横向/纵向的网格数目
GRAPH_SIZE = 100
# 每一个网格的大小
GRID_SIZE = 1.0

# 与环境创建相关的数据 #################################################################
INPUT_VEHICLES_DATA_FILES = ["../data/input/vehicles_data/{0}_{1}_{2}_{3}_{4}.csv".format(EXPERIMENTAL_MODE, i, VEHICLE_NUMBER, MIN_REQUEST_TIME, MAX_REQUEST_TIME) for i in range(MAX_REPEATS)]
INPUT_ORDERS_DATA_FILES = ["../data/input/orders_data/{0}_{1}_{2}_{3}.csv".format(EXPERIMENTAL_MODE, i, MIN_REQUEST_TIME, MAX_REQUEST_TIME) for i in range(MAX_REPEATS)]
SAVE_RESULT_FILES = ["../result/{0}/{1}_{2}_{3}_{4}_{5}_{6}.pkl".format(DISPATCHING_METHOD, EXPERIMENTAL_MODE, i, VEHICLE_NUMBER, TIME_SLOT, MIN_REQUEST_TIME, MAX_REQUEST_TIME) for i in range(MAX_REPEATS)]
