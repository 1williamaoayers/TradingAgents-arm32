#!/usr/bin/env python3
"""
独立测试多源新闻适配器
不依赖FastAPI上下文，直接测试各个适配器
"""
import sys
import asyncio
sys.path.insert(0, '/app')

async def test_akshare_adapter():
    """测试AKShare适配器"""
    print("\n" + "=" * 60)
    print("🧪 测试 AKShare 适配器")
    print("=" * 60)
    
    try:
        from app.worker.news_adapters.akshare_adapter import AKShareAdapter
        
        adapter = AKShareAdapter()
        await adapter.initialize()
        
        # 测试获取新闻
        symbol = "09618"
        news_list = await adapter.get_news(symbol, limit=5)
        
        print(f"✅ AKShare适配器工作正常")
        print(f"📰 获取到 {len(news_list)} 条新闻")
        
        if news_list:
            print(f"\n示例新闻:")
            for i, news in enumerate(news_list[:2], 1):
                print(f"  {i}. {news.get('title', 'N/A')}")
                print(f"     来源: {news.get('source', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ AKShare适配器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_alpha_vantage_adapter():
    """测试Alpha Vantage适配器"""
    print("\n" + "=" * 60)
    print("🧪 测试 Alpha Vantage 适配器")
    print("=" * 60)
    
    try:
        from app.worker.news_adapters.alpha_vantage_adapter import AlphaVantageAdapter
        import os
        
        adapter = AlphaVantageAdapter()
        
        if not adapter.api_key:
            print("⚠️ Alpha Vantage API Key未配置，跳过测试")
            return None
        
        # 测试获取新闻
        symbol = "09618"
        news_list = await adapter.get_news(symbol, limit=5)
        
        print(f"✅ Alpha Vantage适配器工作正常")
        print(f"📰 获取到 {len(news_list)} 条新闻")
        
        if news_list:
            print(f"\n示例新闻:")
            for i, news in enumerate(news_list[:2], 1):
                print(f"  {i}. {news.get('title', 'N/A')}")
                print(f"     相关性: {news.get('relevance_score', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Alpha Vantage适配器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_rss_adapter():
    """测试RSS适配器"""
    print("\n" + "=" * 60)
    print("🧪 测试 RSS 适配器")
    print("=" * 60)
    
    try:
        from app.worker.news_adapters.rss_adapter import RSSAdapter
        
        adapter = RSSAdapter()
        
        # 测试获取新闻
        symbol = "09618.HK"
        news_list = await adapter.get_news(symbol, limit=5)
        
        print(f"✅ RSS适配器工作正常")
        print(f"📰 获取到 {len(news_list)} 条新闻")
        
        if news_list:
            print(f"\n示例新闻:")
            for i, news in enumerate(news_list[:2], 1):
                print(f"  {i}. {news.get('title', 'N/A')}")
                print(f"     来源: {news.get('source', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ RSS适配器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("=" * 60)
    print("🚀 多源新闻适配器独立测试")
    print("=" * 60)
    
    results = {}
    
    # 测试各个适配器
    results['akshare'] = await test_akshare_adapter()
    results['alpha_vantage'] = await test_alpha_vantage_adapter()
    results['rss'] = await test_rss_adapter()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    
    for adapter, result in results.items():
        if result is True:
            status = "✅ 通过"
        elif result is False:
            status = "❌ 失败"
        else:
            status = "⚠️ 跳过"
        print(f"  {adapter:20} {status}")
    
    # 统计
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    
    print(f"\n总计: {passed} 通过, {failed} 失败, {skipped} 跳过")
    
    if failed == 0:
        print("\n🎉 所有测试通过！多源新闻服务可以使用！")
    else:
        print(f"\n⚠️ 有 {failed} 个适配器测试失败，请检查配置")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
