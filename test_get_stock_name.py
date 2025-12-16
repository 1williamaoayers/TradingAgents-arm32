#!/usr/bin/env python3
"""
测试使用get_stock_name_by_ticker获取股票名称
"""
import sys
sys.path.insert(0, '/app')

from tradingagents.dataflows.interface import get_stock_name_by_ticker

# 测试港股
test_stocks = [
    "09618",  # 京东集团
    "00700",  # 腾讯控股
    "09988",  # 阿里巴巴
    "01810",  # 小米集团
    "02525",  # 禾赛科技
    "02128",  # 中国联通？
]

print("=" * 60)
print("🧪 测试get_stock_name_by_ticker函数")
print("=" * 60)

for code in test_stocks:
    name = get_stock_name_by_ticker(code)
    print(f"{code:8} -> {name}")

print("=" * 60)
