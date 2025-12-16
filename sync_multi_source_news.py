#!/usr/bin/env python3
"""
多源新闻同步独立脚本 - 完整版
支持AKShare、Alpha Vantage、FinnHub、RSS四个新闻源
"""
import sys
import asyncio
import logging
from datetime import datetime
from pymongo import MongoClient
sys.path.insert(0, '/app')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """主函数"""
    try:
        logger.info("=" * 60)
        logger.info("🔄 开始多源新闻同步（完整版）")
        logger.info("=" * 60)
        
        # 直接连接MongoDB
        mongo_uri = "mongodb://admin:tradingagents123@mongodb:27017/"
        client = MongoClient(mongo_uri)
        db = client.tradingagents
        logger.info("✅ MongoDB已连接")
        
        # 获取自选股列表
        watchlist = set()
        for doc in db.user_favorites.find({}):
            for fav in doc.get("favorites", []):
                code = fav.get("stock_code")
                if code:
                    watchlist.add(code)
        
        logger.info(f"📌 自选股数量: {len(watchlist)}")
        logger.info(f"   股票列表: {', '.join(watchlist)}")
        
        # 导入所有适配器
        from app.worker.news_adapters.akshare_adapter import AKShareAdapter
        from app.worker.news_adapters.alpha_vantage_adapter import AlphaVantageAdapter
        from app.worker.news_adapters.finnhub_adapter import FinnHubAdapter
        from app.worker.news_adapters.rss_adapter import RSSAdapter
        
        # 初始化适配器
        akshare = AKShareAdapter()
        await akshare.initialize()
        alpha_vantage = AlphaVantageAdapter()
        finnhub = FinnHubAdapter()
        rss = RSSAdapter()
        
        logger.info("✅ 所有适配器已初始化")
        
        # 同步新闻
        total_news = 0
        source_stats = {}
        rss_synced = False  # RSS只同步一次
        
        for symbol in watchlist:
            logger.info(f"🔄 同步 {symbol}...")
            
            # AKShare（港股）
            if '.HK' in symbol:
                try:
                    news_list = await akshare.get_news(symbol, limit=10)
                    if news_list:
                        for news in news_list:
                            db.stock_news.update_one(
                                {"title": news["title"], "symbol": symbol},
                                {"$set": news},
                                upsert=True
                            )
                            source = news.get("source", "unknown")
                            source_stats[source] = source_stats.get(source, 0) + 1
                        total_news += len(news_list)
                        logger.info(f"  ✅ AKShare: {len(news_list)}条")
                except Exception as e:
                    logger.error(f"  ❌ AKShare失败: {str(e)[:50]}")
            
            # Alpha Vantage（美股代码）
            us_symbol = symbol.replace('.HK', '').replace('0', '', 1) if '.HK' in symbol else symbol
            try:
                news_list = await alpha_vantage.get_news(us_symbol, limit=5)
                if news_list:
                    for news in news_list:
                        db.stock_news.update_one(
                            {"title": news["title"], "symbol": symbol},
                            {"$set": news},
                            upsert=True
                        )
                        source = news.get("source", "unknown")
                        source_stats[source] = source_stats.get(source, 0) + 1
                    total_news += len(news_list)
                    logger.info(f"  ✅ Alpha Vantage: {len(news_list)}条")
            except Exception as e:
                logger.debug(f"  Alpha Vantage: 0条")
            
            # FinnHub（美股代码）
            try:
                news_list = await finnhub.get_news(us_symbol, limit=5)
                if news_list:
                    for news in news_list:
                        db.stock_news.update_one(
                            {"title": news["title"], "symbol": symbol},
                            {"$set": news},
                            upsert=True
                        )
                        source = news.get("source", "unknown")
                        source_stats[source] = source_stats.get(source, 0) + 1
                    total_news += len(news_list)
                    logger.info(f"  ✅ FinnHub: {len(news_list)}条")
            except Exception as e:
                logger.debug(f"  FinnHub: 0条")
            
            # RSS（通用财经新闻，只同步一次）
            if not rss_synced:
                try:
                    news_list = await rss.get_news("GENERAL", limit=100)  # 使用通用标识
                    if news_list:
                        for news in news_list:
                            # RSS新闻不绑定特定股票，使用通用symbol
                            news["symbol"] = "GENERAL"
                            db.stock_news.update_one(
                                {"title": news["title"]},  # 只按标题去重
                                {"$set": news},
                                upsert=True
                            )
                            source = news.get("source", "unknown")
                            source_stats[source] = source_stats.get(source, 0) + 1
                        total_news += len(news_list)
                        logger.info(f"  ✅ RSS: {len(news_list)}条（通用财经新闻）")
                        rss_synced = True
                except Exception as e:
                    logger.error(f"  ❌ RSS失败: {str(e)[:50]}")
                    rss_synced = True  # 即使失败也标记为已同步，避免重试
        
        # 输出结果
        logger.info("=" * 60)
        logger.info("✅ 多源新闻同步完成")
        logger.info(f"  新闻总数: {total_news} 条")
        logger.info("  各源统计:")
        for source, count in sorted(source_stats.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"    - {source}: {count} 条")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ 同步失败: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
