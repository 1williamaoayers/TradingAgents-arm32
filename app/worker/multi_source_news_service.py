"""
多源新闻聚合服务
整合多个新闻源，提供统一的新闻获取接口
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.database import get_mongo_db
from app.services.news_data_service import get_news_data_service
from app.worker.news_adapters.base import NewsSourceAdapter

logger = logging.getLogger(__name__)


class MultiSourceNewsService:
    """多源新闻聚合服务"""
    
    def __init__(self):
        """初始化服务"""
        self.db = None
        self.news_service = None
        self.adapters: List[NewsSourceAdapter] = []
        self.batch_size = 10
        self.timeout = 30  # 秒
        
    async def initialize(self):
        """初始化服务"""
        logger.info("🔄 初始化多源新闻聚合服务...")
        
        # 初始化数据库
        self.db = get_mongo_db()
        self.news_service = await get_news_data_service()
        
        # 初始化所有适配器
        await self._initialize_adapters()
        
        logger.info(f"✅ 多源新闻聚合服务初始化完成，共 {len(self.adapters)} 个新闻源")
    
    async def _initialize_adapters(self):
        """初始化所有新闻源适配器"""
        import os
        
        # 1. AKShare适配器（始终启用）
        try:
            from app.worker.news_adapters.akshare_adapter import AKShareAdapter
            akshare = AKShareAdapter()
            await akshare.initialize()
            self.adapters.append(akshare)
            logger.info("✅ AKShare适配器已加载")
        except Exception as e:
            logger.error(f"❌ AKShare适配器加载失败: {e}")
        
        # 2. Alpha Vantage适配器（需要API Key）
        if os.getenv("NEWS_SOURCE_ALPHA_VANTAGE", "true").lower() == "true":
            try:
                from app.worker.news_adapters.alpha_vantage_adapter import AlphaVantageAdapter
                alpha_vantage = AlphaVantageAdapter()
                if alpha_vantage.api_key:
                    self.adapters.append(alpha_vantage)
                    logger.info("✅ Alpha Vantage适配器已加载")
                else:
                    logger.warning("⚠️ Alpha Vantage API Key未配置，跳过")
            except Exception as e:
                logger.error(f"❌ Alpha Vantage适配器加载失败: {e}")
        
        # 3. FinnHub适配器（需要API Key）
        if os.getenv("NEWS_SOURCE_FINNHUB", "true").lower() == "true":
            try:
                from app.worker.news_adapters.finnhub_adapter import FinnHubAdapter
                finnhub = FinnHubAdapter()
                if finnhub.api_key:
                    self.adapters.append(finnhub)
                    logger.info("✅ FinnHub适配器已加载")
                else:
                    logger.warning("⚠️ FinnHub API Key未配置，跳过")
            except Exception as e:
                logger.error(f"❌ FinnHub适配器加载失败: {e}")
        
        # 4. RSS适配器
        if os.getenv("NEWS_SOURCE_RSS", "true").lower() == "true":
            try:
                from app.worker.news_adapters.rss_adapter import RSSAdapter
                rss = RSSAdapter()
                self.adapters.append(rss)
                logger.info("✅ RSS适配器已加载")
            except Exception as e:
                logger.error(f"❌ RSS适配器加载失败: {e}")
        
        logger.info(f"📊 共加载 {len(self.adapters)} 个新闻源适配器")
    
    async def sync_news_data(
        self,
        symbols: List[str] = None,
        max_news_per_stock: int = 20,
        force_update: bool = False,
        favorites_only: bool = True
    ) -> Dict[str, Any]:
        """
        同步新闻数据（主入口）
        
        Args:
            symbols: 股票代码列表
            max_news_per_stock: 每只股票最大新闻数量
            force_update: 是否强制更新
            favorites_only: 是否只同步自选股
            
        Returns:
            同步结果统计
        """
        logger.info("🔄 开始多源新闻数据同步...")
        
        stats = {
            "total_processed": 0,
            "success_count": 0,
            "error_count": 0,
            "news_count": 0,
            "source_stats": {},
            "start_time": datetime.utcnow(),
            "favorites_only": favorites_only,
            "errors": []
        }
        
        try:
            # 1. 获取股票列表
            if symbols is None:
                if favorites_only:
                    symbols = await self._get_favorite_stocks()
                    logger.info(f"📌 只同步自选股，共 {len(symbols)} 只")
                else:
                    stock_list = await self.db.stock_basic_info.find(
                        {}, {"code": 1, "_id": 0}
                    ).to_list(None)
                    symbols = [s["code"] for s in stock_list if s.get("code")]
                    logger.info(f"📊 同步所有股票，共 {len(symbols)} 只")
            
            if not symbols:
                logger.warning("⚠️ 没有找到需要同步新闻的股票")
                return stats
            
            stats["total_processed"] = len(symbols)
            
            # 2. 批量处理
            for i in range(0, len(symbols), self.batch_size):
                batch = symbols[i:i + self.batch_size]
                batch_stats = await self._process_batch(batch, max_news_per_stock)
                
                # 更新统计
                stats["success_count"] += batch_stats["success_count"]
                stats["error_count"] += batch_stats["error_count"]
                stats["news_count"] += batch_stats["news_count"]
                stats["errors"].extend(batch_stats["errors"])
                
                # 合并源统计
                for source, count in batch_stats.get("source_stats", {}).items():
                    stats["source_stats"][source] = stats["source_stats"].get(source, 0) + count
                
                # 进度日志
                progress = min(i + self.batch_size, len(symbols))
                logger.info(f"📈 进度: {progress}/{len(symbols)} "
                           f"(成功: {stats['success_count']}, 新闻: {stats['news_count']})")
                
                # API限流
                if i + self.batch_size < len(symbols):
                    await asyncio.sleep(0.5)
            
            # 3. 完成统计
            stats["end_time"] = datetime.utcnow()
            stats["duration"] = (stats["end_time"] - stats["start_time"]).total_seconds()
            
            logger.info(f"✅ 多源新闻数据同步完成: "
                       f"总计 {stats['total_processed']} 只股票, "
                       f"成功 {stats['success_count']} 只, "
                       f"获取 {stats['news_count']} 条新闻, "
                       f"耗时 {stats['duration']:.2f} 秒")
            
            # 输出各源统计
            for source, count in stats["source_stats"].items():
                logger.info(f"  📰 {source}: {count} 条新闻")
            
            # 4. 保存同步历史记录
            try:
                await self._save_sync_history(stats)
            except Exception as e:
                logger.error(f"保存同步历史失败: {e}")
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ 多源新闻数据同步失败: {e}")
            stats["errors"].append({"error": str(e), "context": "sync_news_data"})
            return stats
    
    async def _process_batch(
        self,
        batch: List[str],
        max_news_per_stock: int
    ) -> Dict[str, Any]:
        """
        处理一批股票的新闻获取
        
        Args:
            batch: 股票代码列表
            max_news_per_stock: 每只股票最大新闻数量
            
        Returns:
            批次统计信息
        """
        batch_stats = {
            "success_count": 0,
            "error_count": 0,
            "news_count": 0,
            "source_stats": {},
            "errors": []
        }
        
        for symbol in batch:
            try:
                # 从所有源获取新闻
                all_news = await self._fetch_from_all_sources(symbol, max_news_per_stock)
                
                if all_news:
                    # 去重
                    unique_news = self._deduplicate_news(all_news)
                    
                    # 保存到数据库
                    saved_count = await self._save_news(unique_news)
                    
                    batch_stats["success_count"] += 1
                    batch_stats["news_count"] += saved_count
                    
                    # 统计各源新闻数量
                    for news in unique_news:
                        source = news.get("source", "unknown")
                        batch_stats["source_stats"][source] = batch_stats["source_stats"].get(source, 0) + 1
                    
                    logger.debug(f"✅ {symbol} 新闻同步成功: {saved_count}条")
                else:
                    logger.debug(f"⚠️ {symbol} 未获取到新闻")
                    batch_stats["success_count"] += 1
                
                await asyncio.sleep(0.2)
                
            except Exception as e:
                batch_stats["error_count"] += 1
                error_msg = f"{symbol}: {str(e)}"
                batch_stats["errors"].append(error_msg)
                logger.error(f"❌ {symbol} 新闻同步失败: {e}")
                await asyncio.sleep(1.0)
        
        return batch_stats
    
    async def _fetch_from_all_sources(
        self,
        symbol: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        并行从所有源获取新闻
        
        Args:
            symbol: 股票代码
            limit: 每个源的最大新闻数量
            
        Returns:
            所有源的新闻列表
        """
        all_news = []
        
        # 获取可用的适配器
        available_adapters = [a for a in self.adapters if a.is_available()]
        
        if not available_adapters:
            logger.warning(f"⚠️ 没有可用的新闻源")
            return all_news
        
        # 并行获取
        tasks = [
            self._fetch_from_source(adapter, symbol, limit)
            for adapter in available_adapters
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 合并结果
        for i, result in enumerate(results):
            if isinstance(result, list):
                all_news.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"源 {available_adapters[i].source_name} 获取失败: {result}")
        
        return all_news
    
    async def _fetch_from_source(
        self,
        adapter: NewsSourceAdapter,
        symbol: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        从单个源获取新闻
        
        Args:
            adapter: 新闻源适配器
            symbol: 股票代码
            limit: 最大新闻数量
            
        Returns:
            新闻列表
        """
        try:
            news_list = await asyncio.wait_for(
                adapter.get_news(symbol, limit),
                timeout=self.timeout
            )
            adapter.record_success()
            return news_list
        except asyncio.TimeoutError:
            logger.warning(f"[{adapter.source_name}] 获取超时: {symbol}")
            adapter.record_error()
            return []
        except Exception as e:
            logger.error(f"[{adapter.source_name}] 获取失败: {symbol} - {e}")
            adapter.record_error()
            return []
    
    def _deduplicate_news(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        去重新闻（简单版本：按标题）
        
        Args:
            news_list: 新闻列表
            
        Returns:
            去重后的新闻列表
        """
        seen_titles = set()
        unique_news = []
        
        for news in news_list:
            title = news.get("title", "")
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_news.append(news)
        
        return unique_news
    
    async def _save_news(self, news_list: List[Dict[str, Any]]) -> int:
        """
        保存新闻到数据库
        
        Args:
            news_list: 新闻列表
            
        Returns:
            保存的新闻数量
        """
        if not news_list:
            return 0
        
        try:
            saved_count = await self.news_service.save_news_data(
                news_data=news_list,
                data_source="multi_source",
                market="CN"
            )
            return saved_count
        except Exception as e:
            logger.error(f"保存新闻失败: {e}")
            return 0
    
    async def _get_favorite_stocks(self) -> List[str]:
        """
        获取所有用户的自选股列表
        
        Returns:
            自选股代码列表
        """
        try:
            favorites_docs = await self.db.user_favorites.find(
                {},
                {"favorites": 1, "_id": 0}
            ).to_list(None)
            
            stock_codes = set()
            for doc in favorites_docs:
                favorites = doc.get("favorites", [])
                for fav in favorites:
                    code = fav.get("stock_code")
                    if code:
                        stock_codes.add(code)
            
            return list(stock_codes)
            
        except Exception as e:
            logger.error(f"获取自选股失败: {e}")
            return []
    
    async def _save_sync_history(self, stats: Dict[str, Any]):
        """
        保存同步历史记录
        
        Args:
            stats: 同步统计数据
        """
        try:
            import uuid
            
            history_record = {
                "sync_id": str(uuid.uuid4()),
                "sync_time": stats["start_time"],
                "sync_type": "multi_source",
                "status": "success" if stats["error_count"] == 0 else "partial_success",
                "total_stocks": stats["total_processed"],
                "success_count": stats["success_count"],
                "error_count": stats["error_count"],
                "news_count": stats["news_count"],
                "source_stats": stats["source_stats"],
                "duration": stats["duration"],
                "errors": stats["errors"][:10] if stats["errors"] else []  # 只保存前10个错误
            }
            
            await self.db.news_sync_history.insert_one(history_record)
            logger.debug(f"同步历史记录已保存: {history_record['sync_id']}")
            
        except Exception as e:
            logger.error(f"保存同步历史失败: {e}")


# 全局服务实例
_multi_source_news_service = None


async def get_multi_source_news_service() -> MultiSourceNewsService:
    """获取多源新闻服务实例"""
    global _multi_source_news_service
    
    if _multi_source_news_service is None:
        _multi_source_news_service = MultiSourceNewsService()
        await _multi_source_news_service.initialize()
    
    return _multi_source_news_service
