#!/usr/bin/env python3
"""
完整的01810测试 - 包含配置加载
"""
import sys
import os
sys.path.insert(0, '/app')
os.chdir('/app')

# 加载环境变量
from dotenv import load_dotenv
load_dotenv('/app/.env')

print("="*70)
print("01810.HK完整测试 - 四个分析师")
print("="*70)

# 使用前端相同的配置加载逻辑
from app.services.simple_analysis_service import create_analysis_config
from tradingagents.graph.trading_graph import TradingAgentsGraph

# 创建配置（与前端相同）
config = create_analysis_config(
    research_depth=1,  # 快速分析
    selected_analysts=['market', 'fundamentals', 'news', 'sentiment'],
    quick_model='qwen-turbo',
    deep_model='qwen-plus',
    llm_provider='dashscope',
    market_type='港股'
)

print(f"\n配置创建完成:")
print(f"  分析师: {config['selected_analysts']}")
print(f"  快速模型: {config['quick_think_llm']}")
print(f"  深度模型: {config['deep_think_llm']}")
print(f"  Backend URL: {config['backend_url']}")

# 创建图
print("\n创建TradingAgentsGraph...")
graph = TradingAgentsGraph(
    selected_analysts=config['selected_analysts'],
    debug=config['debug'],
    config=config
)

# 运行分析
print("\n开始分析01810.HK...")
from datetime import datetime
propagation_result = graph.propagate('01810.HK', datetime.now().strftime('%Y-%m-%d'))

# 处理返回值：propagate返回(final_state, signal)
if isinstance(propagation_result, tuple):
    final_state = propagation_result[0]
else:
    final_state = propagation_result

# 封装为report_exporter期望的格式
result = {
    'state': final_state,
    'status': 'success'
}

print("\n="*70)
print("分析完成")
print("="*70)

# 检查结果
state = result.get('state', {})
print(f"\n生成的报告:")
report_count = 0
for key in sorted(state.keys()):
    value = state[key]
    if isinstance(value, str) and len(value) > 100:
        print(f"  ✅ {key}: {len(value):,}字符")
        report_count += 1
    elif isinstance(value, dict) and len(value) > 0:
        print(f"  ✅ {key}: {len(value)}个字段")
        report_count += 1

print(f"\n总报告数: {report_count}")
print(f"状态: {result.get('status', 'unknown')}")

# 保存到文件（模拟前端保存逻辑）
print("\n保存报告到文件系统...")
from web.utils.report_exporter import save_modular_reports_to_results_dir

saved_files = save_modular_reports_to_results_dir(result, '01810')
print(f"✅ 保存了 {len(saved_files)} 个报告文件")

print("\n测试完成！")
