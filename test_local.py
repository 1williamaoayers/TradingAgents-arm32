import sys
sys.path.insert(0, '.')

from web.utils.analysis_runner import run_stock_analysis

print("🚀 本地测试分析功能...\n")

results = run_stock_analysis(
    stock_symbol='09618.HK',
    analysis_date='2024-12-10',
    analysts=['market'],
    research_depth=1,
    llm_provider='deepseek',
    llm_model='deepseek-chat',
    market_type='港股'
)

state = results.get('state', {})
debate = state.get('investment_debate_state', {})

print(f"\n{'='*60}")
print(f"本地测试结果:")
print(f"成功: {results.get('success')}")
print(f"bull_history: {len(str(debate.get('bull_history', '')))} 字符")
print(f"bear_history: {len(str(debate.get('bear_history', '')))} 字符")
print(f"{'='*60}")

if len(str(debate.get('bull_history', ''))) > 0:
    print("\n✅ 测试通过！可以推送")
else:
    print("\n❌ 测试失败！不要推送")
