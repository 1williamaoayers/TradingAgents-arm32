#!/usr/bin/env python3
"""
简化的新闻工具测试 - 直接展示数据库新闻被读取
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tradingagents.utils.logging_manager import get_logger
logger = get_logger('news_tool_test')


def test_unified_news_tool():
    """测试统一新闻工具是否从数据库读取新闻"""
    
    logger.info("🚀 测试统一新闻工具")
    logger.info("=" * 60)
    
    try:
        # 1. 验证数据库中有新闻
        logger.info("\n📡 [1/2] 验证数据库中的新闻...")
        from pymongo import MongoClient
        
        mongo_uri = "mongodb://admin:tradingagents123@mongodb:27017/?authSource=admin"
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client["tradingagents"]
        
        news_count = db.stock_news.count_documents({"stock_code": "00700.HK"})
        logger.info(f"✅ 数据库中有 {news_count} 条 00700.HK 的新闻")
        
        if news_count > 0:
            news_list = list(db.stock_news.find({"stock_code": "00700.HK"}).limit(5))
            logger.info(f"\n📰 数据库中的新闻:")
            for i, news in enumerate(news_list, 1):
                logger.info(f"  {i}. {news.get('title', '无标题')}")
        
        client.close()
        
        # 2. 测试统一新闻工具
        logger.info(f"\n🔧 [2/2] 测试统一新闻工具...")
        from tradingagents.tools.unified_news_tool import UnifiedNewsAnalyzer
        
        # 创建一个空的 toolkit（因为我们只测试数据库读取）
        class EmptyToolkit:
            pass
        
        toolkit = EmptyToolkit()
        analyzer = UnifiedNewsAnalyzer(toolkit)
        
        # 调用统一新闻工具
        logger.info(f"\n📊 调用 get_stock_news_unified('00700.HK')...")
        result = analyzer.get_stock_news_unified("00700.HK", max_news=10)
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 新闻工具返回结果:")
        logger.info("=" * 60)
        
        if isinstance(result, dict):
            logger.info(f"状态: {result.get('status', 'unknown')}")
            logger.info(f"股票类型: {result.get('stock_type', 'unknown')}")
            logger.info(f"内容长度: {len(result.get('content', ''))} 字符")
            logger.info(f"\n内容预览 (前1000字符):")
            logger.info(result.get('content', '')[:1000])
            
            # 验证是否包含新闻关键词
            content = result.get('content', '')
            keywords = ["回购", "腾讯", "港元", "连续"]
            found_keywords = [kw for kw in keywords if kw in content]
            
            if found_keywords:
                logger.info(f"\n✅ 发现数据库新闻关键词: {found_keywords}")
                logger.info(f"✅ 统一新闻工具成功从数据库读取新闻！")
            else:
                logger.warning(f"\n⚠️ 未发现预期的新闻关键词")
        else:
            logger.info(f"返回类型: {type(result)}")
            logger.info(f"返回内容: {result}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ 测试完成！")
        logger.info("=" * 60)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    test_unified_news_tool()
