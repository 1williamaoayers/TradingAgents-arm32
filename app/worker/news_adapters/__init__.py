"""
新闻适配器包初始化
"""
from .base import NewsSourceAdapter, create_standard_news_item
from .scraper_adapter import ScraperAdapter

__all__ = [
    'NewsSourceAdapter',
    'create_standard_news_item',
    'ScraperAdapter',
]

