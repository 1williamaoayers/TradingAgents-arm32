#!/usr/bin/env python3
"""
测试02128.HK（中国联塑）四个分析师 - 验证真实内容生成
验证能否生成全部10份报告，且内容不为空
"""
import sys
import os
import json
import logging
import sys
import os
import json
import logging

try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

sys.path.insert(0, '/trae/TradingAgents-arm32')
os.chdir('/trae/TradingAgents-arm32')

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

import argparse

# 解析命令行参数
parser = argparse.ArgumentParser(description='Run trading analysis with specific provider')
parser.add_argument('--provider', type=str, default='google', choices=['google', 'deepseek', 'alibaba', 'dashscope'],
                    help='LLM Provider (google, deepseek, alibaba/dashscope)')
parser.add_argument('--check-only', action='store_true', help='Only check reports from existing log file, do not run graph')
args = parser.parse_args()

print("\n" + "="*70)
print(f"测试 02128.HK (中国联塑) - 四个分析师 [真实内容验证]")
print(f"Provider: {args.provider}")
print("="*70)

# 配置
config = DEFAULT_CONFIG.copy()
config['selected_analysts'] = ['market', 'fundamentals', 'news', 'sentiment']
config['debug'] = True

# 适配用户环境配置
if args.provider == 'google':
    config["llm_provider"] = "google"
    config["backend_url"] = "https://generativelanguage.googleapis.com/v1beta"
    config["deep_think_llm"] = "gemini-2.0-flash"
    config["quick_think_llm"] = "gemini-2.0-flash"
elif args.provider == 'deepseek':
    config["llm_provider"] = "deepseek"
    config["backend_url"] = "https://api.deepseek.com/v1"
    config["deep_think_llm"] = "deepseek-chat"
    config["quick_think_llm"] = "deepseek-chat"
elif args.provider in ['alibaba', 'dashscope']:
    config["llm_provider"] = "dashscope" # 或 alibaba，需看内部实现
    # DashScope通常不需要backend_url，或者使用 SDK
    config["deep_think_llm"] = "qwen-plus" # 或 qwen-max
    config["quick_think_llm"] = "qwen-turbo"

config["online_tools"] = True # 启用在线搜索以获取真实信息

# 创建图
print("初始化 TradingAgentsGraph...")
graph = TradingAgentsGraph(
    selected_analysts=config['selected_analysts'],
    debug=config['debug'],
    config=config
)

# 运行分析
print("\n开始执行分析工作流 (这可能需要几分钟)...")
try:
    # 尝试使用 propagate 或者是 run_workflow (根据 main.py 使用 propagate)
    # 但 propagate 需要 ticker 和 start_date
    # 检查 main.py 发现: _, decision = ta.propagate("NVDA", "2024-05-10")
    # 我们这里只给 Ticker, 所以可能需要默认日期
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    
    if args.check_only:
        print("⚠️ Skipping graph execution, checking existing logs only.")
        final_state = {}
        result = {'state': final_state}
    else:
        # 3. 运行分析
        print("\n🚀 开始执行多智能体分析 (02128.HK)...")
        try:
            final_state = graph.propagate('02128.HK', today)
            result = {'state': final_state, 'decision': final_state.get('final_trade_decision')}
            print("✅ 分析执行完成")
        except AttributeError:
            result = graph.run('02128.HK')
            print("✅ 分析执行完成 (legacy run)")
    
except Exception as e:
    print(f"❌ 运行失败: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("分析完成 - 结果验证")
print("="*70)
print(f"执行状态: {result.get('status', 'unknown')}")

if result.get('status') == 'failed':
    print(f"❌ 分析流程报错: {result.get('error_message', 'No error message')}")

# 获取状态字典
state = result.get('state', {})
final_decision = result.get('decision', {}) or result.get('final_decision', {}) # 兼容不同字段名

# 尝试读取完整日志文件，因为 propagate 返回的 state 可能不包含中间步骤
try:
    log_file = f"eval_results/02128.HK/TradingAgentsStrategy_logs/full_states_log.json"
    if os.path.exists(log_file):
        print(f"读取完整日志文件: {log_file}")
        with open(log_file, 'r') as f:
            logs = json.load(f)
            # 取最后一个日期的日志
            if logs:
                last_date = sorted(logs.keys())[-1]
                state = logs[last_date]
                print(f"已加载日期 {last_date} 的完整状态")
except Exception as e:
    print(f"⚠️ 读取日志文件失败: {e}")


# 需要检查的关键报告/模块
required_reports = [
    'market_report', 
    'fundamentals_report', 
    'news_report', 
    'sentiment_report',
    'bull_researcher',
    'bear_researcher',
    'research_team_decision',
    'risky_analyst',
    'safe_analyst',
    'neutral_analyst',
    'risk_management_decision',
    'trader_investment_plan',
    'final_trade_decision'
]

print(f"\n检查 {len(required_reports)} 个核心报告的内容质量:")
print("-" * 50)

valid_count = 0
for key in required_reports:
    # 从 state 中查找报告
    content = state.get(key)
    if not content and 'reports' in state:
        content = state['reports'].get(key)
    
    # 从 investment_debate_state 中提取
    if not content and 'investment_debate_state' in state:
        debate = state['investment_debate_state']
        if key == 'bull_researcher':
            content = debate.get('bull_history', '')
        elif key == 'bear_researcher':
            content = debate.get('bear_history', '')
        elif key == 'research_team_decision':
            content = debate.get('judge_decision', '')
            
    # 从 risk_debate_state 中提取
    if not content and 'risk_debate_state' in state:
        risk_debate = state['risk_debate_state']
        if key == 'risk_management_decision':
            content = risk_debate.get('judge_decision', '')
        elif key == 'risky_analyst':
            content = risk_debate.get('risky_history', '')
        elif key == 'safe_analyst':
            content = risk_debate.get('safe_history', '')
        elif key == 'neutral_analyst':
            content = risk_debate.get('neutral_history', '')
            
    # 映射 trader_investment_plan
    if key == 'trader_investment_plan' and not content:
        content = state.get('trader_investment_decision') or state.get('investment_plan')

    # 特殊处理 final_trade_decision
    if key == 'final_trade_decision' and not content:
        content = final_decision


    status_icon = "❌"
    length_info = "0 字符"
    preview = ""

    if content:
        if isinstance(content, str):
            length = len(content)
            if length > 200: # 认为大于200字符才算"实质内容"
                status_icon = "✅"
                valid_count += 1
            length_info = f"{length} 字符"
            preview = content[:50].replace('\n', ' ') + "..."
        elif isinstance(content, dict):
            # 对于字典类型的报告（如决策结构体），检查是否有 action 或 reasoning
            if content.get('action') or content.get('reasoning') or content.get('judge_decision'):
                status_icon = "✅"
                valid_count += 1
                length_info = f"{len(str(content))} 字符 (JSON)"
                preview = str(content)[:50].replace('\n', ' ') + "..."
    
    print(f"{status_icon} {key:<25} | {length_info:<15} | {preview}")

print("-" * 50)
print(f"有效报告数量: {valid_count} / {len(required_reports)}")

if valid_count < len(required_reports):
    print("\n⚠️ 警告: 部分报告缺失或内容过短，请检查日志。")
else:
    print("\n✅ 验证通过: 所有分析报告均已生成且包含实质内容。")

# 保存结果到文件以便进一步检查
output_file = 'result_02128_verification.json'
with open(output_file, 'w', encoding='utf-8') as f:
    # 处理不可序列化的对象
    safe_result = {k: v for k, v in result.items() if k != 'graph'}
    json.dump(safe_result, f, indent=2, ensure_ascii=False, default=str)
print(f"\n完整结果已保存至: {output_file}")
