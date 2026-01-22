"""
定时清理过期爬虫新闻
保护重要公告（财报、回购等），只清理普通新闻
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

logger = logging.getLogger(__name__)


async def cleanup_old_scraper_news(
    retention_days: int = 90,
    protected_tags: list = None
) -> Dict[str, Any]:
    """
    清理过期的爬虫新闻
    
    Args:
        retention_days: 保留天数，默认90天
        protected_tags: 受保护的标签列表（包含这些标签的新闻不会被删除）
        
    Returns:
        Dict: 清理结果统计
    """
    if protected_tags is None:
        protected_tags = ['公告', '财报', '回购', '分红', '业绩', '年报', '季报', '半年报']
    
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import os
        
        # 连接MongoDB
        mongo_uri = os.getenv("MONGODB_URI", "mongodb://mongodb:27017")
        mongo_client = AsyncIOMotorClient(mongo_uri)
        db = mongo_client['tradingagents']
        collection = db.stock_news
        
        # 计算截止日期
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        # 构建查询条件：
        # 1. source_type 是 scraper（只清理爬虫数据）
        # 2. publish_time 早于截止日期
        # 3. tags 不包含受保护的标签
        # 4. title 不包含受保护的关键词
        
        # 构建标题保护正则（任何受保护关键词）
        protected_pattern = '|'.join(protected_tags)
        
        query = {
            'source_type': 'scraper',
            '$or': [
                {'publish_time': {'$lt': cutoff_date}},
                {'created_at': {'$lt': cutoff_date}},
                {'sync_time': {'$lt': cutoff_date}}
            ],
            'tags': {'$not': {'$elemMatch': {'$in': protected_tags}}},
            'title': {'$not': {'$regex': protected_pattern, '$options': 'i'}}
        }
        
        # 先统计要删除的数量
        count_to_delete = await collection.count_documents(query)
        
        if count_to_delete == 0:
            logger.info(f"[Cleanup] 没有需要清理的过期新闻 (保留 {retention_days} 天内)")
            return {
                "status": "success",
                "deleted_count": 0,
                "retention_days": retention_days,
                "cutoff_date": cutoff_date.isoformat()
            }
        
        # 执行删除
        result = await collection.delete_many(query)
        
        logger.info(f"[Cleanup] ✅ 清理完成: 删除 {result.deleted_count} 条过期爬虫新闻 "
                   f"(保留 {retention_days} 天内, 受保护标签: {protected_tags})")
        
        return {
            "status": "success",
            "deleted_count": result.deleted_count,
            "retention_days": retention_days,
            "cutoff_date": cutoff_date.isoformat(),
            "protected_tags": protected_tags
        }
        
    except Exception as e:
        logger.error(f"[Cleanup] ❌ 清理任务失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "error": str(e)
        }


async def get_scraper_news_stats() -> Dict[str, Any]:
    """
    获取爬虫新闻统计信息
    
    Returns:
        Dict: 统计信息（总数、各时间段分布、来源分布等）
    """
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import os
        
        mongo_uri = os.getenv("MONGODB_URI", "mongodb://mongodb:27017")
        mongo_client = AsyncIOMotorClient(mongo_uri)
        db = mongo_client['tradingagents']
        collection = db.stock_news
        
        # 总数
        total_count = await collection.count_documents({'source_type': 'scraper'})
        
        # 最近7天
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_count = await collection.count_documents({
            'source_type': 'scraper',
            'created_at': {'$gte': seven_days_ago}
        })
        
        # 最近30天
        thirty_days_ago = datetime.now() - timedelta(days=30)
        monthly_count = await collection.count_documents({
            'source_type': 'scraper',
            'created_at': {'$gte': thirty_days_ago}
        })
        
        # 按来源统计
        pipeline = [
            {'$match': {'source_type': 'scraper'}},
            {'$group': {'_id': '$source', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]
        
        source_stats = {}
        async for doc in collection.aggregate(pipeline):
            source_stats[doc['_id'] or 'unknown'] = doc['count']
        
        # 按股票统计（前10）
        pipeline = [
            {'$match': {'source_type': 'scraper'}},
            {'$group': {'_id': '$symbol', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]
        
        stock_stats = {}
        async for doc in collection.aggregate(pipeline):
            stock_stats[doc['_id'] or 'unknown'] = doc['count']
        
        return {
            "total_count": total_count,
            "recent_7_days": recent_count,
            "recent_30_days": monthly_count,
            "by_source": source_stats,
            "top_10_stocks": stock_stats,
            "query_time": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[Stats] 获取统计失败: {e}")
        return {"error": str(e)}
