#!/usr/bin/env python3
"""
港股09618完整分析测试脚本 - 简化版
直接通过Web API提交分析请求并监控结果
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
print("🧪 港股09618完整分析测试")
print("=" * 80)
print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"股票代码: 09618 (京东集团-SW)")
print(f"市场类型: 港股")
print("=" * 80)

# 测试配置
TEST_CONFIG = {
    'stock_symbol': '09618',
    'market_type': '港股',
    'analysis_date': str(date.today()),
    'analysts': ['market', 'news', 'fundamentals'],  # 先测试3个核心分析师
    'research_depth': 2,  # 使用基础分析加快速度
    'llm_provider': 'deepseek',
    'llm_model': 'deepseek-chat'
}

print(f"\n📋 测试配置:")
print(f"  分析师: {', '.join(TEST_CONFIG['analysts'])}")
print(f"  研究深度: {TEST_CONFIG['research_depth']} (基础分析)")
print(f"  LLM: {TEST_CONFIG['llm_provider']} / {TEST_CONFIG['llm_model']}")

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
        for key, value in state.items():
            if value and ('report' in key or 'assessment' in key or 'plan' in key or 'decision' in key or 'state' in key):
                report_count += 1
                if isinstance(value, str):
                    print(f"  {report_count}. {key}: {len(value)}字符")
                elif isinstance(value, dict):
                    print(f"  {report_count}. {key}: {len(value)}个字段")
        
        print(f"\n🎯 总计: {report_count}个报告")
        
        # 保存结果
        result_file = f"test_result_09618_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            # 只保存关键信息，避免文件过大
            summary = {
                'test_time': datetime.now().isoformat(),
                'duration': duration,
                'success': results.get('success'),
                'stock_symbol': results.get('stock_symbol'),
                'report_count': report_count,
                'reports': list(state.keys()) if state else []
            }
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 结果已保存: {result_file}")
        print("\n✅ 测试成功完成！")
        
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
