#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/12/27
from setting import INT_ZERO, VALUE_EPS
import numpy as np
from typing import List, Set, Tuple
from setting import POINT_LENGTH
from env.order import Order
from agent.vehicle import Vehicle
from algorithm.simple_dispatching.matching_graph import BipartiteGraph


class MarketClearingMatchingGraph(BipartiteGraph):
    """
    利用市场清仓算法进行匹配工作，利用商品价格递增来去进行求解
    """
    __slots__ = ["epsilon"]

    def __init__(self, feasible_vehicles: Set[Vehicle], feasible_orders: Set[Order]):
        super(MarketClearingMatchingGraph, self).__init__(feasible_vehicles, feasible_orders)
        self.epsilon = 1 / pow(10, POINT_LENGTH)  # TODO 这递增值需要修改, 这个对于算法性能有很大的影响，这里暂时不使用这个算法

    @staticmethod
    def _is_prefect_matching(matches: List, m: int, n: int):
        m_o = np.ones(shape=(m,), dtype=np.int16) * -1
        m_v = np.ones(shape=(n,), dtype=np.int16) * -1
        v_v = np.zeros(shape=(n,), dtype=np.bool)

        def _greedy_matching() -> int:
            _cnt = INT_ZERO
            for i in range(m):
                for j in matches[i]:
                    if m_o[i] == -1 and m_v[j] == -1:
                        m_o[i], m_v[j] = j, i
                        _cnt += 1
                        break
            return _cnt

        def _find_augmenting_path(i: int) -> bool:
            for j in matches[i]:
                if v_v[j]:
                    continue
                v_v[j] = True
                if m_v[j] == -1 or _find_augmenting_path(m_v[j]):
                    m_o[i], m_v[j] = j, i
                    return True
            return False

        cnt = _greedy_matching()
        for _i in range(m):
            if m_o[_i] == -1:
                v_v = v_v * False
                if _find_augmenting_path(_i):
                    cnt += 1

        if cnt == m:
            return True, m_o
        else:
            return False, None

    @staticmethod
    def _get_match_result(payoff: np.ndarray):
        m, n = payoff.shape
        bid_cnt = np.zeros(n, dtype=np.int32)
        matches = [np.array([]) for _ in range(m)]
        for i in range(m):
            each_line = payoff[i, :]
            arg_max_idx = np.argwhere(np.abs(each_line - np.amax(each_line)) <= VALUE_EPS).flatten()
            matches[i] = arg_max_idx
            bid_cnt[arg_max_idx] += 1
        return bid_cnt, matches

    def maximal_weight_matching(self, return_match=False) -> Tuple[float, List[Tuple[Vehicle, Order]]]:
        if self.deny_vehicle_index != -1:
            sw_matrix = np.row_stack((self.pair_social_welfare_matrix[:self.deny_vehicle_index, :], self.pair_social_welfare_matrix[self.deny_vehicle_index+1:, :]))
        else:
            sw_matrix = self.pair_social_welfare_matrix.copy()

        if 0 in sw_matrix.shape:  # 如果存在一个维度不存在
            return 0, []

        if sw_matrix.shape[0] > sw_matrix.shape[1]:
            sw_matrix = sw_matrix.T
            transposed = True
        else:
            transposed = False

        m, n = sw_matrix.shape
        prices = np.zeros(shape=(n,))
        while True:
            payoff = np.round(sw_matrix - prices, 2)
            bid_cnt, matches = self._get_match_result(payoff)
            is_feasible, prefect_matching = self._is_prefect_matching(matches, m, n)
            if is_feasible:
                print(sw_matrix.shape[0], len(prefect_matching))
                social_welfare = np.round(sw_matrix[range(len(prefect_matching)), prefect_matching].sum(), POINT_LENGTH)
                match_pairs = []
                if return_match:
                    for i, j in enumerate(prefect_matching):
                        if transposed:
                            vehicle_index, order_index = j, i
                        else:
                            vehicle_index, order_index = i, j
                        if self.deny_vehicle_index != -1 and vehicle_index >= self.deny_vehicle_index:
                            vehicle_index += 1
                        vehicle = self.index2vehicle[vehicle_index]
                        order = self.index2order[order_index]
                        if order in self.vehicle_link_orders[vehicle]:
                            match_pairs.append((vehicle, order))
                return social_welfare, match_pairs
            else:
                prices[np.argwhere(bid_cnt > 1).flatten()] += self.epsilon
