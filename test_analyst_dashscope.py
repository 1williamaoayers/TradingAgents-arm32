#!/usr/bin/env python3
"""
完整的分析师测试 - 使用阿里百炼 API
展示数据库新闻数据被分析师使用
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


async def test_analyst_with_dashscope(stock_code: str = "00700.HK", trade_date: str = "2025-12-14"):
    """
    使用阿里百炼测试分析师是否使用 MongoDB 中的新闻数据
    
    Args:
        stock_code: 股票代码
        trade_date: 交易日期
    """
    logger.info(f"🚀 开始完整分析师测试: {stock_code}")
    logger.info(f"📊 交易日期: {trade_date}")
    logger.info(f"🤖 使用模型: 阿里百炼 (DashScope)")
    logger.info("=" * 80)
    
    try:
        # 1. 验证数据库中有新闻
        logger.info(f"\n📡 [步骤 1/4] 验证数据库中的新闻数据...")
        from pymongo import MongoClient
        
        mongo_uri = "mongodb://admin:tradingagents123@mongodb:27017/?authSource=admin"
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client["tradingagents"]
        
        news_count = db.stock_news.count_documents({"stock_code": stock_code})
        logger.info(f"✅ 数据库中有 {news_count} 条 {stock_code} 的新闻")
        
        if news_count > 0:
            news_list = list(db.stock_news.find({"stock_code": stock_code}).limit(5))
            logger.info(f"\n📰 数据库中的新闻标题:")
            for i, news in enumerate(news_list, 1):
                title = news.get('title', '无标题')
                logger.info(f"  {i}. {title}")
                # 提取关键词用于后续验证
                if i == 1:
                    first_news_title = title
        else:
            logger.warning(f"⚠️ 数据库中没有 {stock_code} 的新闻")
            first_news_title = ""
        
        client.close()
        
        # 2. 测试统一新闻工具
        logger.info(f"\n🔧 [步骤 2/4] 测试统一新闻工具是否读取数据库...")
        from tradingagents.tools.unified_news_tool import UnifiedNewsAnalyzer
        
        class EmptyToolkit:
            pass
        
        toolkit = EmptyToolkit()
        analyzer = UnifiedNewsAnalyzer(toolkit)
        
        news_result = analyzer.get_stock_news_unified(stock_code, max_news=10)
        
        if isinstance(news_result, dict):
            news_content = news_result.get('content', '')
            logger.info(f"✅ 新闻工具返回: {len(news_content)} 字符")
            
            # 验证是否包含数据库新闻
            if "回购" in news_content and "腾讯" in news_content:
                logger.info(f"✅ 新闻工具成功从数据库读取新闻！")
                logger.info(f"📋 新闻内容预览 (前500字符):")
                logger.info(news_content[:500])
            else:
                logger.warning(f"⚠️ 新闻工具未读取到预期的数据库新闻")
        
        # 3. 配置分析师
        logger.info(f"\n🎯 [步骤 3/4] 配置分析师并运行分析...")
        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = "dashscope"
        config["deep_think_llm"] = "qwen-max"
        config["quick_think_llm"] = "qwen-turbo"
        config["max_debate_rounds"] = 1
        config["online_tools"] = False  # 关闭在线工具，确保使用数据库
        
        logger.info(f"✅ 配置: {config['llm_provider']} / {config['deep_think_llm']}")
        logger.info(f"⏳ 开始分析，请耐心等待 1-2 分钟...")
        
        ta = TradingAgentsGraph(
            selected_analysts=["news"],  # 只运行新闻分析师
            debug=True,
            config=config
        )
        
        # 运行分析
        _, decision = ta.propagate(stock_code, trade_date)
        
        # 4. 验证结果
        logger.info(f"\n🔍 [步骤 4/4] 验证分析报告是否引用数据库新闻...")
        logger.info("\n" + "=" * 80)
        logger.info("📊 分析报告:")
        logger.info("=" * 80)
        logger.info(decision)
        logger.info("=" * 80)
        
        # 检查关键词
        keywords = ["回购", "腾讯", "港元", "连续", "12月"]
        found_keywords = [kw for kw in keywords if kw in decision]
        
        logger.info(f"\n✅ 验证结果:")
        if found_keywords:
            logger.info(f"  ✅ 发现数据库新闻关键词: {found_keywords}")
            logger.info(f"  ✅ 分析报告引用了数据库中的新闻数据！")
            
            # 检查是否包含具体的新闻标题内容
            if first_news_title and any(word in decision for word in first_news_title.split()[:3]):
                logger.info(f"  ✅ 分析报告中提及了具体的新闻事件！")
        else:
            logger.warning(f"  ⚠️ 未在分析报告中发现预期的新闻关键词")
        
        logger.info("\n✅ 测试完成！")
        return decision
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="完整分析师测试工具")
    parser.add_argument("--stock", type=str, default="00700.HK", help="股票代码")
    parser.add_argument("--date", type=str, default="2025-12-14", help="交易日期")
    
    args = parser.parse_args()
    
    # 运行测试
    asyncio.run(test_analyst_with_dashscope(args.stock, args.date))
