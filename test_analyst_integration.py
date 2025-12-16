#!/usr/bin/env python3
"""
分析师整合测试 - 验证新闻数据是否被分析师使用
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('analyst_test')


async def test_analyst_with_news(stock_code: str = "00700.HK", trade_date: str = "2025-12-14"):
    """
    测试分析师是否使用 MongoDB 中的新闻数据
    
    Args:
        stock_code: 股票代码
        trade_date: 交易日期
    """
    logger.info(f"🚀 开始测试分析师整合: {stock_code}")
    logger.info(f"📊 交易日期: {trade_date}")
    logger.info("=" * 60)
    
    try:
        # 1. 验证数据库中有新闻
        logger.info(f"\n📡 [1/3] 验证数据库中的新闻数据...")
        from pymongo import MongoClient
        
        mongo_uri = "mongodb://admin:tradingagents123@mongodb:27017/?authSource=admin"
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client["tradingagents"]
        
        news_count = db.stock_news.count_documents({"stock_code": stock_code})
        logger.info(f"✅ 数据库中有 {news_count} 条 {stock_code} 的新闻")
        
        if news_count > 0:
            news_list = list(db.stock_news.find({"stock_code": stock_code}).limit(3))
            logger.info(f"\n📰 新闻示例:")
            for i, news in enumerate(news_list, 1):
                logger.info(f"  {i}. {news.get('title', '无标题')}")
        else:
            logger.warning(f"⚠️ 数据库中没有 {stock_code} 的新闻，测试可能无法验证整合")
        
        client.close()
        
        # 2. 配置分析师
        logger.info(f"\n🔧 [2/3] 配置分析师...")
        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = "google"
        config["backend_url"] = "https://generativelanguage.googleapis.com/v1beta"
        config["deep_think_llm"] = "gemini-2.0-flash-exp"
        config["quick_think_llm"] = "gemini-2.0-flash-exp"
        config["max_debate_rounds"] = 1
        config["online_tools"] = True
        
        logger.info(f"✅ 配置完成: {config['llm_provider']} / {config['deep_think_llm']}")
        
        # 3. 运行分析
        logger.info(f"\n🎯 [3/3] 运行分析师对 {stock_code} 进行分析...")
        logger.info(f"⏳ 请耐心等待，分析过程可能需要 1-2 分钟...")
        
        ta = TradingAgentsGraph(debug=True, config=config)
        
        # 运行分析
        _, decision = ta.propagate(stock_code, trade_date)
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 分析结果:")
        logger.info("=" * 60)
        logger.info(decision)
        logger.info("=" * 60)
        
        # 4. 验证新闻是否被引用
        logger.info(f"\n🔍 验证新闻数据是否被引用...")
        
        # 检查关键词
        keywords = ["回购", "腾讯", "港元", "连续"]
        found_keywords = [kw for kw in keywords if kw in decision]
        
        if found_keywords:
            logger.info(f"✅ 发现新闻关键词: {found_keywords}")
            logger.info(f"✅ 分析报告中引用了数据库新闻！")
        else:
            logger.warning(f"⚠️ 未在分析报告中发现新闻关键词")
        
        logger.info("\n✅ 测试完成！")
        return decision
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="分析师整合测试工具")
    parser.add_argument("--stock", type=str, default="00700.HK", help="股票代码")
    parser.add_argument("--date", type=str, default="2025-12-14", help="交易日期")
    
    args = parser.parse_args()
    
    # 运行测试
    asyncio.run(test_analyst_with_news(args.stock, args.date))
