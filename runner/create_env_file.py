#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2020/1/2
from typing import List
import pickle
import numpy as np
import pandas as pd
from setting import MIN_REQUEST_TIME, MAX_REQUEST_TIME
from env.location import PickLocation, DropLocation, VehicleLocation
from env.network import Network
from preprocess.utility import RegionModel
from setting import SHORTEST_DISTANCE_FILE, SHORTEST_PATH_FILE, ACCESS_INDEX_FILE
from setting import ORDER_NUMBER_RATIO, MILE_TO_M, MAX_REPEATS
from setting import DEMAND_MODEL_FILE, DEMAND_LOCATION_MODEL_FILE, DEMAND_TRANSFER_MODEL_FILE, PICK_REGION_MODEL_FILE, DROP_REGION_MODEL_FILE, UNIT_FARE_MODEL_FILE
from setting import FUEL_CONSUMPTION_DATA_FILE, WAIT_TIMES, DETOUR_RATIOS, POINT_LENGTH, VEHICLE_FUEL_COST_RATIO
from setting import EXPERIMENTAL_MODE, ROAD_MODE, GRID_MODE, INPUT_ORDERS_DATA_FILES, INPUT_VEHICLES_DATA_FILES
from setting import N_SEATS, VEHICLE_NUMBER
from env.graph import BaseGraph, RoadGraph, GridGraph
from utility import load_bin_data


def generate_road_graph() -> BaseGraph:
    """
    生成实际的图
    :return:
    """
    shortest_distance = load_bin_data(SHORTEST_DISTANCE_FILE)
    shortest_path = load_bin_data(SHORTEST_PATH_FILE)
    access_index = load_bin_data(ACCESS_INDEX_FILE)
    return RoadGraph(shortest_distance=shortest_distance, shortest_path=shortest_path, access_index=access_index)


def generate_grid_graph() -> BaseGraph:
    from setting import GRAPH_SIZE
    from setting import GRID_SIZE
    return GridGraph(graph_size=GRAPH_SIZE, grid_size=GRID_SIZE)


def create_vehicle_data_file(_vehicle_number: int, _network: Network, _output_file: str):
    """
    用于生成用于模拟的文件
    :param _vehicle_number:
    :param _network:
    :param _output_file:
    :return:
    """
    locations: List[VehicleLocation] = _network.generate_random_locations(_vehicle_number, VehicleLocation)
    car_fuel_consumption_info = pd.read_csv(FUEL_CONSUMPTION_DATA_FILE)
    cars_info = car_fuel_consumption_info.sample(n=_vehicle_number)
    seats = np.random.choice(N_SEATS, size=_vehicle_number)
    unit_cost_info = cars_info["fuel_consumption"].values.astype(np.float) * VEHICLE_FUEL_COST_RATIO
    with open(_output_file, "w") as file:
        for vehicle_id in range(_vehicle_number):
            file.write(",".join(list(map(str, (locations[vehicle_id].to_file_index(), seats[vehicle_id], unit_cost_info[vehicle_id])))) + "\n")


def create_road_orders_data_file(output_file: str, *args, **kwargs):
    """
    将原始数据生成一个csv文件
    :param output_file: csv输出文件
    :return:
    """
    # 这个是将30天的数据合并之后的结果
    with open(PICK_REGION_MODEL_FILE, "rb") as file:
        pick_region_model: RegionModel = pickle.load(file)
    with open(DROP_REGION_MODEL_FILE, "rb") as file:
        drop_region_model: RegionModel = pickle.load(file)
    shortest_distance = np.load(SHORTEST_DISTANCE_FILE)
    unit_fare_model = np.load(UNIT_FARE_MODEL_FILE)
    demand_model = np.load(DEMAND_MODEL_FILE)
    demand_location_model = np.load(DEMAND_LOCATION_MODEL_FILE)
    demand_transfer_model = np.load(DEMAND_TRANSFER_MODEL_FILE)
    st_time_bin = MIN_REQUEST_TIME // 3600  # MIN_REQUEST_TIME 落在了哪一个时间区间上
    en_time_bin = (MAX_REQUEST_TIME - 1) // 3600  # MAX_REQUEST_TIME 落在了哪一个时间区间上
    # 第一个时间区域还需要生成的时间
    data_series = []
    for time_bin in range(st_time_bin, en_time_bin + 1):
        if st_time_bin == en_time_bin:  # 在同一个时间区间上
            demand_number = demand_model[time_bin] * (MAX_REQUEST_TIME - MIN_REQUEST_TIME) / 3600
        elif time_bin == st_time_bin:
            demand_number = demand_model[time_bin] * ((st_time_bin + 1) * 3600 - MIN_REQUEST_TIME) / 3600
        elif time_bin == en_time_bin:
            demand_number = demand_model[time_bin] * (MAX_REQUEST_TIME - en_time_bin * 3600) / 3600
        else:
            demand_number = demand_model[time_bin]
        demand_number = demand_number * ORDER_NUMBER_RATIO
        demand_prob_location = demand_location_model[time_bin]
        demand_prob_transfer = demand_transfer_model[time_bin]
        demand_number_of_each_transfer = np.zeros(shape=demand_prob_transfer.shape, dtype=np.int32)
        for i in range(demand_prob_transfer.shape[0]):
            demand_number_of_each_transfer[i] = np.round(demand_prob_location[i] * demand_prob_transfer[i] * demand_number, 0)
        for i in range(demand_number_of_each_transfer.shape[0]):
            for j in range(demand_number_of_each_transfer.shape[1]):
                d_n_of_t = demand_number_of_each_transfer[i, j]
                temp_order_data = pd.DataFrame()
                temp_order_data["request_time"] = np.random.randint(3600 * time_bin, 3600 * (time_bin + 1), size=d_n_of_t)
                temp_order_data["wait_time"] = np.random.choice(WAIT_TIMES, size=d_n_of_t)
                temp_order_data["pick_index"] = np.array([pick_region_model.get_rand_index_by_region_id(i) for _ in range(d_n_of_t)], dtype=np.int16)
                temp_order_data["drop_index"] = np.array([drop_region_model.get_rand_index_by_region_id(j) for _ in range(d_n_of_t)], dtype=np.int16)
                temp_order_data["order_distance"] = shortest_distance[temp_order_data.pick_index.values, temp_order_data.drop_index.values]
                temp_order_data["order_fare"] = np.round(temp_order_data["order_distance"] * unit_fare_model[time_bin] / MILE_TO_M, POINT_LENGTH)
                temp_order_data["detour_ratio"] = np.random.choice(DETOUR_RATIOS, size=d_n_of_t)
                temp_order_data = temp_order_data[(temp_order_data["order_distance"] != np.inf) & (temp_order_data["order_distance"] >= 1000.0)]
                temp_order_data = temp_order_data[["request_time", "wait_time", "pick_index", "drop_index", "order_distance", "order_fare", "detour_ratio"]]
                data_series.append(temp_order_data)
    order_data: pd.DataFrame = pd.concat(data_series, axis=0, ignore_index=True)
    order_data = order_data.sort_values(by="request_time", axis=0, ascending=True)
    order_data.to_csv(output_file, index=False)


def create_grid_orders_data_file(output_file: str, *args, **kwargs):
    """
    网格路网环境中的订单生成和时间流逝
    我们生成订单的方式可以参考论文 An Online Mechanism for Ridesharing in Autonomous Mobility-on-Demand Systems (IJCAI2016)
    """
    _network: Network = kwargs["network"]
    order_series = []
    unit_fare_model = np.load(UNIT_FARE_MODEL_FILE)
    st_time_bin = MIN_REQUEST_TIME // 3600  # MIN_REQUEST_TIME 落在了哪一个时间区间上
    en_time_bin = (MAX_REQUEST_TIME - 1) // 3600  # MAX_REQUEST_TIME 落在了哪一个时间区间上
    demand_model = np.load(DEMAND_MODEL_FILE)
    for time_bin in range(st_time_bin, en_time_bin + 1):
        if st_time_bin == en_time_bin:  # 在同一个时间区间上
            demand_number = demand_model[time_bin] * (MAX_REQUEST_TIME - MIN_REQUEST_TIME) / 3600
        elif time_bin == st_time_bin:
            demand_number = demand_model[time_bin] * ((st_time_bin + 1) * 3600 - MIN_REQUEST_TIME) / 3600
        elif time_bin == en_time_bin:
            demand_number = demand_model[time_bin] * (MAX_REQUEST_TIME - en_time_bin * 3600) / 3600
        else:
            demand_number = demand_model[time_bin]
        demand_number = demand_number * ORDER_NUMBER_RATIO
        temp_order_data = pd.DataFrame()
        temp_order_data["request_time"] = np.random.randint(3600 * time_bin, 3600 * (time_bin + 1), size=demand_number)
        temp_order_data["wait_time"] = np.random.choice(WAIT_TIMES, size=(demand_number,))
        pick_locations = _network.generate_random_locations(demand_number, PickLocation)
        drop_locations = _network.generate_random_locations(demand_number, DropLocation)
        temp_order_data["pick_index"] = np.array([location.to_file_index() for location in pick_locations])
        temp_order_data["drop_index"] = np.array([location.to_file_index() for location in drop_locations])
        temp_order_data["order_distance"] = np.array([_network.get_shortest_distance(pick_locations[idx], drop_locations[idx]) for idx in range(demand_number)])
        temp_order_data["order_fare"] = np.round(temp_order_data.order_distance * unit_fare_model[time_bin], POINT_LENGTH)
        temp_order_data["detour_ratio"] = np.random.choice(DETOUR_RATIOS, size=(demand_number,))
        temp_order_data = temp_order_data[temp_order_data.pick_index != temp_order_data.drop_index]
        temp_order_data = temp_order_data[["request_time", "wait_time", "pick_index", "drop_index", "order_distance", "order_fare", "detour_ratio"]]
        order_series.append(temp_order_data)
    order_data: pd.DataFrame = pd.concat(order_series, axis=0, ignore_index=True)
    order_data.to_csv(output_file, index=False)


def create_network():
    if EXPERIMENTAL_MODE == ROAD_MODE:
        BaseGraph.set_generate_graph_function(generate_road_graph)
    elif EXPERIMENTAL_MODE == GRID_MODE:
        BaseGraph.set_generate_graph_function(generate_grid_graph)
    else:
        raise Exception("目前还没有实现其实验模式")
    _network = Network(BaseGraph.generate_graph())
    return _network


def create_order_data_files(_network: Network):
    # 生成订单数目
    if EXPERIMENTAL_MODE == ROAD_MODE:
        for epoch in range(MAX_REPEATS):
            create_road_orders_data_file(INPUT_ORDERS_DATA_FILES[epoch])
    elif EXPERIMENTAL_MODE == GRID_MODE:
        for epoch in range(MAX_REPEATS):
            create_grid_orders_data_file(INPUT_ORDERS_DATA_FILES[epoch], _network)
    else:
        raise Exception("目前还没有开发别的类型的订单模型")


def create_vehicle_data_files(_network: Network):
    # 生成车辆
    for epoch in range(MAX_REPEATS):
        create_vehicle_data_file(VEHICLE_NUMBER, _network, INPUT_VEHICLES_DATA_FILES[epoch])


# 生成用于实验的数据
if __name__ == '__main__':
    network = create_network()
    create_vehicle_data_files(network)
    create_order_data_files(network)
