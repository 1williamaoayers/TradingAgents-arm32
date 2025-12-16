
import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Setup paths
if Path('/app').exists():
    BASE_DIR = Path('/app')
else:
    BASE_DIR = Path('/trae/TradingAgents-arm32')
sys.path.append(str(BASE_DIR))

# 初始化日志
from tradingagents.utils.logging_init import init_logging
init_logging()

import logging
logger = logging.getLogger("test_01810_sentiment")

from tradingagents.graph.trading_graph import TradingAgentsGraph

def test_sentiment_only():
    print("======================================================================")
    print("01810.HK 社交媒体(Sentiment)分析独立测试")
    print("======================================================================")
    
    # 1. 配置参数
    ticker = "01810.HK"
    analyze_date = datetime.now().strftime('%Y-%m-%d')
    company_name = "Xiaomi" # 或 "小米集团"
    
    # 2. 初始化图，仅启用 'sentiment' 分析师
    selected_analysts = ["sentiment"]
    
    try:
        # 使用默认配置作为基础
        from tradingagents.default_config import DEFAULT_CONFIG
        config = DEFAULT_CONFIG.copy()
        
        # 更新特定参数
        config.update({
            "ticker": ticker,
            "company_name": company_name,
            "llm_provider": "dashscope/qwen-turbo", # 确保provider正确
            "quick_think_llm": "qwen-turbo",  # 修正：Dashscope不支持gpt-4o-mini
            "deep_think_llm": "qwen-plus",    # 修正：Dashscope不支持o4-mini
            "selected_analysts": selected_analysts,
            "project_dir": str(BASE_DIR),
            "api_key": os.getenv("DASHSCOPE_API_KEY") 
        })
        
        print(f"初始化 TradingAgentsGraph, Config keys: {list(config.keys())}")
            
        graph = TradingAgentsGraph(
            selected_analysts=selected_analysts,
            config=config,
            debug=True
        )
            
        print(f"开始分析 {ticker}...")
        
        # 3. 运行分析
        # propagate 方法返回 (final_state, signal)
        result = graph.propagate(ticker, analyze_date)
        
        # 4. 验证结果
        # 注意：propagate返回的是tuple (final_state, signal)
        if isinstance(result, tuple):
            final_state = result[0]
        else:
            final_state = result.get("state", {})
            
        sentiment_report = final_state.get("sentiment_report", "")
        
        print("\n================ 测试结果 ================")
        if sentiment_report and len(sentiment_report) > 100:
            print("✅ 社交媒体(Sentiment)分析成功生成报告")
            print(f"报告长度: {len(sentiment_report)} 字符")
            print("报告预览 (前500字符):")
            print("-" * 40)
            print(sentiment_report[:500])
            print("-" * 40)
            
            # 手动保存一份以供检查（如果需要）
            report_path = BASE_DIR / "sentiment_test_01810.md"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(sentiment_report)
            print(f"完整报告已保存至: {report_path}")
            
        else:
            print("❌ 社交媒体(Sentiment)分析未生成有效报告")
            print(f"报告内容: {sentiment_report}")
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sentiment_only()
