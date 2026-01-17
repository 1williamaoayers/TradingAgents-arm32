
import os
import sys
import asyncio
from pathlib import Path

# 添加项目路径
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

from tradingagents.tools.unified_news_tool import UnifiedNewsAnalyzer

class MockToolkit:
    def __init__(self):
        pass

async def test():
    analyzer = UnifiedNewsAnalyzer(MockToolkit())
    print("Testing get_stock_news_unified for 01810...")
    res = analyzer.get_stock_news_unified('01810', max_news=5)
    print("\n--- Status ---")
    print(res.get('status'))
    print("\n--- Content Preview ---")
    print(res.get('content')[:1000])

if __name__ == "__main__":
    asyncio.run(test())
