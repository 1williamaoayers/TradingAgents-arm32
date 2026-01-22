"""
爬虫新闻定时同步服务
只同步自选股，智能调整采集频率，支持即时双写
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def get_sync_interval() -> int:
    """
    根据时间返回采集间隔（分钟）
    - 交易时段（9:30-16:00）：每1小时
    - 盘前盘后（6:00-20:00）：每2小时
    - 深夜（20:00-6:00）：每6小时
    - 周末/节假日：每12小时
    """
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    is_weekend = now.weekday() >= 5  # 周六=5，周日=6
    
    if is_weekend:
        return 720  # 12小时
    
    # 交易时段（9:30-16:00）
    if (hour == 9 and minute >= 30) or (10 <= hour < 16):
        return 60   # 1小时
    # 盘前盘后（6:00-20:00）
    elif 6 <= hour < 20:
        return 120  # 2小时
    # 深夜
    else:
        return 360  # 6小时


class ScraperSyncService:
    """爬虫新闻定时同步服务"""
    
    def __init__(self):
        self.scraper = None  # 延迟初始化，避免循环导入
        self.db = None
        self._initialized = False
        self.stats = {
            "total_syncs": 0,
            "last_sync_time": None,
            "last_sync_count": 0,
            "errors": []
        }
    
    async def initialize(self):
        """延迟初始化，避免启动时的导入问题"""
        if self._initialized:
            return
        
        try:
            # 导入ScraperAdapter
            from app.worker.news_adapters.scraper_adapter import ScraperAdapter
            self.scraper = ScraperAdapter()
            
            # 连接MongoDB（使用环境变量中的认证信息）
            from motor.motor_asyncio import AsyncIOMotorClient
            import os
            
            host = os.getenv("MONGODB_HOST", "mongodb")
            port = os.getenv("MONGODB_PORT", "27017")
            username = os.getenv("MONGODB_USERNAME", "")
            password = os.getenv("MONGODB_PASSWORD", "")
            database = os.getenv("MONGODB_DATABASE", "tradingagents")
            
            # 构建连接URI（支持有认证和无认证两种情况）
            if username and password:
                mongo_uri = f"mongodb://{username}:{password}@{host}:{port}/{database}?authSource=admin"
            else:
                mongo_uri = f"mongodb://{host}:{port}"
            
            mongo_client = AsyncIOMotorClient(mongo_uri)
            self.db = mongo_client[database]
            
            self._initialized = True
            logger.info("[ScraperSync] ✅ 服务初始化成功")
        except Exception as e:
            logger.error(f"[ScraperSync] ❌ 初始化失败: {e}")
            raise
    
    async def get_all_favorite_stocks(self) -> List[str]:
        """
        获取所有用户的自选股列表（去重）
        
        Returns:
            List[str]: 去重后的股票代码列表
        """
        try:
            if self.db is None:
                await self.initialize()
            
            # 查询user_favorites集合（favorites是嵌套数组）
            collection = self.db.user_favorites
            cursor = collection.find({}, {'favorites': 1})
            
            favorites_set = set()
            async for doc in cursor:
                # favorites是一个数组，每个元素包含stock_code
                favorites_list = doc.get('favorites', [])
                for fav in favorites_list:
                    stock_code = fav.get('stock_code') or fav.get('symbol')
                    if stock_code:
                        favorites_set.add(stock_code)
            
            logger.info(f"[ScraperSync] 获取到 {len(favorites_set)} 只自选股")
            return list(favorites_set)
        
        except Exception as e:
            logger.error(f"[ScraperSync] 获取自选股失败: {e}")
            return []
    
    async def sync_favorite_stocks(self) -> Dict[str, Any]:
        """
        同步所有自选股新闻到数据库
        
        Returns:
            Dict: 同步统计信息
        """
        start_time = datetime.now()
        
        try:
            await self.initialize()
            
            # 获取自选股列表
            favorites = await self.get_all_favorite_stocks()
            
            if not favorites:
                logger.info("[ScraperSync] 没有自选股，跳过同步")
                return {"status": "skipped", "reason": "no_favorites"}
            
            logger.info(f"[ScraperSync] 🚀 开始同步 {len(favorites)} 只自选股...")
            
            # 统计
            success_count = 0
            total_news = 0
            total_fetched = 0  # 新增: 统计抓取总数
            errors = []
            
            # 分批并发采集（5个一批，避免过载）
            batch_size = 5
            for i in range(0, len(favorites), batch_size):
                batch = favorites[i:i+batch_size]
                
                # 并发采集这一批
                tasks = [self._sync_single_stock(stock) for stock in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for stock, result in zip(batch, results):
                    if isinstance(result, Exception):
                        errors.append(f"{stock}: {str(result)}")
                    elif result and result.get("success"):
                        success_count += 1
                        total_news += result.get("saved_count", 0)
                        total_fetched += result.get("fetched_count", 0)  # 累加抓取数
                
                # 批次间休息10秒，避免爬虫服务过载
                if i + batch_size < len(favorites):
                    await asyncio.sleep(10)
            
            # 更新统计
            self.stats["total_syncs"] += 1
            self.stats["last_sync_time"] = datetime.now()
            self.stats["last_sync_count"] = total_news
            if errors:
                self.stats["errors"] = errors[-5:]  # 只保留最近5个错误
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            result = {
                "status": "success",
                "favorites_count": len(favorites),
                "success_count": success_count,
                "total_news_saved": total_news,
                "total_fetched": total_fetched,
                "errors": errors,
                "elapsed_seconds": round(elapsed, 2)
            }
            
            logger.info(f"[ScraperSync] ✅ 同步完成: {success_count}/{len(favorites)} 成功, "
                       f"新增 {total_news} 条新闻 (抓取 {total_fetched}), 耗时 {elapsed:.1f}秒")

            # 保存同步历史 (新增: 确保Scraper任务可见) 
            try:
                # 转换为标准格式
                sync_record = {
                    "sync_type": "scraper", 
                    "total_stocks": len(favorites),
                    "success_count": success_count,
                    "news_count": total_news,
                    "fetched_count": total_fetched,  # 新增: 记录抓取总数
                    "error_count": len(errors),
                    "duration": round(elapsed, 2),
                    "status": "success" if not errors else "partial",
                    "sync_time": datetime.utcnow(),  # 使用 UTC 时间以保持一致性
                    "created_at": datetime.utcnow()
                }
                
                # 只有当数据库连接初始化成功时才写入
                if self.db is not None:
                     await self.db.news_sync_history.insert_one(sync_record)
                     logger.info(f"[ScraperSync] 📜 同步记录已写入历史表: {success_count}成功/{len(errors)}失败")
                else:
                    logger.warning("[ScraperSync] ⚠️ 数据库未连接，无法写入同步历史")

            except Exception as e:
                logger.error(f"[ScraperSync] ❌ 保存同步历史失败: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"[ScraperSync] ❌ 同步任务失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"status": "error", "error": str(e)}
    
    async def _sync_single_stock(self, stock_code: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        同步单只股票新闻（带重试机制）
        
        Args:
            stock_code: 股票代码
            max_retries: 最大重试次数
            
        Returns:
            Dict: 同步结果
        """
        for attempt in range(max_retries):
            try:
                # 调用爬虫API获取新闻
                news_list = await self.scraper.get_news(stock_code, limit=50)
                
                if not news_list:
                    logger.info(f"[ScraperSync] {stock_code}: 无新闻数据")
                    return {"success": True, "saved_count": 0}
                
                # 去重保存到数据库
                saved_count = await self._save_with_dedup(news_list, stock_code)
                
                logger.info(f"[ScraperSync] {stock_code}: 采集 {len(news_list)} 条, 新增 {saved_count} 条")
                return {"success": True, "saved_count": saved_count, "fetched_count": len(news_list)}
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"[ScraperSync] {stock_code} 采集失败 (尝试 {attempt+1}/{max_retries}): {e}")
                    await asyncio.sleep(30)  # 等待30秒后重试
                else:
                    logger.error(f"[ScraperSync] {stock_code} 采集失败 (已重试 {max_retries} 次): {e}")
                    return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "max_retries_exceeded"}
    
    async def _save_with_dedup(self, news_list: List[Dict], stock_code: str) -> int:
        """
        去重保存新闻到数据库
        
        Args:
            news_list: 新闻列表
            stock_code: 股票代码
            
        Returns:
            int: 实际保存的条数
        """
        if self.db is None:
            await self.initialize()
        
        collection = self.db.stock_news
        saved_count = 0
        
        for news in news_list:
            try:
                title = news.get('title', '')
                if not title:
                    continue
                
                # 检查是否已存在（标题+来源去重）
                existing = await collection.find_one({
                    'title': title,
                    'source': news.get('source', 'scraper')
                })
                
                if not existing:
                    # 添加元数据
                    news_doc = {
                        **news,
                        'symbol': stock_code,
                        'source_type': 'scraper',
                        'sync_time': datetime.now(),
                        'created_at': datetime.now()
                    }
                    
                    await collection.insert_one(news_doc)
                    saved_count += 1
                    
            except Exception as e:
                logger.warning(f"[ScraperSync] 保存新闻失败: {e}")
                continue
        
        return saved_count
    
    async def cache_news_immediately(self, news_list: List[Dict], stock_code: str):
        """
        即时双写：将新闻缓存到数据库（异步，不阻塞主流程）
        
        Args:
            news_list: 新闻列表
            stock_code: 股票代码
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            saved_count = await self._save_with_dedup(news_list, stock_code)
            
            if saved_count > 0:
                logger.info(f"[ScraperSync] 即时缓存 {stock_code}: {saved_count} 条新增")
                
        except Exception as e:
            # 即时缓存失败不影响主流程，只记录日志
            logger.warning(f"[ScraperSync] 即时缓存失败 {stock_code}: {e}")


# 全局单例
_scraper_sync_service: Optional[ScraperSyncService] = None


def get_scraper_sync_service() -> ScraperSyncService:
    """获取同步服务单例"""
    global _scraper_sync_service
    if _scraper_sync_service is None:
        _scraper_sync_service = ScraperSyncService()
    return _scraper_sync_service
