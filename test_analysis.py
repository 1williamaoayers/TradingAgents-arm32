#!/usr/bin/env python3
"""
测试分析功能脚本
"""
import sys
import os
import time
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '/app')

from pymongo import MongoClient

def test_analysis():
    """测试分析功能"""
    print("=" * 60)
    print("🧪 开始测试分析功能")
    print("=" * 60)
    
    # 1. 检查LLM配置
    print("\n1️⃣ 检查LLM配置...")
    client = MongoClient('mongodb://admin:tradingagents123@mongodb:27017/?authSource=admin')
    db = client['tradingagents']
    
    llm_config = db.system_config.find_one({'config_type': 'llm'})
    if llm_config and 'llm_configs' in llm_config:
        print(f"   ✅ LLM配置已找到: {len(llm_config['llm_configs'])} 个模型")
        for llm in llm_config['llm_configs']:
            print(f"      - {llm.get('provider')}: {llm.get('model_name')} (enabled: {llm.get('enabled')})")
    else:
        print("   ❌ LLM配置未找到")
        return False
    
    # 2. 创建测试分析任务
    print("\n2️⃣ 创建测试分析任务...")
    test_task = {
        "symbol": "01810",
        "symbol_name": "小米集团-W",
        "market": "hk",
        "analyst_types": ["market_analyst", "news_analyst"],
        "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        "status": "pending",
        "created_at": datetime.now()
    }
    
    # 清理旧的测试报告
    db.analysis_reports.delete_many({"symbol": "01810", "created_at": {"$gte": datetime.now().replace(hour=0, minute=0, second=0)}})
    print("   ✅ 已清理旧的测试报告")
    
    # 插入测试任务
    result = db.analysis_queue.insert_one(test_task)
    print(f"   ✅ 测试任务已创建: {result.inserted_id}")
    
    # 3. 等待分析完成（简化版，实际应该由后台worker处理）
    print("\n3️⃣ 等待分析完成...")
    print("   ⚠️ 注意：此脚本只创建任务，实际分析由后台worker执行")
    print("   💡 请在前端查看分析结果，或等待60秒后检查数据库")
    
    # 4. 检查现有报告
    print("\n4️⃣ 检查现有分析报告...")
    reports = list(db.analysis_reports.find(
        {"symbol": "01810"},
        {"_id": 0, "analyst_type": 1, "created_at": 1, "content": 1}
    ).sort("created_at", -1).limit(5))
    
    if reports:
        print(f"   ✅ 找到 {len(reports)} 个报告:")
        for i, report in enumerate(reports, 1):
            analyst_type = report.get('analyst_type', 'unknown')
            content = report.get('content', '')
            content_len = len(content)
            content_preview = content[:80] if content else '(无内容)'
            
            print(f"\n   报告 {i}:")
            print(f"      分析师: {analyst_type}")
            print(f"      时间: {report.get('created_at')}")
            print(f"      内容长度: {content_len} 字符")
            print(f"      内容预览: {content_preview}...")
            
            # 检查内容质量
            if content_len < 10:
                print(f"      ⚠️ 警告: 内容过短，可能无效")
            elif "我好" in content or content_len < 50:
                print(f"      ❌ 错误: 内容无效")
            else:
                print(f"      ✅ 内容看起来正常")
    else:
        print("   ⚠️ 未找到分析报告")
    
    client.close()
    
    print("\n" + "=" * 60)
    print("🎯 测试完成")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_analysis()
