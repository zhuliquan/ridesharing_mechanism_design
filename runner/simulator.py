#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/2/22
from typing import List, NoReturn, Set
from agent.platform import Platform
from agent.proxy_bidder import AdditionalProfitBidder, AdditionalCostBidder
from agent.vehicle import Vehicle
from algorithm.generic_dispatching.auction import second_price_sequence_auction
from algorithm.generic_dispatching.baseline import sparp_mechanism, nearest_vehicle_dispatching
from algorithm.simple_dispatching.auction import vcg_mechanism, greedy_mechanism
from algorithm.route_planning.planner import InsertingPlanner, ReschedulingPlanner
from setting import INSERTING, RESCHEDULING, VEHICLE_SPEED
from setting import MINIMIZE_COST, MAXIMIZE_PROFIT
from setting import ROAD_MODE, GRID_MODE, ADDITIONAL_COST_STRATEGY, ADDITIONAL_PROFIT_STRATEGY, NEAREST_DISPATCHING, VCG_MECHANISM, GM_MECHANISM, SPARP_MECHANISM, SEQUENCE_AUCTION
from runner.create_env_file import create_network
from env.order import Order
from env.network import Network
from setting import BIDDING_STRATEGY, DISPATCHING_METHOD, EXPERIMENTAL_MODE, ROUTE_PLANNING_GOAL
from setting import TIME_SLOT, MIN_REQUEST_TIME, INT_ZERO


class Simulator:
    __slots__ = [
        "network", "vehicles", "orders", "platform", "time_slot",
        "current_time",
        "social_welfare_trend", "social_cost_trend", "total_driver_rewards_trend", "total_driver_payoffs_trend", "platform_profit_trend",
        "accumulate_service_ratio_trend", "total_orders_number_trend", "serviced_orders_number_trend",
        "empty_vehicle_number_trend", "total_vehicle_number_trend", "empty_vehicle_ratio_trend",
        "accumulate_service_distance_trend", "accumulate_random_distance_trend",
        "each_orders_service_time_trend", "each_orders_wait_time_trend", "each_orders_detour_ratio_trend",
        "each_vehicles_reward", "each_vehicles_payoff", "each_vehicles_finish_order_number", "each_vehicles_service_distance", "each_vehicles_random_distance",
        "bidding_time_trend", "running_time_trend",
    ]

    def __init__(self):
        network = create_network()

        if DISPATCHING_METHOD == VCG_MECHANISM:
            mechanism = vcg_mechanism
        elif DISPATCHING_METHOD == GM_MECHANISM:
            mechanism = greedy_mechanism
        elif DISPATCHING_METHOD == SPARP_MECHANISM:
            mechanism = sparp_mechanism
        elif DISPATCHING_METHOD == SEQUENCE_AUCTION:
            mechanism = second_price_sequence_auction
        elif DISPATCHING_METHOD == NEAREST_DISPATCHING:
            mechanism = nearest_vehicle_dispatching
        else:
            raise Exception("目前还没有实现其他类型的订单分配机制")
        platform = Platform(mechanism)

        # 初始化模拟器的变量
        self.platform: Platform = platform
        self.vehicles: List[Vehicle] = list()
        self.orders = None  # 实则是一个生成器
        self.network: Network = network
        self.time_slot: int = TIME_SLOT
        self.current_time = MIN_REQUEST_TIME
        self.social_welfare_trend = list()
        self.social_cost_trend = list()
        self.total_driver_rewards_trend = list()
        self.total_driver_payoffs_trend = list()
        self.platform_profit_trend = list()
        self.total_orders_number_trend = list()
        self.serviced_orders_number_trend = list()
        self.accumulate_service_ratio_trend = list()
        self.empty_vehicle_number_trend = list()
        self.total_vehicle_number_trend = list()
        self.empty_vehicle_ratio_trend = list()
        self.accumulate_service_distance_trend = list()
        self.accumulate_random_distance_trend = list()
        self.each_orders_service_time_trend = list()
        self.each_orders_wait_time_trend = list()
        self.each_orders_detour_ratio_trend = list()
        self.each_vehicles_reward = list()
        self.each_vehicles_payoff = list()
        self.each_vehicles_finish_order_number = list()
        self.each_vehicles_service_distance = list()
        self.each_vehicles_random_distance = list()
        self.bidding_time_trend = list()
        self.running_time_trend = list()

    def load_env(self, vehicles_data_file, orders_data_file):
        """
        首先加载环境，然后
        :return:
        """
        # 模拟器构造环境
        if BIDDING_STRATEGY == ADDITIONAL_COST_STRATEGY:
            proxy_bidder = AdditionalCostBidder()
        elif BIDDING_STRATEGY == ADDITIONAL_PROFIT_STRATEGY:
            proxy_bidder = AdditionalProfitBidder()
        else:
            raise Exception("目前还没有实现其他投标方式")
        from setting import ROUTE_PLANNING_METHOD

        if ROUTE_PLANNING_GOAL == MINIMIZE_COST:
            from algorithm.route_planning.optimizer import MinimizeCostOptimizer
            optimizer = MinimizeCostOptimizer()
        elif ROUTE_PLANNING_GOAL == MAXIMIZE_PROFIT:
            from algorithm.route_planning.optimizer import MaximizeProfitOptimizer
            optimizer = MaximizeProfitOptimizer()
        else:
            optimizer = None

        if ROUTE_PLANNING_METHOD == INSERTING:
            route_planner = InsertingPlanner(optimizer)
        elif ROUTE_PLANNING_METHOD == RESCHEDULING:
            route_planner = ReschedulingPlanner(optimizer)
        else:
            raise Exception("目前还没有实现其他的路线规划方式")
        self.vehicles = Vehicle.load_vehicles_data(VEHICLE_SPEED, self.time_slot, proxy_bidder, route_planner, vehicles_data_file)
        self.orders = Order.load_orders_data(MIN_REQUEST_TIME, self.time_slot, orders_data_file)

    def save_simulate_result(self, file_name):
        import pickle
        result = [
            self.social_welfare_trend,
            self.social_cost_trend,
            self.total_driver_rewards_trend,
            self.total_driver_payoffs_trend,
            self.platform_profit_trend,
            self.total_orders_number_trend,
            self.serviced_orders_number_trend,
            self.accumulate_service_ratio_trend,
            self.empty_vehicle_ratio_trend,
            self.bidding_time_trend,
            self.running_time_trend,
            self.accumulate_service_distance_trend,
            self.accumulate_random_distance_trend,
            self.each_orders_wait_time_trend,
            self.each_orders_service_time_trend,
            self.each_orders_detour_ratio_trend,
            self.each_vehicles_reward,
            self.each_vehicles_payoff,
            self.each_vehicles_finish_order_number,
            self.each_vehicles_service_distance,
            self.each_vehicles_random_distance
        ]
        with open(file_name, "wb") as file:
            pickle.dump(result, file)

    def reset(self):
        """
        一个模拟之前的整理工作, 将上一步结果清空
        """
        self.platform.reset()
        self.orders = None
        self.vehicles = None
        self.social_welfare_trend.clear()
        self.social_cost_trend.clear()
        self.total_driver_rewards_trend.clear()
        self.total_driver_payoffs_trend.clear()
        self.platform_profit_trend.clear()
        self.total_orders_number_trend.clear()
        self.serviced_orders_number_trend.clear()
        self.accumulate_service_ratio_trend.clear()
        self.empty_vehicle_number_trend.clear()
        self.total_vehicle_number_trend.clear()
        self.empty_vehicle_ratio_trend.clear()
        self.accumulate_service_distance_trend.clear()
        self.accumulate_random_distance_trend.clear()
        self.each_orders_service_time_trend.clear()
        self.each_orders_wait_time_trend.clear()
        self.each_orders_detour_ratio_trend.clear()
        self.each_vehicles_reward.clear()
        self.each_vehicles_payoff.clear()
        self.each_vehicles_finish_order_number.clear()
        self.each_vehicles_service_distance.clear()
        self.each_vehicles_random_distance.clear()
        self.bidding_time_trend.clear()
        self.running_time_trend.clear()

    def simulate(self):
        for current_time, new_orders in self.orders:  # orders 是一个生成器
            self.current_time = current_time
            self.platform.merge_orders(new_orders, current_time, self.network)
            # self.platform.round_based_process(self.vehicles, new_orders, self.current_time, self.network)  # 订单分发和司机定价
            # self.trace_vehicles_info()  # 车辆更新信息
            # self.summary_each_round_result(new_orders)  # 统计匹配结果
            # print(
            #     "at {0} social welfare {1} driver payoffs {2} platform profit {3} empty vehicle ratio {4:.4f} service ratio {5:.4f} bidding time {6:.4f} running time {7:.4f}".format(
            #         current_time,
            #         self.social_welfare_trend[-1],
            #         self.total_driver_payoffs_trend[-1],
            #         self.platform_profit_trend[-1],
            #         self.empty_vehicle_ratio_trend[-1],
            #         self.accumulate_service_ratio_trend[-1],
            #         self.bidding_time_trend[-1],
            #         self.running_time_trend[-1],
            #     )
            # )
        #
        # # 等待所有车辆完成订单之后结束
        # self.current_time += self.time_slot
        # self.finish_all_orders()

    def trace_vehicles_info(self, print_vehicle=False) -> NoReturn:
        """
        更新车辆信息
        :return:
        """
        mechanism = self.platform.dispatching_mechanism
        empty_vehicle_number = INT_ZERO
        total_vehicle_number = INT_ZERO
        for vehicle in self.vehicles:
            if not vehicle.is_activated:
                continue
            total_vehicle_number += 1
            if vehicle not in mechanism.dispatched_vehicles and not vehicle.have_service_mission:
                vehicle.drive_on_random(self.network)
                empty_vehicle_number += 1
            else:
                if vehicle in mechanism.dispatched_vehicles:
                    dispatching_result = mechanism.dispatched_results[vehicle]
                    for order in dispatching_result.orders:
                        order.set_belong_vehicle(vehicle)
                    vehicle.set_route(dispatching_result.driver_route)
                    vehicle.increase_earn_reward(dispatching_result.driver_reward)
                    vehicle.increase_earn_profit(dispatching_result.driver_payoff)
                finish_orders = vehicle.drive_on_route(self.current_time, self.network)  # 下一个 time_slot 车的位置
                for order in finish_orders:
                    self.each_orders_wait_time_trend.append(order.real_wait_time)
                    self.each_orders_service_time_trend.append(order.real_service_time)
                    self.each_orders_detour_ratio_trend.append(order.real_detour_ratio)

                if print_vehicle:
                    print(vehicle)
        self.empty_vehicle_number_trend.append(empty_vehicle_number)
        self.total_vehicle_number_trend.append(total_vehicle_number)
        self.empty_vehicle_ratio_trend.append(empty_vehicle_number / total_vehicle_number)

    def finish_all_orders(self):
        Vehicle.set_could_drive_distance(10000000.0)  # 设置一个很大的值，让车辆不可能走完，自然就会在放下所有乘客自动停下
        for vehicle in self.vehicles:
            if not vehicle.is_activated:
                continue
            if vehicle.have_service_mission:
                finish_orders = vehicle.drive_on_route(self.current_time, self.network)
                for order in finish_orders:
                    self.each_orders_wait_time_trend.append(order.real_wait_time)
                    self.each_orders_service_time_trend.append(order.real_service_time)
                    self.each_orders_detour_ratio_trend.append(order.real_detour_ratio)

            self.each_vehicles_reward.append(vehicle.earn_reward)
            self.each_vehicles_payoff.append(vehicle.earn_profit)
            self.each_vehicles_finish_order_number.append(vehicle.finish_orders_number)
            self.each_vehicles_service_distance.append(vehicle.service_driven_distance)
            self.each_vehicles_random_distance.append(vehicle.random_driven_distance)
            if vehicle.have_service_mission:
                raise Exception("有这么长订单路线吗")
        self.accumulate_service_distance_trend.append(sum([vehicle.service_driven_distance for vehicle in self.vehicles if vehicle.is_activated]))
        self.accumulate_random_distance_trend.append(sum([vehicle.random_driven_distance for vehicle in self.vehicles if vehicle.is_activated]))

        # data = []
        # import pickle
        # for vehicle in self.vehicles:
        #     each_data = [vehicle.vehicle_id, vehicle.unit_cost, vehicle.available_seats, vehicle.earn_profit, vehicle.earn_reward, vehicle.finish_orders_number, vehicle.service_driven_distance, vehicle.random_driven_distance]
        #     data.append(each_data)
        # with open("../test/data.pkl", "wb") as file:
        #     pickle.dump(data, file)

    def summary_each_round_result(self, new_orders: Set[Order]) -> NoReturn:
        """
        总结这次分配的结果
        :param new_orders: 新的订单
        :return:
        """
        mechanism = self.platform.dispatching_mechanism
        self.social_welfare_trend.append(mechanism.social_welfare)
        self.social_cost_trend.append(mechanism.social_cost)
        self.total_driver_rewards_trend.append(mechanism.total_driver_rewards)
        self.total_driver_payoffs_trend.append(mechanism.total_driver_payoffs)
        self.platform_profit_trend.append(mechanism.platform_profit)
        self.serviced_orders_number_trend.append(len(mechanism.dispatched_orders))
        self.total_orders_number_trend.append(len(new_orders))
        if sum(self.total_orders_number_trend) != 0:
            self.accumulate_service_ratio_trend.append(sum(self.serviced_orders_number_trend) / sum(self.total_orders_number_trend))
        self.bidding_time_trend.append(mechanism.bidding_time)
        self.running_time_trend.append(mechanism.running_time)
        self.accumulate_service_distance_trend.append(sum([vehicle.service_driven_distance for vehicle in self.vehicles if vehicle.is_activated]))
        self.accumulate_random_distance_trend.append(sum([vehicle.random_driven_distance for vehicle in self.vehicles if vehicle.is_activated]))
