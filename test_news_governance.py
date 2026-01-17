import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from app.worker.news_utils.keyword_generator import get_keyword_generator
from tradingagents.dataflows.providers.china.akshare import get_akshare_provider

async def test_governance():
    symbol = "01810"
    print(f"🚀 测试股票: {symbol} (小米集团)")
    
    # 1. 测试关键词生成
    kw_gen = get_keyword_generator()
    keywords = await kw_gen.generate_keywords(symbol, "小米集团")
    print(f"✨ AI 生成关键词: {keywords}")
    
    # 2. 测试 Provider 的市场识别与补位
    provider = get_akshare_provider()
    # 模拟内部逻辑
    from tradingagents.utils.stock_utils import StockUtils
    market_info = StockUtils.get_market_info(symbol)
    target_symbol = symbol.zfill(5) if market_info['is_hk'] else symbol.zfill(6)
    print(f"🔍 市场识别: {'港股' if market_info['is_hk'] else '非港股'}")
    print(f"📌 最终补位代码: {target_symbol}")
    
    if target_symbol != "01810":
        print(f"❌ 补位错误! 期望 01810, 得到 {target_symbol}")
    else:
        print(f"✅ 补位正确!")

    # 3. 测试搜索获取 (Docker 环境下会调用 _get_stock_news_direct)
    search_query = " ".join(keywords)
    print(f"📡 正在尝试抓取新闻，搜索词: {search_query}")
    
    # 注意：在非 Docker 环境下可能返回空，但我们要看是否有 001810 的噪声
    news = await provider.get_stock_news(symbol, limit=5, query=search_query)
    
    if news:
        print(f"📊 抓取到 {len(news)} 条新闻:")
        for i, n in enumerate(news):
            title = n.get('title', '')
            print(f"   [{i+1}] {title[:60]}")
            if "基金" in title or "001810" in title:
                print("   ⚠️ 警告: 发现疑似基金噪声!")
    else:
        print("⚠️ 未抓取到新闻 (可能是 stock_news_em 接口问题或非 Docker 环境)")

if __name__ == "__main__":
    asyncio.run(test_governance())
