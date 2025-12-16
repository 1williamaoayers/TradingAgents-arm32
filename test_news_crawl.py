#!/usr/bin/env python3
"""
新闻抓取测试脚本
手动触发针对指定股票的新闻抓取，用于测试爬虫功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.worker.akshare_sync_service import get_akshare_sync_service
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('news_test')


async def test_news_crawl(stock_code: str = "00700.HK", max_news: int = 10):
    """
    测试新闻抓取功能
    
    Args:
        stock_code: 股票代码
        max_news: 最大新闻数量
    """
    logger.info(f"🚀 开始测试新闻抓取: {stock_code}")
    logger.info(f"📊 最大新闻数量: {max_news}")
    logger.info("=" * 60)
    
    try:
        # 获取同步服务
        service = await get_akshare_sync_service()
        logger.info("✅ AKShare 同步服务初始化成功")
        
        # 测试抓取指定股票的新闻
        logger.info(f"\n🔍 开始抓取 {stock_code} 的新闻...")
        result = await service.sync_news_data(
            symbols=[stock_code],
            max_news_per_stock=max_news,
            force_update=True,
            favorites_only=False  # 不限制只抓自选股
        )
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 抓取结果统计:")
        logger.info(f"  - 处理股票数: {result.get('total_processed', 0)}")
        logger.info(f"  - 成功数量: {result.get('success_count', 0)}")
        logger.info(f"  - 错误数量: {result.get('error_count', 0)}")
        logger.info(f"  - 新闻总数: {result.get('news_count', 0)}")
        logger.info(f"  - 耗时: {result.get('duration', 0):.2f} 秒")
        
        if result.get('errors'):
            logger.warning(f"\n⚠️ 错误列表:")
            for error in result['errors']:
                logger.warning(f"  - {error}")
        
        logger.info("\n✅ 测试完成！")
        return result
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return None


async def test_favorites_news_crawl():
    """测试自选股新闻抓取"""
    logger.info("🚀 开始测试自选股新闻抓取")
    logger.info("=" * 60)
    
    try:
        # 获取同步服务
        service = await get_akshare_sync_service()
        logger.info("✅ AKShare 同步服务初始化成功")
        
        # 先获取自选股列表
        logger.info("\n📌 获取自选股列表...")
        favorite_stocks = await service._get_favorite_stocks()
        logger.info(f"✅ 找到 {len(favorite_stocks)} 只自选股:")
        for stock in favorite_stocks:
            logger.info(f"  - {stock}")
        
        if not favorite_stocks:
            logger.warning("⚠️ 没有自选股，无法测试")
            return None
        
        # 抓取自选股新闻
        logger.info(f"\n🔍 开始抓取自选股新闻...")
        result = await service.sync_news_data(
            symbols=None,  # 自动获取自选股
            max_news_per_stock=10,
            force_update=True,
            favorites_only=True  # 只抓自选股
        )
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 抓取结果统计:")
        logger.info(f"  - 处理股票数: {result.get('total_processed', 0)}")
        logger.info(f"  - 成功数量: {result.get('success_count', 0)}")
        logger.info(f"  - 错误数量: {result.get('error_count', 0)}")
        logger.info(f"  - 新闻总数: {result.get('news_count', 0)}")
        logger.info(f"  - 耗时: {result.get('duration', 0):.2f} 秒")
        
        logger.info("\n✅ 测试完成！")
        return result
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="新闻抓取测试工具")
    parser.add_argument("--stock", type=str, default="00700.HK", help="股票代码")
    parser.add_argument("--max-news", type=int, default=10, help="最大新闻数量")
    parser.add_argument("--favorites", action="store_true", help="测试自选股新闻抓取")
    
    args = parser.parse_args()
    
    if args.favorites:
        # 测试自选股新闻抓取
        asyncio.run(test_favorites_news_crawl())
    else:
        # 测试指定股票新闻抓取
        asyncio.run(test_news_crawl(args.stock, args.max_news))
