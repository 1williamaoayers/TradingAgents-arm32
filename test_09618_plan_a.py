#!/usr/bin/env python3
"""
港股09618测试 - 方案A（零风险）
只测试3个已验证成功的分析师
"""

import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime, date

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("🧪 港股09618测试 - 方案A（零风险）")
print("=" * 80)
print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"股票代码: 09618 (京东集团-SW)")
print(f"市场类型: 港股")
print(f"测试方案: 只测试3个已验证成功的分析师")
print("=" * 80)

# 测试配置 - 只包含已验证成功的3个分析师
TEST_CONFIG = {
    'stock_symbol': '09618',
    'market_type': '港股',
    'analysis_date': str(date.today()),
    'analysts': ['market', 'news', 'fundamentals'],  # 只测试3个
    'research_depth': 2,  # 基础分析
    'llm_provider': 'deepseek',
    'llm_model': 'deepseek-chat'
}

print(f"\n📋 测试配置:")
print(f"  分析师: {', '.join(TEST_CONFIG['analysts'])} (3个)")
print(f"  研究深度: {TEST_CONFIG['research_depth']} (基础分析)")
print(f"  LLM: {TEST_CONFIG['llm_provider']} / {TEST_CONFIG['llm_model']}")
print(f"  预期报告: 9/10个")
print(f"  风险等级: 零风险（已验证成功）")

# 导入分析运行器
try:
    from web.utils.analysis_runner import run_stock_analysis
    print("\n✅ 分析运行器导入成功")
except Exception as e:
    print(f"\n❌ 导入失败: {e}")
    sys.exit(1)

# 进度回调
def progress_callback(message, step=None, total_steps=None):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

# 执行分析
print("\n" + "=" * 80)
print("📊 开始执行分析...")
print("=" * 80)

start_time = time.time()

try:
    results = run_stock_analysis(
        stock_symbol=TEST_CONFIG['stock_symbol'],
        analysis_date=TEST_CONFIG['analysis_date'],
        analysts=TEST_CONFIG['analysts'],
        research_depth=TEST_CONFIG['research_depth'],
        llm_provider=TEST_CONFIG['llm_provider'],
        llm_model=TEST_CONFIG['llm_model'],
        market_type=TEST_CONFIG['market_type'],
        progress_callback=progress_callback
    )
    
    duration = time.time() - start_time
    
    print("\n" + "=" * 80)
    print("📊 分析结果")
    print("=" * 80)
    print(f"⏱️ 耗时: {duration:.2f}秒 ({duration/60:.2f}分钟)")
    print(f"✅ 成功: {results.get('success', False)}")
    
    if results.get('success'):
        state = results.get('state', {})
        print(f"\n📋 生成的报告:")
        report_count = 0
        
        # 预期的9个报告（不包括sentiment_report）
        expected_reports = [
            'market_report',
            'fundamentals_report',
            'news_report',
            'risk_assessment',
            'investment_plan',
            'investment_debate_state',
            'trader_investment_plan',
            'risk_debate_state',
            'final_trade_decision'
        ]
        
        for report_name in expected_reports:
            if report_name in state and state[report_name]:
                report_count += 1
                value = state[report_name]
                if isinstance(value, str):
                    status = "✅" if len(value) > 100 else "⚠️"
                    print(f"  {report_count}. {report_name}: {len(value)}字符 {status}")
                elif isinstance(value, dict):
                    status = "✅" if len(value) > 0 else "⚠️"
                    print(f"  {report_count}. {report_name}: {len(value)}个字段 {status}")
            else:
                print(f"  ❌ {report_name}: 未生成")
        
        print(f"\n🎯 总计: {report_count}/9个报告")
        print(f"📊 成功率: {report_count/9*100:.1f}%")
        
        # 保存结果
        result_file = f"test_result_09618_plan_a_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            summary = {
                'test_time': datetime.now().isoformat(),
                'test_plan': 'Plan A - 3 Analysts Only',
                'duration': duration,
                'success': results.get('success'),
                'stock_symbol': results.get('stock_symbol'),
                'report_count': report_count,
                'expected_count': 9,
                'success_rate': f"{report_count/9*100:.1f}%",
                'reports': list(state.keys()) if state else []
            }
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 结果已保存: {result_file}")
        
        if report_count == 9:
            print("\n🎉 测试完全成功！生成了全部9个预期报告！")
        elif report_count >= 8:
            print(f"\n✅ 测试基本成功！生成了{report_count}/9个报告")
        else:
            print(f"\n⚠️ 测试部分成功，生成了{report_count}/9个报告")
        
    else:
        print(f"\n❌ 分析失败: {results.get('error', '未知错误')}")
        sys.exit(1)
        
except Exception as e:
    duration = time.time() - start_time
    print(f"\n❌ 测试异常: {e}")
    print(f"⏱️ 失败前耗时: {duration:.2f}秒")
    import traceback
    traceback.print_exc()
    sys.exit(1)
