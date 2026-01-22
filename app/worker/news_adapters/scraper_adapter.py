"""
Playwright爬虫API适配器
调用 playwriteOCR 项目的 RESTful API 获取新闻
支持即时双写：获取新闻时自动异步缓存到数据库
"""
import asyncio
import logging
import os
import aiohttp
from typing import List, Dict, Any
from datetime import datetime

from app.worker.news_adapters.base import NewsSourceAdapter, create_standard_news_item

logger = logging.getLogger(__name__)

# 即时双写开关（通过环境变量控制）
ENABLE_INSTANT_CACHE = os.getenv("SCRAPER_INSTANT_CACHE", "true").lower() == "true"


class ScraperAdapter(NewsSourceAdapter):
    """Playwright爬虫API适配器（支持即时双写）"""
    
    def __init__(self, api_url: str = None):
        super().__init__("scraper")
        # Docker容器内使用网关IP访问宿主机
        # 可通过环境变量SCRAPER_API_URL覆盖
        default_url = os.getenv("SCRAPER_API_URL", "http://172.20.0.1:9527")
        self.api_url = api_url or default_url

    
    async def get_news(self, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取指定股票的新闻
        
        Args:
            symbol: 股票代码或公司名称
            limit: 最大新闻数量
            
        Returns:
            新闻列表
        """
        try:
            # 调用爬虫API
            url = f"{self.api_url}/api/v1/news"
            params = {
                "keyword": symbol,
                "limit": limit
                # sources 不传，默认采集全部 8 个源
            }
            
            async with aiohttp.ClientSession() as session:
                # 爬虫任务耗时较长，设置为 900秒 (15分钟) 超时
                async with session.get(url, params=params, timeout=900) as resp:
                    if resp.status != 200:
                        logger.error(f"[Scraper] API返回错误: {resp.status}")
                        return []
                    
                    data = await resp.json()
                    
                    if not data.get("success"):
                        logger.error(f"[Scraper] API失败: {data.get('error')}")
                        return []
                    
                    raw_news_list = data.get("data", [])
                    
                    # 转换为标准格式
                    news_list = []
                    for raw_news in raw_news_list:
                        normalized = self.normalize_news(raw_news)
                        news_list.append(normalized)
                    
                    logger.info(f"[Scraper] {symbol} 采集到 {len(news_list)} 条新闻")
                    
                    # 🔥 即时双写：异步缓存到数据库（不阻塞主流程）
                    if ENABLE_INSTANT_CACHE and news_list:
                        asyncio.create_task(self._cache_to_db(news_list, symbol))
                    
                    return news_list
                    
        except aiohttp.ClientError as e:
            logger.error(f"[Scraper] 网络错误: {e}")
            self.record_error()
            return []
        except Exception as e:
            logger.error(f"[Scraper] 获取新闻失败: {symbol} - {e}")
            self.record_error()
            return []
    
    async def _cache_to_db(self, news_list: List[Dict[str, Any]], symbol: str):
        """
        即时双写：异步缓存新闻到数据库（不阻塞主流程）
        
        Args:
            news_list: 新闻列表
            symbol: 股票代码
        """
        try:
            # 延迟导入，避免循环依赖
            from app.worker.scraper_sync_service import get_scraper_sync_service
            
            service = get_scraper_sync_service()
            await service.cache_news_immediately(news_list, symbol)
            
        except Exception as e:
            # 即时缓存失败不影响主流程，只记录警告日志
            logger.warning(f"[Scraper] 即时缓存失败（不影响分析）: {symbol} - {e}")
    
    def normalize_news(self, raw_news: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化爬虫API返回的新闻为统一格式
        
        Args:
            raw_news: API原始新闻（已是标准格式）
            
        Returns:
            标准化的新闻字典
        """
        # API已经返回标准格式，直接使用
        return create_standard_news_item(
            symbol=raw_news.get("symbol", ""),
            title=raw_news.get("title", ""),
            source=raw_news.get("source", "Scraper"),
            summary=raw_news.get("summary", ""),
            content=raw_news.get("content", ""),
            source_type="scraper",
            url=raw_news.get("url", ""),
            publish_time=raw_news.get("publish_time") or datetime.utcnow(),
            sentiment=raw_news.get("sentiment", "neutral"),
            relevance_score=raw_news.get("relevance_score", 0.8),
            tags=raw_news.get("tags", [])
        )

