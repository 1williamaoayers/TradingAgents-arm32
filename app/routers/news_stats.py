"""
新闻统计API
提供新闻同步监控所需的统计数据
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from fastapi import APIRouter, Depends

from app.core.database import get_mongo_db
from app.core.response import ok, fail

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/news", tags=["新闻统计"])


@router.get("/stats")
async def get_news_stats(db=Depends(get_mongo_db)) -> Dict[str, Any]:
    """
    获取新闻统计总览
    
    Returns:
        新闻统计数据
    """
    try:
        # 总新闻数
        total_news = await db.stock_news.count_documents({})
        
        # 今日新增（最近24小时）
        yesterday = datetime.utcnow() - timedelta(days=1)
        today_news = await db.stock_news.count_documents({
            "created_at": {"$gte": yesterday}
        })
        
        # 自选股数量
        watchlist_count = await db.user_favorites.count_documents({})
        
        # 最近同步时间
        last_sync = await db.news_sync_history.find_one(
            {},
            sort=[("sync_time", -1)]
        )
        
        last_sync_time = None
        if last_sync:
            sync_time = last_sync.get("sync_time")
            if sync_time:
                # 计算时间差
                delta = datetime.utcnow() - sync_time
                hours = int(delta.total_seconds() / 3600)
                if hours < 1:
                    minutes = int(delta.total_seconds() / 60)
                    last_sync_time = f"{minutes}分钟前"
                elif hours < 24:
                    last_sync_time = f"{hours}小时前"
                else:
                    days = int(hours / 24)
                    last_sync_time = f"{days}天前"
        
        return ok({
            "total_news": total_news,
            "today_news": today_news,
            "watchlist_count": watchlist_count,
            "last_sync_time": last_sync_time,
            "last_sync_status": last_sync.get("status") if last_sync else None
        })
        
    except Exception as e:
        logger.error(f"获取新闻统计失败: {e}")
        return fail(f"获取统计失败: {str(e)}")


@router.get("/stats/sources")
async def get_source_stats(db=Depends(get_mongo_db)) -> Dict[str, Any]:
    """
    获取各新闻源统计
    
    Returns:
        各源新闻数量
    """
    try:
        # 聚合查询各源数量
        pipeline = [
            {"$group": {
                "_id": "$source",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        
        source_stats = []
        total = 0
        
        async for item in db.stock_news.aggregate(pipeline):
            count = item["count"]
            total += count
            source_stats.append({
                "source": item["_id"] or "未知",
                "count": count
            })
        
        # 计算百分比
        for stat in source_stats:
            stat["percentage"] = round(stat["count"] / total * 100, 1) if total > 0 else 0
        
        return ok({
            "sources": source_stats,
            "total": total
        })
        
    except Exception as e:
        logger.error(f"获取源统计失败: {e}")
        return fail(f"获取源统计失败: {str(e)}")


@router.get("/stats/watchlist")
async def get_watchlist_stats(db=Depends(get_mongo_db)) -> Dict[str, Any]:
    """
    获取watchlist新闻统计
    
    Returns:
        每只自选股的新闻数量
    """
    try:
        # 获取所有自选股
        watchlist_stocks = []
        favorites_docs = await db.user_favorites.find({}).to_list(None)
        
        for doc in favorites_docs:
            favorites = doc.get("favorites", [])
            for fav in favorites:
                stock_code = fav.get("stock_code")
                stock_name = fav.get("stock_name", stock_code)
                if stock_code:
                    watchlist_stocks.append({
                        "code": stock_code,
                        "name": stock_name
                    })
        
        # 查询每只股票的新闻数量
        stats = []
        for stock in watchlist_stocks:
            code = stock["code"]
            
            # 查询新闻数量
            count = await db.stock_news.count_documents({
                "symbol": code
            })
            
            # 最近7天新闻数量
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_count = await db.stock_news.count_documents({
                "symbol": code,
                "created_at": {"$gte": week_ago}
            })
            
            stats.append({
                "code": code,
                "name": stock["name"],
                "total_count": count,
                "recent_count": recent_count,
                "status": "✅" if count > 10 else "⚠️"
            })
        
        # 按新闻数量排序
        stats.sort(key=lambda x: x["total_count"], reverse=True)
        
        return ok({
            "stocks": stats,
            "total_stocks": len(stats)
        })
        
    except Exception as e:
        logger.error(f"获取watchlist统计失败: {e}")
        return fail(f"获取watchlist统计失败: {str(e)}")


@router.get("/stats/sync-history")
async def get_sync_history(
    limit: int = 10,
    db=Depends(get_mongo_db)
) -> Dict[str, Any]:
    """
    获取同步历史记录
    
    Args:
        limit: 返回记录数量
        
    Returns:
        同步历史列表
    """
    try:
        history = []
        
        cursor = db.news_sync_history.find({}).sort("sync_time", -1).limit(limit)
        
        async for record in cursor:
            history.append({
                "sync_time": record.get("sync_time").strftime("%Y-%m-%d %H:%M") if record.get("sync_time") else "N/A",
                "sync_type": record.get("sync_type", "unknown"),
                "status": record.get("status", "unknown"),
                "news_count": record.get("news_count", 0),
                "duration": round(record.get("duration", 0), 1),
                "source_stats": record.get("source_stats", {})
            })
        
        return ok({
            "history": history,
            "total": len(history)
        })
        
    except Exception as e:
        logger.error(f"获取同步历史失败: {e}")
        return fail(f"获取同步历史失败: {str(e)}")


@router.post("/trigger-sync")
async def trigger_news_sync() -> Dict[str, Any]:
    """
    手动触发新闻同步
    
    Returns:
        触发结果
    """
    try:
        from app.main import scheduler
        
        # 触发多源新闻同步任务
        job = scheduler.get_job('multi_source_news_sync')
        
        if job:
            job.modify(next_run_time=datetime.now())
            return ok({
                "message": "新闻同步任务已触发，将在几秒内开始执行",
                "job_id": "multi_source_news_sync"
            })
        else:
            return fail("未找到新闻同步任务，请检查配置")
            
    except Exception as e:
        logger.error(f"触发同步失败: {e}")
        return fail(f"触发同步失败: {str(e)}")
