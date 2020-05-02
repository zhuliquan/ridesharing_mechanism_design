#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/11/26
from setting import INPUT_VEHICLES_DATA_FILES, INPUT_ORDERS_DATA_FILES, SAVE_RESULT_FILES, MAX_REPEATS
from runner.simulator import Simulator


def run_simulation(_simulator: Simulator):
    for epoch in range(MAX_REPEATS):
        _simulator.reset()  # 这一步很重要一定要做
        _simulator.load_env(INPUT_VEHICLES_DATA_FILES[epoch], INPUT_ORDERS_DATA_FILES[epoch])
        _simulator.simulate()
        _simulator.save_simulate_result(SAVE_RESULT_FILES[epoch])


if __name__ == '__main__':
    simulator = Simulator()  # 这一步已经创建了所有的网络数目，平台情况

    # 运行算法， 这个要在上面语句已经成功执行之后执行，这句执行要把上面的注释掉
    run_simulation(simulator)
