#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author : zlq16
# date   : 2019/2/20

# 转化坐标公式
# avg_longitude = gdf['geometry'].unary_union.centroid.x
#
# # calculate the UTM zone from this avg longitude and define the UTM
# # CRS to project
# utm_zone = int(math.floor((avg_longitude + 180) / 6.) + 1)
# utm_crs = {'datum': 'WGS84',
#            'ellps': 'WGS84',
#            'proj': 'utm',
#            'zone': utm_zone,
#            'units': 'm'}
#
# # project the GeoDataFrame to the UTM CRS
# projected_gdf = gdf.to_crs(utm_crs)