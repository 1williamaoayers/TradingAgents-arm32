"""
AKShare新闻源适配器
复用现有的AKShare提供器获取新闻
"""
import logging
from typing import List, Dict, Any
from datetime import datetime

from app.worker.news_adapters.base import NewsSourceAdapter, create_standard_news_item
from tradingagents.dataflows.providers.china.akshare import get_akshare_provider
from app.worker.news_utils.keyword_generator import get_keyword_generator

logger = logging.getLogger(__name__)


class AKShareAdapter(NewsSourceAdapter):
    """AKShare新闻源适配器"""
    
    def __init__(self):
        super().__init__("akshare")
        self.provider = None
    
    async def initialize(self):
        """初始化AKShare提供器"""
        self.provider = get_akshare_provider()  # 不需要await
        logger.info("✅ AKShare适配器初始化完成")
    
    async def get_news(self, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取指定股票的新闻
        
        Args:
            symbol: 股票代码
            limit: 最大新闻数量
            
        Returns:
            新闻列表
        """
        try:
            # 1. 获取 AI 联想关键词（用于增强搜索和后续过滤）
            kw_gen = get_keyword_generator()
            # 注意：generate_keywords 是 async 且内部包装了线程池调用 LLM
            keywords = await kw_gen.generate_keywords(symbol)
            search_query = " ".join(keywords) if keywords else symbol
            
            logger.info(f"[AKShare] 使用复合关键词搜索: {search_query}")

            # 2. 调用AKShare提供器获取新闻
            raw_news_list = await self.provider.get_stock_news(
                symbol=symbol,
                limit=limit,
                query=search_query
            )
            
            if not raw_news_list:
                return []
            
            # 3. 质量门禁：基于关键词过滤相关性不足的新闻
            news_list = []
            if raw_news_list:
                for raw_news in raw_news_list:
                    # 优先获取标准字段名，也要适配 AKShare 可能返回的原始名
                    title = raw_news.get("title") or raw_news.get("新闻标题") or ""
                    content = raw_news.get("content") or raw_news.get("新闻内容") or raw_news.get("summary") or ""
                    
                    # 检查相关性：标题、内容或摘要必须包含至少一个 AI 联想词或原始代码
                    if not keywords or any(k.lower() in title.lower() or k.lower() in content.lower() for k in keywords):
                        normalized = self.normalize_news(raw_news)
                        news_list.append(normalized)
                    else:
                        logger.debug(f"[AKShare] ✂️ 过滤相关性不足的新闻: {title[:40]}...")
            
            logger.info(f"[AKShare] {symbol} 原始抓取 {len(raw_news_list) if raw_news_list else 0} 条，经过 AI 过滤后保留 {len(news_list)} 条")
            return news_list
            
        except Exception as e:
            logger.error(f"[AKShare] 获取新闻失败: {symbol} - {e}")
            raise
    
    def normalize_news(self, raw_news: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化AKShare新闻为统一格式
        
        Args:
            raw_news: AKShare原始新闻
            
        Returns:
            标准化的新闻字典
        """
        return create_standard_news_item(
            symbol=raw_news.get("symbol", ""),
            title=raw_news.get("title") or raw_news.get("新闻标题", ""),
            source=raw_news.get("source") or raw_news.get("文章来源", "AKShare"),
            summary=raw_news.get("summary") or raw_news.get("新闻内容", "")[:200],
            content=raw_news.get("content") or raw_news.get("新闻内容", ""),
            source_type="api",
            url=raw_news.get("url") or raw_news.get("新闻链接", ""),
            publish_time=raw_news.get("publish_time") or raw_news.get("发布时间") or datetime.utcnow(),
            sentiment=raw_news.get("sentiment", "neutral"),
            relevance_score=0.7,  # AKShare新闻相关性中等
            tags=raw_news.get("tags", [])
        )
