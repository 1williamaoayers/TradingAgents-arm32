import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# 添加项目路径
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

# 加载环境变量
env_path = current_dir / '.env'
load_dotenv(dotenv_path=env_path)

from tradingagents.tools.unified_news_tool import UnifiedNewsAnalyzer

class RealToolkit:
    """提供给 Analyzer 的工具包占位"""
    def __init__(self):
        # 如果需要某些子工具，这里可以构造
        pass

async def test():
    analyzer = UnifiedNewsAnalyzer(RealToolkit())
    ticker = '01810' # 小米集团
    print(f"Testing REAL Serper search for {ticker}...")
    
    # 确保 API KEY 存在
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        print("❌ SERPER_API_KEY still not found in environment!")
        return

    res = analyzer.get_stock_sentiment_unified(ticker, '2026-01-12')
    
    print("\n--- Result ---")
    print(f"Status: {res.get('status')}")
    print(f"Source: {res.get('source')}")
    
    content = res.get('content', '')
    if content:
        print("\n--- Content Preview (1000 chars) ---")
        print(content[:1000])
    else:
        print("\n--- No Content Returned ---")
        print(f"Summary: {res.get('summary')}")

if __name__ == "__main__":
    asyncio.run(test())

