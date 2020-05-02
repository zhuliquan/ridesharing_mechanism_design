#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/1/22
import json
import random
from urllib import parse

import requests

agents = [
    'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:21.0) Gecko/20100101 Firefox/21.0',
    'Mozilla/5.0 (Android; Mobile; rv:14.0) Gecko/14.0 Firefox/14.0',
    'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.94 Safari/537.36',
    'Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.133 Mobile Safari/535.19'
]

f = open("./raw_data/vehicle_fuel_consumption_info.csv", "w", encoding='utf-8')
f.write("车辆型号,生产企业,驱动型式,额定功率,变速器类型,发动机型号,车辆净重量,车辆最大重量,市郊油耗,市区油耗,综合油耗\n")
headers = {}
page_size = 200
page_num = 135
for i in range(1, page_num + 1):
    s = '{"goPage":' + str(i) + ',"orderBy":[{"orderBy":"pl","reverse":false}],"pageSize":' + str(
        page_size) + ',"queryParam":[{"shortName":"clzl","value":"clzl>cycM1l"}]}'
    s = parse.quote(s)
    s = parse.quote(s)
    url = "http://chaxun.miit.gov.cn/asopCmsSearch/searchIndex.jsp?params=" + s
    print(url)
    headers['User-Agent'] = agents[random.randint(0, len(agents) - 1)]
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        json_result = response.text
        json_result = json_result.replace("null(", "")
        json_result = json_result.replace(");", "")
        dict_result = json.loads(json_result)
        car_list = dict_result["resultMap"]
        for car_info in car_list:
            clxh = car_info.get('clxh', "NULL")  # 车辆型号  e.g. ELECTRIC UP EABAFA1001 唯一的id
            scqy = car_info.get('scqy', "NULL")  # 生产企业  e.g. 大众汽车股份公司
            qdxs = car_info.get('qdxs', "NULL")  # 驱动型式 e.g. 前轮驱动
            edgl = car_info.get('edgl', "NULL")  # 额定功率  单位 kw
            bsqlx = car_info.get('bsqlx', "NULL")  # 变速器类型  e.g. AT
            fdjxh = car_info.get('fdjxh', "NULL")  # 发动机型号 e.g. EAB
            zczbzl = car_info.get('zczbzl', "NULL")  # 车辆净重量 单位 kg
            zdsjzzl = car_info.get('zdsjzzl', "NULL")  # 车辆最大重量 单位 kg
            sjgk = car_info.get('sjgk', "NULL")  # 市郊油耗  单位 L/100km
            sqgk = car_info.get('sqgk', "NULL")  # 市区油耗  单位 L/100km
            zhgk = car_info.get('zhgk', "NULL")  # 综合油耗  单位 L/100km
            info = ",".join([clxh, scqy, qdxs, edgl, bsqlx, fdjxh, zczbzl, zdsjzzl, sjgk, sqgk, zhgk])
            f.write(info + "\n")
    else:
        print("not found")
f.close()
