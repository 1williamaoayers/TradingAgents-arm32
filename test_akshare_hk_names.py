#!/usr/bin/env python3
"""
最终测试：使用AKShare API获取港股名称
"""
import sys
sys.path.insert(0, '/app')

from pymongo import MongoClient
from datetime import datetime
import akshare as ak

# 测试港股
test_stocks = [
    ("09618.HK", "港股"),  # 京东集团
    ("00700.HK", "港股"),  # 腾讯控股
    ("09988.HK", "港股"),  # 阿里巴巴
    ("01810.HK", "港股"),  # 小米集团
    ("02525.HK", "港股"),  # 禾赛科技
    ("02128.HK", "港股"),  # 验证真实名称
]

def get_hk_stock_name(symbol):
    """使用AKShare获取港股名称"""
    try:
        clean_symbol = symbol.replace('.HK', '')
        hk_info = ak.stock_hk_spot_em()
        matched = hk_info[hk_info['代码'] == clean_symbol]
        if not matched.empty:
            return matched.iloc[0]['名称']
    except Exception as e:
        print(f"  ❌ 查询失败: {e}")
    return symbol

print("=" * 60)
print("🧪 测试AKShare获取港股名称")
print("=" * 60)

for symbol, market in test_stocks:
    name = get_hk_stock_name(symbol)
    print(f"{symbol:12} -> {name}")

print("=" * 60)
