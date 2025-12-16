#!/usr/bin/env python3
"""测试AKShare获取09618数据"""
import akshare as ak
from datetime import datetime

print("=" * 80)
print("=== 测试AKShare获取09618数据 ===")
print("=" * 80)

# 1. 测试实时行情
try:
    print("\n1. 测试实时行情...")
    df = ak.stock_hk_spot_em()
    jd_data = df[df['代码'] == '09618']
    if not jd_data.empty:
        print(f"✅ 实时行情获取成功")
        print(f"   股票名称: {jd_data['名称'].values[0]}")
        print(f"   最新价: {jd_data['最新价'].values[0]}")
        print(f"   涨跌幅: {jd_data['涨跌幅'].values[0]}%")
    else:
        print("❌ 未找到09618数据")
except Exception as e:
    print(f"❌ 实时行情获取失败: {e}")

# 2. 测试历史K线
try:
    print("\n2. 测试历史K线...")
    df = ak.stock_hk_hist(symbol="09618", period="daily", start_date="20241201", end_date="20241215", adjust="qfq")
    if not df.empty:
        print(f"✅ 历史K线获取成功")
        print(f"   数据行数: {len(df)}")
        print(f"   最新日期: {df.index[-1]}")
        print(f"   最新收盘价: {df['收盘'].iloc[-1]}")
    else:
        print("❌ 历史K线数据为空")
except Exception as e:
    print(f"❌ 历史K线获取失败: {e}")

# 3. 测试财务数据
try:
    print("\n3. 测试财务数据...")
    df = ak.stock_financial_abstract_em(symbol="09618")
    if not df.empty:
        print(f"✅ 财务数据获取成功")
        print(f"   数据行数: {len(df)}")
        print(f"   最新报告期: {df['报告期'].iloc[0]}")
    else:
        print("⚠️ 财务数据为空（可能正常）")
except Exception as e:
    print(f"⚠️ 财务数据获取失败: {e}（港股可能不支持）")

print("\n" + "=" * 80)
print("=== 数据源测试完成 ===")
print("=" * 80)
