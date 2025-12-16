#!/usr/bin/env python3
"""
测试01810.HK（小米集团）四个分析师
验证能否生成全部10份报告
"""
import sys
import os
sys.path.insert(0, '/app')
os.chdir('/app')

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

print("="*70)
print("测试01810.HK（小米集团）- 四个分析师")
print("="*70)

# 配置
config = DEFAULT_CONFIG.copy()
config['selected_analysts'] = ['market', 'fundamentals', 'news', 'sentiment']
config['debug'] = False

# 创建图
graph = TradingAgentsGraph(
    selected_analysts=config['selected_analysts'],
    debug=config['debug'],
    config=config
)

# 运行分析
print("\n开始分析...")
result = graph.run('01810.HK')

print("\n="*70)
print("分析完成")
print("="*70)
print(f"状态: {result.get('status', 'unknown')}")

# 检查报告
state = result.get('state', {})
print(f"\n生成的报告模块:")
for key in state.keys():
    if isinstance(state[key], str) and len(state[key]) > 100:
        print(f"  ✅ {key}: {len(state[key])}字符")
    elif isinstance(state[key], dict):
        print(f"  ✅ {key}: {len(state[key])}个字段")

print(f"\n总报告数: {len([k for k in state.keys() if k.endswith('_report') or k.endswith('_plan') or k.endswith('_decision') or k == 'final_trade_decision'])}")
