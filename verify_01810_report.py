#!/usr/bin/env python3
"""
修正後的 01810 测试 - 适应宿主机环境
"""
import sys
import os
from pathlib import Path

# 获取当前脚本所在目录
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

# 修改工作目录到 TradingAgents-arm32
os.chdir(str(current_dir))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv('.env')

print("="*70)
print("01810.HK 治理后成果验证分析")
print("="*70)

from app.services.simple_analysis_service import create_analysis_config
from tradingagents.graph.trading_graph import TradingAgentsGraph

# 创建配置
config = create_analysis_config(
    research_depth=1,  # 快速分析
    selected_analysts=['news', 'sentiment'], # 重点测试新闻和情绪分析师
    quick_model='deepseek-chat',
    deep_model='deepseek-chat',
    llm_provider='openai', # 使用 OpenAI SDK 调用 DeepSeek
    market_type='港股'
)

# 注入我们的 DeepSeek 配置
config['llm_config']['openai'] = {
    'api_key': os.getenv('DEEPSEEK_API_KEY'),
    'base_url': os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com'),
    'model': 'deepseek-chat'
}

print(f"\n配置创建完成:")
print(f"  分析师: {config['selected_analysts']}")
print(f"  模型: deepseek-chat")

# 创建图
print("\n创建TradingAgentsGraph...")
graph = TradingAgentsGraph(
    selected_analysts=config['selected_analysts'],
    debug=True,
    config=config
)

# 运行分析
print("\n开始全链路分析 01810.HK (已启用 AI 联想和智能降噪)...")
from datetime import datetime
propagation_result = graph.propagate('01810.HK', datetime.now().strftime('%Y-%m-%d'))

if isinstance(propagation_result, tuple):
    final_state = propagation_result[0]
else:
    final_state = propagation_result

# 打印新闻分析预览
print("\n" + "="*70)
print("新闻分析师输出预览 (治理后):")
print("="*70)
print(final_state.get('news_report', '❌ 未生成新闻报告'))

print("\n測試完成，您可以直接對比這份報告與之前的空洞報告。")
