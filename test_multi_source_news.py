#!/usr/bin/env python3
"""
测试多源新闻聚合服务
验证所有适配器是否正常工作
"""
import sys
import asyncio
sys.path.insert(0, '/app')

from app.worker.multi_source_news_service import get_multi_source_news_service

async def test_multi_source_news():
    """测试多源新闻服务"""
    print("=" * 60)
    print("🧪 测试多源新闻聚合服务")
    print("=" * 60)
    
    # 初始化服务
    service = await get_multi_source_news_service()
    
    # 测试股票
    test_symbols = ["09618.HK", "00700.HK"]
    
    print(f"\n📊 测试股票: {', '.join(test_symbols)}")
    print(f"📰 已加载新闻源: {len(service.adapters)} 个")
    
    for adapter in service.adapters:
        stats = adapter.get_stats()
        print(f"  - {stats['source_name']}: {'✅ 可用' if stats['is_available'] else '❌ 不可用'}")
    
    # 同步新闻
    print("\n🔄 开始同步新闻...")
    stats = await service.sync_news_data(
        symbols=test_symbols,
        max_news_per_stock=10,
        favorites_only=False
    )
    
    # 输出结果
    print("\n📊 同步结果:")
    print(f"  总处理: {stats['total_processed']} 只股票")
    print(f"  成功: {stats['success_count']} 只")
    print(f"  新闻总数: {stats['news_count']} 条")
    print(f"  耗时: {stats.get('duration', 0):.2f} 秒")
    
    print("\n📰 各源新闻数量:")
    for source, count in stats.get('source_stats', {}).items():
        print(f"  - {source}: {count} 条")
    
    if stats.get('errors'):
        print("\n❌ 错误:")
        for error in stats['errors'][:5]:
            print(f"  - {error}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_multi_source_news())
