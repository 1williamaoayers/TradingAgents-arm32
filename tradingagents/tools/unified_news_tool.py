#!/usr/bin/env python3
import json
import requests
"""
统一新闻分析工具
整合A股、港股、美股等不同市场的新闻获取逻辑到一个工具函数中
让大模型只需要调用一个工具就能获取所有类型股票的新闻数据
"""

import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)


# ==================== 智能去重工具 ====================

def normalize_title(title: str) -> str:
    """
    标准化新闻标题，用于去重比较
    处理：数字格式差异、空格、标点符号等
    
    Args:
        title: 原始标题
        
    Returns:
        标准化后的标题
    """
    if not title:
        return ""
    
    # 1. 转小写
    normalized = title.lower()
    
    # 2. 移除所有空格
    normalized = re.sub(r'\s+', '', normalized)
    
    # 3. 标准化数字格式（1.00亿 -> 1亿，1,000 -> 1000）
    normalized = re.sub(r'\.0+', '', normalized)  # 1.00 -> 1
    normalized = re.sub(r',', '', normalized)      # 1,000 -> 1000
    
    # 4. 移除常见标点
    normalized = re.sub(r'[，。、！？：；""''【】\[\]()（）]', '', normalized)
    
    # 5. 移除来源标识（如 [证券时报]、【财联社】）
    normalized = re.sub(r'\[.*?\]', '', normalized)
    normalized = re.sub(r'【.*?】', '', normalized)
    
    return normalized


def is_similar_title(title1: str, title2: str, threshold: float = 0.8) -> bool:
    """
    判断两个标题是否相似（使用简单的字符重叠率）
    
    Args:
        title1: 标题1
        title2: 标题2
        threshold: 相似度阈值，默认0.8（80%相似就认为重复）
        
    Returns:
        是否相似
    """
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)
    
    if not norm1 or not norm2:
        return False
    
    # 完全相同
    if norm1 == norm2:
        return True
    
    # 一个包含另一个（子串匹配）
    if norm1 in norm2 or norm2 in norm1:
        return True
    
    # 字符重叠率计算
    set1 = set(norm1)
    set2 = set(norm2)
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    if union == 0:
        return False
    
    similarity = intersection / union
    return similarity >= threshold


def extract_date_from_title(title: str) -> str:
    """
    从标题中提取日期信息
    支持格式：12月15日、12-15、12/15、2024年12月15日等
    
    Args:
        title: 新闻标题
        
    Returns:
        提取到的日期字符串，如果没有日期则返回空字符串
    """
    if not title:
        return ""
    
    # 模式1: X月X日
    match = re.search(r'(\d{1,2})月(\d{1,2})日', title)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    
    # 模式2: X年X月X日
    match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', title)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    
    # 模式3: YYYY-MM-DD 或 MM-DD
    match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', title)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    
    match = re.search(r'(\d{1,2})-(\d{1,2})', title)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    
    return ""


class NewsDeduplicator:
    """
    🔥 终极新闻去重器
    
    特性：
    1. 日期敏感：不同日期的相似新闻不会被去重
    2. 保留最完整版本：相似时保留更长的标题
    3. 标准化处理：统一数字格式、去标点等
    """
    
    def __init__(self):
        # 存储格式: {normalized_title: (original_title, date)}
        self.seen_items = {}
        self.stats = {"total": 0, "duplicates": 0, "replaced": 0}
    
    def check_and_add(self, title: str, threshold: float = 0.75) -> bool:
        """
        🔥 终极去重逻辑
        
        Args:
            title: 待检查的标题
            threshold: 相似度阈值
            
        Returns:
            True = 应该保留（新标题或更完整版本）
            False = 应该跳过（重复且不如已有版本完整）
        """
        if not title or len(title.strip()) < 5:
            return False
        
        self.stats["total"] += 1
        
        # 1. 提取日期
        new_date = extract_date_from_title(title)
        normalized = normalize_title(title)
        
        # 2. 检查完全匹配（标准化后相同）
        if normalized in self.seen_items:
            old_title, old_date = self.seen_items[normalized]
            
            # 日期不同 = 不同事件，都保留
            if new_date and old_date and new_date != old_date:
                # 用不同的key存储（加日期后缀）
                self.seen_items[f"{normalized}_{new_date}"] = (title, new_date)
                return True
            
            # 日期相同或无日期，比较长度
            if len(title) > len(old_title):
                # 新标题更长，替换
                self.seen_items[normalized] = (title, new_date or old_date)
                self.stats["replaced"] += 1
                return True
            else:
                # 旧标题更长或相等，跳过
                self.stats["duplicates"] += 1
                return False
        
        # 3. 检查相似匹配
        for norm_key, (old_title, old_date) in list(self.seen_items.items()):
            if is_similar_title(title, old_title, threshold):
                # 日期不同 = 不同事件
                if new_date and old_date and new_date != old_date:
                    continue  # 不算重复，继续检查
                
                # 日期相同或无日期，比较长度
                if len(title) > len(old_title):
                    # 新标题更长，替换
                    del self.seen_items[norm_key]
                    self.seen_items[normalized] = (title, new_date or old_date)
                    self.stats["replaced"] += 1
                    return True
                else:
                    # 旧标题更长或相等，跳过
                    self.stats["duplicates"] += 1
                    return False
        
        # 4. 全新标题，添加
        self.seen_items[normalized] = (title, new_date)
        return True
    
    def get_stats(self) -> dict:
        """获取去重统计"""
        return {
            "total_checked": self.stats["total"],
            "duplicates_removed": self.stats["duplicates"],
            "replaced_with_longer": self.stats["replaced"],
            "unique_kept": len(self.seen_items)
        }

class UnifiedNewsAnalyzer:
    """统一新闻分析器，整合所有新闻获取逻辑"""
    
    def __init__(self, toolkit):
        """初始化统一新闻分析器
        
        Args:
            toolkit: 包含各种新闻获取工具的工具包
        """
        self.toolkit = toolkit
        
    def get_stock_news_unified(self, stock_code: str, max_news: int = 10, model_info: str = "") -> dict:
        """
        统一新闻获取接口
        根据股票代码自动识别股票类型并获取相应新闻
        
        Args:
            stock_code: 股票代码
            max_news: 最大新闻数量
            model_info: 当前使用的模型信息，用于特殊处理
            
        Returns:
            dict: 包含新闻内容和元数据的字典
        """
        logger.info(f"[统一新闻工具] 开始获取 {stock_code} 的新闻，模型: {model_info}")
        logger.info(f"[统一新闻工具] 🤖 当前模型信息: {model_info}")
        
        # 识别股票类型
        stock_type = self._identify_stock_type(stock_code)
        logger.info(f"[统一新闻工具] 股票类型: {stock_type}")
        
        # 根据股票类型调用相应的获取方法
        if stock_type == "A股":
            result_str = self._get_a_share_news(stock_code, max_news, model_info)
        elif stock_type == "港股":
            result_str = self._get_hk_share_news(stock_code, max_news, model_info)
        elif stock_type == "美股":
            result_str = self._get_us_share_news(stock_code, max_news, model_info)
        else:
            # 默认使用A股逻辑
            result_str = self._get_a_share_news(stock_code, max_news, model_info)
        
        # 🔍 构建“满血版”数据集：注入南向/北向资金流数据 (仅限A股/港股)
        fund_flow_str = ""
        if stock_type in ["A股", "港股"]:
            try:
                from tradingagents.dataflows.providers.china.akshare import get_akshare_provider
                provider = get_akshare_provider()
                # 使用同步版本的资金流获取
                fund_flow_str = provider.get_hsgt_fund_flow_sync(stock_code)
                
                if fund_flow_str and result_str:  # 确保两者都不为None
                    logger.info(f"[统一新闻工具] ✅ 成功注入资金流数据")
                    result_str = fund_flow_str + "\n\n" + result_str
            except Exception as e:
                logger.warning(f"[统一新闻工具] ⚠️ 资金流注入失败: {e}")

        # 🔍 添加详细的结果调试日志
        if result_str:
            logger.info(f"[统一新闻工具] 📊 满血版数据集构建完成，结果长度: {len(result_str)} 字符")
            logger.info(f"[统一新闻工具] 📋 返回结果预览 (前1000字符): {result_str[:1000]}")
        else:
            logger.warning("[统一新闻工具] ⚠️ result_str为None，可能所有新闻源都失败了")
        
        # 如果结果为空或过短，记录警告
        if not result_str or len(result_str.strip()) < 50:
            logger.warning(f"[统一新闻工具] ⚠️ 返回结果异常短或为空！")
            logger.warning(f"[统一新闻工具] 📝 完整结果内容: '{result_str}'")
        
        # 构造返回字典
        return {
            "status": "success" if result_str and len(result_str) > 50 else "warning",
            "content": result_str,
            "stock_type": stock_type,
            "ticker": stock_code,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _identify_stock_type(self, stock_code: str) -> str:
        """识别股票类型"""
        stock_code = stock_code.upper().strip()
        
        # A股判断
        if re.match(r'^(00|30|60|68)\d{4}$', stock_code):
            return "A股"
        elif re.match(r'^(SZ|SH)\d{6}$', stock_code):
            return "A股"
        
        # 港股判断
        elif re.match(r'^\d{4,5}\.HK$', stock_code):
            return "港股"
        elif re.match(r'^\d{4,5}$', stock_code) and len(stock_code) <= 5:
            return "港股"
        
        # 美股判断
        elif re.match(r'^[A-Z]{1,5}$', stock_code):
            return "美股"
        elif '.' in stock_code and not stock_code.endswith('.HK'):
            return "美股"
        
        # 默认按A股处理
        else:
            return "A股"
    
    def _search_news_with_serper(self, query: str, period: str = "qdr:w") -> str:
        """
        使用Serper API搜索新闻
        Args:
            query: 搜索关键词
            period: 时间范围，默认为过去一周 (qdr:w)，可选 qdr:d (一天), qdr:m (一月)
        """
        try:
            import os
            api_key = os.getenv("SERPER_API_KEY")
            if not api_key:
                return ""
                
            url = "https://google.serper.dev/search"
            headers = {
                'X-API-KEY': api_key,
                'Content-Type': 'application/json'
            }
            
            payload = json.dumps({
                "q": query,
                "tbs": period,
                "num": 10
            })
            
            response = requests.post(url, headers=headers, data=payload, timeout=10)
            if response.status_code != 200:
                return ""
                
            results = response.json().get('organic', [])
            if not results:
                return ""
                
            formatted = []
            for item in results:
                title = item.get('title', '')
                snippet = item.get('snippet', '')
                link = item.get('link', '')
                date = item.get('date', '')
                formatted.append(f"### {title}\n- **来源**: {link}\n- **时间**: {date}\n- **摘要**: {snippet}\n")
                
            return "\n".join(formatted)
        except Exception as e:
            logger.warning(f"[统一新闻工具] Serper搜索失败: {e}")
            return ""

    def _get_company_name_from_code(self, stock_code: str) -> str:
        """
        根据股票代码获取公司名称
        
        Args:
            stock_code: 股票代码
            
        Returns:
            str: 公司名称，如果无法获取则返回空字符串
        """
        # 简单的映射表（常见股票）
        stock_name_map = {
            '09618': '京东集团',
            '9618': '京东集团',
            'JD': '京东',
            '00700': '腾讯控股',
            '0700': '腾讯控股',
            'BABA': '阿里巴巴',
            '09988': '阿里巴巴',
            'AAPL': '苹果',
            'TSLA': '特斯拉',
            'NVDA': '英伟达',
            '000001': '平安银行',
            '600519': '贵州茅台',
        }
        
        # 标准化代码
        clean_code = stock_code.replace('.HK', '').replace('.SH', '').replace('.SZ', '')
        
        # 查找映射
        company_name = stock_name_map.get(clean_code, '')
        
        if company_name:
            logger.debug(f"[统一新闻工具] 股票代码 {stock_code} 映射到公司名称: {company_name}")
        else:
            logger.debug(f"[统一新闻工具] 股票代码 {stock_code} 未找到公司名称映射")
        
        return company_name

    def _get_news_from_database(self, stock_code: str, max_news: int = 10, company_name: str = "") -> str:
        """
        从数据库获取新闻（改进版：支持内容相关性查询）

        Args:
            stock_code: 股票代码
            max_news: 最大新闻数量
            company_name: 公司名称（用于内容匹配）

        Returns:
            str: 格式化的新闻内容，如果没有新闻则返回空字符串
        """
        try:
            from tradingagents.dataflows.cache.app_adapter import get_mongodb_client
            from datetime import timedelta

            # 🔧 确保 max_news 是整数（防止传入浮点数）
            max_news = int(max_news)

            client = get_mongodb_client()
            if not client:
                logger.warning(f"[统一新闻工具] 无法连接到MongoDB")
                return ""

            db = client.get_database('tradingagents')
            collection = db.stock_news

            # 标准化股票代码（去除后缀）
            clean_code = stock_code.replace('.SH', '').replace('.SZ', '').replace('.SS', '')\
                                   .replace('.XSHE', '').replace('.XSHG', '').replace('.HK', '')

            # 查询最近30天的新闻（扩大时间范围）
            thirty_days_ago = datetime.now() - timedelta(days=30)

            # 🔥 改进：构建关键词列表（支持内容相关性查询）
            keywords = [stock_code, clean_code]
            
            if company_name:
                # 添加公司名称相关关键词
                keywords.append(company_name)
                # 去除"集团"、"股份"等后缀
                clean_name = company_name.replace('集团', '').replace('股份', '').replace('有限公司', '')
                if clean_name != company_name:
                    keywords.append(clean_name)
                
                # 添加相关业务关键词（针对大公司）
                if clean_name:
                    keywords.extend([
                        f'{clean_name}物流',
                        f'{clean_name}零售',
                        f'{clean_name}科技'
                    ])
            
            # 构建正则表达式（不区分大小写）
            keyword_pattern = '|'.join([k for k in keywords if k])
            
            logger.info(f"[统一新闻工具] 🔍 查询关键词: {keywords[:5]}...")  # 只显示前5个

            # 🔥 改进：融合多个查询条件的结果，使用标题去重
            news_items = []
            seen_titles = set()  # 用于去重
            
            # 定义查询条件（按优先级排序）
            specific_queries = [
                # 优先级1: 精确匹配symbol + 时间范围（最相关）
                {'symbol': clean_code, 'publish_time': {'$gte': thirty_days_ago}},
                {'symbol': stock_code, 'publish_time': {'$gte': thirty_days_ago}},
                
                # 优先级2: 标题包含关键词 + 时间范围
                {'title': {'$regex': keyword_pattern, '$options': 'i'}, 'publish_time': {'$gte': thirty_days_ago}},
                
                # 优先级3: 内容包含关键词 + 时间范围
                {'content': {'$regex': keyword_pattern, '$options': 'i'}, 'publish_time': {'$gte': thirty_days_ago}},
                
                # 优先级4: 精确匹配symbol（不限时间，历史新闻）
                {'symbol': clean_code},
                {'symbol': stock_code},
            ]
            
            # 🔥 融合查询：遍历所有条件，收集所有结果并去重
            for query in specific_queries:
                if len(news_items) >= max_news:
                    break  # 已经够了，停止查询
                    
                try:
                    remaining = max_news - len(news_items)
                    cursor = collection.find(query).sort('publish_time', -1).limit(remaining * 2)  # 多取一些用于去重
                    
                    for news in cursor:
                        title = news.get('title', '')
                        if title and title not in seen_titles:
                            seen_titles.add(title)
                            news_items.append(news)
                            if len(news_items) >= max_news:
                                break
                except Exception as e:
                    logger.debug(f"[统一新闻工具] 查询条件失败: {e}")
                    continue
            
            logger.info(f"[统一新闻工具] 📊 融合查询获得 {len(news_items)} 条新闻（已去重）")
            
            # 第二步：实时获取AKShare新闻（如果专属新闻不足max_news条）
            if len(news_items) < max_news:
                try:
                    logger.info(f"[统一新闻工具] 📡 专属新闻不足，尝试实时获取AKShare新闻...")
                    
                    # 动态导入AKShare适配器
                    import asyncio
                    from app.worker.news_adapters.akshare_adapter import AKShareAdapter
                    
                    # 创建适配器并获取实时新闻
                    akshare = AKShareAdapter()
                    
                    # 判断是否需要初始化
                    loop = None
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    # 初始化并获取新闻
                    if not loop.is_running():
                        loop.run_until_complete(akshare.initialize())
                        realtime_limit = min(10, max_news - len(news_items))  # 最多获取10条实时新闻
                        realtime_news = loop.run_until_complete(akshare.get_news(stock_code, limit=realtime_limit))
                    else:
                        # 如果事件循环已在运行，使用同步方式
                        import nest_asyncio
                        nest_asyncio.apply()
                        loop.run_until_complete(akshare.initialize())
                        realtime_limit = min(10, max_news - len(news_items))
                        realtime_news = loop.run_until_complete(akshare.get_news(stock_code, limit=realtime_limit))
                    
                    if realtime_news:
                        # 去重后添加
                        added_count = 0
                        for news in realtime_news:
                            title = news.get('title', '')
                            if title and title not in seen_titles:
                                seen_titles.add(title)
                                news_items.append(news)
                                added_count += 1
                        logger.info(f"[统一新闻工具] 🔥 实时获取 {added_count} 条AKShare新闻（去重后）")
                    else:
                        logger.info(f"[统一新闻工具] ⚠️ 实时AKShare未返回新闻")
                        
                except Exception as e:
                    logger.warning(f"[统一新闻工具] ⚠️ 实时获取AKShare新闻失败: {e}")
            
            # 第三步：补充RSS通用新闻（如果仍然不足max_news条）
            if len(news_items) < max_news:
                rss_limit = max_news - len(news_items)  # 计算还需要多少条
                rss_query = {'symbol': 'GENERAL', 'source': 'RSS', 'publish_time': {'$gte': thirty_days_ago}}
                rss_cursor = collection.find(rss_query).sort('publish_time', -1).limit(rss_limit * 2)
                
                added_count = 0
                for news in rss_cursor:
                    title = news.get('title', '')
                    if title and title not in seen_titles:
                        seen_titles.add(title)
                        news_items.append(news)
                        added_count += 1
                        if len(news_items) >= max_news:
                            break
                
                if added_count > 0:
                    logger.info(f"[统一新闻工具] 📰 补充 {added_count} 条RSS通用新闻")
            
            logger.info(f"[统一新闻工具] 📊 最终获得 {len(news_items)} 条新闻")

            if not news_items:
                logger.info(f"[统一新闻工具] 数据库中没有找到 {stock_code} 或 {company_name} 的相关新闻")
                return ""

            # 格式化新闻
            report = f"# {stock_code} 最新新闻 (数据库缓存)\n\n"
            report += f"📅 查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            report += f"📊 新闻数量: {len(news_items)} 条\n\n"

            for i, news in enumerate(news_items, 1):
                title = news.get('title', '无标题')
                content = news.get('content', '') or news.get('summary', '')
                source = news.get('source', '未知来源')
                publish_time = news.get('publish_time', datetime.now())
                sentiment = news.get('sentiment', 'neutral')

                # 情绪图标
                sentiment_icon = {
                    'positive': '📈',
                    'negative': '📉',
                    'neutral': '➖'
                }.get(sentiment, '➖')

                report += f"## {i}. {sentiment_icon} {title}\n\n"
                report += f"**来源**: {source} | **时间**: {publish_time.strftime('%Y-%m-%d %H:%M') if isinstance(publish_time, datetime) else publish_time}\n"
                report += f"**情绪**: {sentiment}\n\n"

                if content:
                    # 限制内容长度
                    content_preview = content[:500] + '...' if len(content) > 500 else content
                    report += f"{content_preview}\n\n"

                report += "---\n\n"

            logger.info(f"[统一新闻工具] ✅ 成功从数据库获取并格式化 {len(news_items)} 条新闻")
            return report

        except Exception as e:
            logger.error(f"[统一新闻工具] 从数据库获取新闻失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return ""

    def _sync_news_from_akshare(self, stock_code: str, max_news: int = 10) -> bool:
        """
        从AKShare同步新闻到数据库（同步方法）
        使用同步的数据库客户端和新线程中的事件循环，避免事件循环冲突

        Args:
            stock_code: 股票代码
            max_news: 最大新闻数量

        Returns:
            bool: 是否同步成功
        """
        try:
            import asyncio
            import concurrent.futures

            # 标准化股票代码（去除后缀）
            clean_code = stock_code.replace('.SH', '').replace('.SZ', '').replace('.SS', '')\
                                   .replace('.XSHE', '').replace('.XSHG', '').replace('.HK', '')

            logger.info(f"[统一新闻工具] 🔄 开始同步 {clean_code} 的新闻...")

            # 🔥 在新线程中运行，使用同步数据库客户端
            def run_sync_in_new_thread():
                """在新线程中创建新的事件循环并运行同步任务"""
                # 创建新的事件循环
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)

                try:
                    # 定义异步获取新闻任务
                    async def get_news_task():
                        try:
                            # 动态导入 AKShare provider（正确的导入路径）
                            from tradingagents.dataflows.providers.china.akshare import AKShareProvider

                            # 创建 provider 实例
                            provider = AKShareProvider()

                            # 调用 provider 获取新闻
                            news_data = await provider.get_stock_news(
                                symbol=clean_code,
                                limit=max_news
                            )

                            return news_data

                        except Exception as e:
                            logger.error(f"[统一新闻工具] ❌ 获取新闻失败: {e}")
                            import traceback
                            logger.error(traceback.format_exc())
                            return None

                    # 在新的事件循环中获取新闻
                    news_data = new_loop.run_until_complete(get_news_task())

                    if not news_data:
                        logger.warning(f"[统一新闻工具] ⚠️ 未获取到新闻数据")
                        return False

                    logger.info(f"[统一新闻工具] 📥 获取到 {len(news_data)} 条新闻")

                    # 🔥 使用同步方法保存到数据库（不依赖事件循环）
                    from app.services.news_data_service import NewsDataService

                    news_service = NewsDataService()
                    saved_count = news_service.save_news_data_sync(
                        news_data=news_data,
                        data_source="akshare",
                        market="CN"
                    )

                    logger.info(f"[统一新闻工具] ✅ 同步成功: {saved_count} 条新闻")
                    return saved_count > 0

                finally:
                    # 清理事件循环
                    new_loop.close()

            # 在线程池中执行
            logger.info(f"[统一新闻工具] 在新线程中运行同步任务，避免事件循环冲突")
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_sync_in_new_thread)
                result = future.result(timeout=30)  # 30秒超时
                return result

        except concurrent.futures.TimeoutError:
            logger.error(f"[统一新闻工具] ❌ 同步新闻超时（30秒）")
            return False
        except Exception as e:
            logger.error(f"[统一新闻工具] ❌ 同步新闻失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def _get_a_share_news(self, stock_code: str, max_news: int, model_info: str = "") -> str:
        """获取A股新闻"""
        logger.info(f"[统一新闻工具] 获取A股 {stock_code} 新闻")

        # 获取当前日期
        curr_date = datetime.now().strftime("%Y-%m-%d")

        # 优先级0: 从数据库获取新闻（最高优先级）
        try:
            logger.info(f"[统一新闻工具] 🔍 优先从数据库获取 {stock_code} 的新闻...")
            # 获取公司名称用于内容匹配
            company_name = self._get_company_name_from_code(stock_code)
            db_news = self._get_news_from_database(stock_code, max_news, company_name)
            if db_news:
                logger.info(f"[统一新闻工具] ✅ 数据库新闻获取成功: {len(db_news)} 字符")
                return self._format_news_result(db_news, "数据库缓存", model_info)
            else:
                logger.info(f"[统一新闻工具] ⚠️ 数据库中没有 {stock_code} 的新闻，尝试同步...")

                # 🔥 数据库没有数据时，调用同步服务同步新闻
                try:
                    logger.info(f"[统一新闻工具] 📡 调用同步服务同步 {stock_code} 的新闻...")
                    synced_news = self._sync_news_from_akshare(stock_code, max_news)

                    if synced_news:
                        logger.info(f"[统一新闻工具] ✅ 同步成功，重新从数据库获取...")
                        # 重新从数据库获取
                        company_name = self._get_company_name_from_code(stock_code)
                        db_news = self._get_news_from_database(stock_code, max_news, company_name)
                        if db_news:
                            logger.info(f"[统一新闻工具] ✅ 同步后数据库新闻获取成功: {len(db_news)} 字符")
                            return self._format_news_result(db_news, "数据库缓存(新同步)", model_info)
                    else:
                        logger.warning(f"[统一新闻工具] ⚠️ 同步服务未返回新闻数据")

                except Exception as sync_error:
                    logger.warning(f"[统一新闻工具] ⚠️ 同步服务调用失败: {sync_error}")

                logger.info(f"[统一新闻工具] ⚠️ 同步后仍无数据，尝试其他数据源...")
        except Exception as e:
            logger.warning(f"[统一新闻工具] 数据库新闻获取失败: {e}")

        # 优先级1: 东方财富实时新闻
        try:
            if hasattr(self.toolkit, 'get_realtime_stock_news'):
                logger.info(f"[统一新闻工具] 尝试东方财富实时新闻...")
                # 使用LangChain工具的正确调用方式：.invoke()方法和字典参数
                result = self.toolkit.get_realtime_stock_news.invoke({"ticker": stock_code, "curr_date": curr_date})
                
                # 🔍 详细记录东方财富返回的内容
                logger.info(f"[统一新闻工具] 📊 东方财富返回内容长度: {len(result) if result else 0} 字符")
                logger.info(f"[统一新闻工具] 📋 东方财富返回内容预览 (前500字符): {result[:500] if result else 'None'}")
                
                if result and len(result.strip()) > 100:
                    logger.info(f"[统一新闻工具] ✅ 东方财富新闻获取成功: {len(result)} 字符")
                    return self._format_news_result(result, "东方财富实时新闻", model_info)
                else:
                    logger.warning(f"[统一新闻工具] ⚠️ 东方财富新闻内容过短或为空")
        except Exception as e:
            logger.warning(f"[统一新闻工具] 东方财富新闻获取失败: {e}")
        
        # 优先级2: Google新闻（优先使用Serper API，回退到普通爬虫）
        try:
            logger.info(f"[统一新闻工具] 尝试Google新闻 (Serper API)...")
            query = f"{stock_code} 股票 新闻 财报"
            
            # 1. 尝试使用 Serper API
            serper_result = self._search_news_with_serper(query, period="qdr:w")
            if serper_result and len(serper_result) > 50:
                logger.info(f"[统一新闻工具] ✅ Serper新闻获取成功: {len(serper_result)} 字符")
                return self._format_news_result(serper_result, "Google/Serper新闻", model_info)
            
            # 2. 回退到普通爬虫
            if hasattr(self.toolkit, 'get_google_news'):
                logger.info(f"[统一新闻工具] Serper无结果，尝试Google新闻爬虫...")
                # 使用LangChain工具的正确调用方式：.invoke()方法和字典参数
                result = self.toolkit.get_google_news.invoke({"query": query, "curr_date": curr_date})
                if result and len(result.strip()) > 50:
                    logger.info(f"[统一新闻工具] ✅ Google新闻爬虫获取成功: {len(result)} 字符")
                    return self._format_news_result(result, "Google新闻(爬虫)", model_info)
        except Exception as e:
            logger.warning(f"[统一新闻工具] Google新闻获取失败: {e}")
        
        # 优先级3: OpenAI全球新闻
        try:
            if hasattr(self.toolkit, 'get_global_news_openai'):
                logger.info(f"[统一新闻工具] 尝试OpenAI全球新闻...")
                # 使用LangChain工具的正确调用方式：.invoke()方法和字典参数
                result = self.toolkit.get_global_news_openai.invoke({"curr_date": curr_date})
                if result and len(result.strip()) > 50:
                    logger.info(f"[统一新闻工具] ✅ OpenAI新闻获取成功: {len(result)} 字符")
                    return self._format_news_result(result, "OpenAI全球新闻", model_info)
        except Exception as e:
            logger.warning(f"[统一新闻工具] OpenAI新闻获取失败: {e}")
        
        return "❌ 无法获取A股新闻数据，所有新闻源均不可用"
    
    def _get_hk_share_news(self, stock_code: str, max_news: int, model_info: str = "") -> str:
        """
        获取港股新闻 - 🔥 并行融合策略
        同时从多个数据源获取新闻，融合去重后返回
        """
        logger.info(f"[统一新闻工具] 🚀 获取港股 {stock_code} 新闻 (并行融合模式)")
        
        # 获取当前日期
        curr_date = datetime.now().strftime("%Y-%m-%d")
        company_name = self._get_company_name_from_code(stock_code)
        
        # 🔥 并行收集所有数据源的新闻
        # 🔥 新顺序：实时数据优先，数据库缓存放最后（避免旧数据显示在前面）
        all_news = []  # 存储标题和来源的tuple用于去重
        all_content_parts = []  # 存储格式化后的内容片段
        sources_used = []  # 记录成功使用的数据源
        
        # ==================== 数据源1: 东方财富个股新闻（最新）====================
        try:
            logger.info(f"[统一新闻工具] 📰 [1/6] 从东方财富获取最新个股新闻...")
            from tradingagents.dataflows.providers.china.akshare import get_akshare_provider
            clean_code = stock_code.replace('.HK', '').replace('.hk', '')
            provider = get_akshare_provider()
            news_df = provider.stock_news_em(symbol=clean_code)
            
            if news_df is not None and not news_df.empty:
                news_content = f"=== 📰 东方财富个股新闻（最新）===\n\n"
                news_count = min(10, len(news_df))
                
                for idx, row in news_df.head(news_count).iterrows():
                    title = row.get('标题', '无标题')
                    time_val = row.get('发布时间', '')
                    content = row.get('内容', '')
                    content_preview = content[:200] + '...' if len(content) > 200 else content
                    news_content += f"### {title}\n- **时间**: {time_val}\n- **内容**: {content_preview}\n\n"
                
                logger.info(f"[统一新闻工具] ✅ 东方财富: {news_count}条, {len(news_content)} 字符")
                all_content_parts.append(("东方财富个股新闻", news_content))
                sources_used.append("东方财富")
        except Exception as e:
            logger.warning(f"[统一新闻工具] ⚠️ 东方财富获取失败: {e}")
        
        # ==================== 数据源7: Playwright爬虫 (补全缺失代码) ====================
        try:
            logger.info(f"[统一新闻工具] 🕷️ [7/7] 调用 Playwright 爬虫获取深度新闻...")
            # 动态导入防止循环引用
            from app.worker.news_adapters.scraper_adapter import ScraperAdapter
            import asyncio
            
            # 使用现有的 loop 或者创建新的
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            # 初始化适配器 (API地址由环境变量或默认值处理)
            adapter = ScraperAdapter()
            
            # 使用公司名作为关键词 (比代码更准确)
            search_keyword = company_name if company_name else stock_code
            logger.info(f"[统一新闻工具] 🕷️ 爬虫关键词: {search_keyword}")
            
            # 异步调用获取新闻
            if not loop.is_running():
                scraper_news = loop.run_until_complete(adapter.get_news(search_keyword, limit=10))
            else:
                import nest_asyncio
                nest_asyncio.apply()
                scraper_news = loop.run_until_complete(adapter.get_news(search_keyword, limit=10))
                
            if scraper_news:
                scraper_content = f"=== 🕷️ Playwright爬虫新闻 ({search_keyword}) ===\n\n"
                
                for news in scraper_news:
                    title = news.get('title', '')
                    source = news.get('source', 'Scraper')
                    summary = news.get('summary', '')[:200]
                    url = news.get('url', '')
                    scraper_content += f"### {title}\n- **来源**: {source}\n- **摘要**: {summary}\n- **链接**: {url}\n\n"
                    
                logger.info(f"[统一新闻工具] ✅ Playwright爬虫: {len(scraper_news)}条, {len(scraper_content)} 字符")
                all_content_parts.append(("Playwright爬虫", scraper_content))
                sources_used.append("Playwright爬虫")
            else:
                 logger.info(f"[统一新闻工具] 🕷️ Playwright爬虫未返回数据")
                 
        except Exception as e:
            logger.warning(f"[统一新闻工具] ⚠️ Playwright爬虫调用失败: {e}")

        # ==================== 数据源2: AKShare多源财经快讯（实时）====================
        try:
            logger.info(f"[统一新闻工具] 📡 [2/6] 从AKShare聚合多源快讯...")
            from tradingagents.dataflows.providers.china.akshare import get_akshare_provider
            provider = get_akshare_provider()
            multi_news = provider.get_multi_source_news(limit_per_source=5)
            if multi_news and len(multi_news) > 200:
                logger.info(f"[统一新闻工具] ✅ AKShare多源快讯: {len(multi_news)} 字符")
                all_content_parts.append(("AKShare多源快讯", multi_news))
                sources_used.append("多源快讯")
        except Exception as e:
            logger.warning(f"[统一新闻工具] ⚠️ AKShare多源快讯获取失败: {e}")
        
        # ==================== 数据源3: Serper实时搜索 ====================
        try:
            logger.info(f"[统一新闻工具] 🔍 [3/6] 从Serper获取实时新闻...")
            query = f"{stock_code} {company_name or '港股'} 新闻 财报 分析"
            serper_result = self._search_news_with_serper(query, period="qdr:d")  # 过去1天
            if serper_result and len(serper_result) > 100:
                logger.info(f"[统一新闻工具] ✅ Serper: {len(serper_result)} 字符")
                all_content_parts.append(("Serper实时搜索", serper_result))
                sources_used.append("Serper")
        except Exception as e:
            logger.warning(f"[统一新闻工具] ⚠️ Serper获取失败: {e}")
        
        # ==================== 数据源4: Alpha Vantage个股新闻（仅美股）====================
        # Alpha Vantage只支持美股格式，港股/A股会报错，直接跳过节省时间
        is_hk_stock = '.HK' in stock_code.upper() or '.hk' in stock_code
        is_a_stock = stock_code.isdigit() and len(stock_code) == 6
        
        if is_hk_stock or is_a_stock:
            logger.info(f"[统一新闻工具] ⏭️ [4/6] Alpha Vantage跳过（仅支持美股，当前: {'港股' if is_hk_stock else 'A股'}）")
        else:
            try:
                logger.info(f"[统一新闻工具] 📈 [4/6] 从Alpha Vantage获取美股新闻...")
                from tradingagents.tools.alpha_vantage_news import get_alpha_vantage_news, format_alpha_vantage_news
                av_news = get_alpha_vantage_news(ticker=stock_code, limit=10)
                if av_news and len(av_news) > 0:
                    formatted = format_alpha_vantage_news(av_news, stock_code)
                    logger.info(f"[统一新闻工具] ✅ Alpha Vantage: {len(av_news)}条, {len(formatted)} 字符")
                    all_content_parts.append(("Alpha Vantage", formatted))
                    sources_used.append("Alpha Vantage")
            except Exception as e:
                logger.warning(f"[统一新闻工具] ⚠️ Alpha Vantage获取失败: {e}")
        
        # ==================== 数据源5: RSS新闻源 ====================
        try:
            logger.info(f"[统一新闻工具] 📡 [5/6] 从RSS源获取新闻...")
            from app.worker.news_adapters.rss_adapter import RSSAdapter
            import asyncio
            
            rss_adapter = RSSAdapter()
            
            # 获取事件循环
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # 初始化并获取新闻
            if not loop.is_running():
                rss_news = loop.run_until_complete(rss_adapter.get_news(symbol=stock_code, limit=15))
            else:
                import nest_asyncio
                nest_asyncio.apply()
                rss_news = loop.run_until_complete(rss_adapter.get_news(symbol=stock_code, limit=15))
            
            if rss_news and len(rss_news) > 0:
                rss_content = f"=== 📻 RSS财经快讯 ===\n\n"
                rss_content += f"📊 来源: 金十数据、财联社、格隆汇、华尔街见闻、Google News\n\n"
                
                for news in rss_news[:15]:
                    title = news.get('title', '')
                    source = news.get('source', 'RSS')
                    match_type = news.get('match_type', '')
                    rss_content += f"- **{title}** [{source}] ({match_type})\n"
                
                logger.info(f"[统一新闻工具] ✅ RSS新闻: {len(rss_news)}条, {len(rss_content)} 字符")
                all_content_parts.append(("RSS新闻", rss_content))
                sources_used.append("RSS")
        except Exception as e:
            logger.warning(f"[统一新闻工具] ⚠️ RSS新闻获取失败: {e}")
        
        # ==================== 数据源6: 数据库缓存（补充历史新闻）====================
        try:
            logger.info(f"[统一新闻工具] 📦 [6/6] 从数据库获取历史新闻...")
            db_news = self._get_news_from_database(stock_code, 15, company_name)  # 取15条
            if db_news and len(db_news) > 100:
                logger.info(f"[统一新闻工具] ✅ 数据库缓存: {len(db_news)} 字符")
                all_content_parts.append(("数据库历史", db_news))
                sources_used.append("数据库历史")
        except Exception as e:
            logger.warning(f"[统一新闻工具] ⚠️ 数据库获取失败: {e}")
        
        # ==================== 融合所有数据源 ====================
        if not all_content_parts:
            logger.error(f"[统一新闻工具] ❌ 所有数据源均失败！")
            return "❌ 无法获取港股新闻数据，所有新闻源均不可用"
        
        # 🔥 智能去重：跨数据源去重
        deduplicator = NewsDeduplicator()
        deduplicated_parts = []
        total_before = 0
        total_after = 0
        
        for source_name, content in all_content_parts:
            # 提取内容中的所有标题行
            lines = content.split('\n')
            deduplicated_lines = []
            
            for line in lines:
                # 检测标题行（以##、###开头或包含**粗体**）
                is_title_line = False
                title_to_check = ""
                
                if line.strip().startswith('##') or line.strip().startswith('###'):
                    is_title_line = True
                    # 提取标题内容
                    title_to_check = re.sub(r'^#+\s*\d*\.\s*[📈📉➖📰📌📻]*\s*', '', line.strip())
                elif '**' in line and line.strip().startswith('-'):
                    is_title_line = True
                    # 提取**内容**
                    match = re.search(r'\*\*(.+?)\*\*', line)
                    if match:
                        title_to_check = match.group(1)
                
                if is_title_line and title_to_check:
                    total_before += 1
                    # 使用智能去重判断
                    if deduplicator.check_and_add(title_to_check, threshold=0.75):
                        deduplicated_lines.append(line)
                        total_after += 1
                    else:
                        # 重复的标题，跳过这一行
                        logger.debug(f"[去重] 跳过重复标题: {title_to_check[:30]}...")
                else:
                    # 非标题行，直接保留
                    deduplicated_lines.append(line)
            
            # 重建内容
            deduplicated_content = '\n'.join(deduplicated_lines)
            if deduplicated_content.strip():
                deduplicated_parts.append((source_name, deduplicated_content))
        
        # 计算去重统计
        duplicates_removed = total_before - total_after
        if duplicates_removed > 0:
            logger.info(f"[统一新闻工具] 🔄 智能去重: {duplicates_removed} 条重复新闻已移除 (原{total_before}条 → {total_after}条)")
        
        # 构建融合报告
        total_chars = sum(len(content) for _, content in deduplicated_parts)
        report = f"# {stock_code} 综合新闻报告 (多源融合+智能去重)\n\n"
        report += f"📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"📊 数据来源: {', '.join(sources_used)} ({len(sources_used)}个)\n"
        report += f"📏 总数据量: {total_chars} 字符\n"
        if duplicates_removed > 0:
            report += f"🔄 去重统计: {duplicates_removed} 条重复已移除\n"
        report += "\n---\n\n"
        
        # 按数据源分组输出
        for source_name, content in deduplicated_parts:
            report += f"\n## 📌 来源: {source_name}\n\n"
            report += content
            report += "\n---\n"
        
        logger.info(f"[统一新闻工具] 🎉 融合完成: {len(sources_used)}个数据源, {len(report)} 字符, 去重{duplicates_removed}条")
        
        return self._format_news_result(report, f"多源融合({','.join(sources_used)})", model_info)
    
    def get_stock_sentiment_unified(
        self,
        ticker: str,
        curr_date: str
    ) -> dict:
        """
        统一的股票情绪分析工具
        自动识别股票类型（A股、港股、美股）并调用相应的情绪数据源
        对于A股和港股，使用Serper API抓取雪球和股吧的真实散户评论

        Args:
            ticker: 股票代码（如：000001、0700.HK、AAPL）
            curr_date: 当前日期（格式：YYYY-MM-DD）

        Returns:
            dict: 包含情绪分析报告和元数据的字典
        """
        logger.info(f"😊 [统一情绪工具] 分析股票: {ticker}")

        try:
            from tradingagents.utils.stock_utils import StockUtils

            # 自动识别股票类型
            market_info = StockUtils.get_market_info(ticker)
            is_china = market_info['is_china']
            is_hk = market_info['is_hk']
            is_us = market_info['is_us']

            logger.info(f"😊 [统一情绪工具] 股票类型: {market_info['market_name']}")

            result_data = []
            
            # 初始化默认返回字典
            response_dict = {
                "ticker": ticker,
                "stock_type": market_info['market_name'],
                "date": curr_date,
                "sentiment": "Neutral",
                "score": 0.5,
                "summary": "分析中...",
                "confidence": "low",
                "content": ""
            }

            if is_china or is_hk:
                # 中国A股和港股：使用Serper API搜索雪球和股吧
                logger.info(f"🇨🇳🇭🇰 [统一情绪工具] 使用Serper搜索中文市场情绪...")
                
                try:
                    import requests
                    import os
                    import re
                    
                    serper_api_key = os.getenv("SERPER_API_KEY")
                    if not serper_api_key:
                        raise ValueError("未配置SERPER_API_KEY")
                        
                    # 处理股票名称
                    clean_ticker = ticker.replace('.SH', '').replace('.SZ', '').replace('.SS', '').replace('.HK', '')
                    stock_name = market_info.get('name', '').replace('港股', '').replace('A股', '')
                    
                    # 【安全锁】使用局部变量，默认为 Ticker，防止查库失败导致变量缺失
                    real_name = clean_ticker
                    
                    # 尝试从数据库获取真实公司名
                    try:
                        # 【关键】局部引用，防止 Circular Import 导致全站崩溃
                        from tradingagents.dataflows.interface import get_stock_name_by_ticker
                        
                        # 尝试查询
                        name_from_db = get_stock_name_by_ticker(clean_ticker)
                        if name_from_db:
                            real_name = name_from_db
                            logger.info(f"[统一情绪工具] ✅ 从数据库获取到公司名: {real_name}")
                        else:
                            logger.info(f"[统一情绪工具] ⚠️ 未在数据库中找到 {clean_ticker} 的公司名，使用代码: {real_name}")
                    except Exception as e:
                        # 【关键】静默失败：如有任何报错，直接忽略，仅打印警告，保证程序继续运行
                        logger.warning(f"[统一情绪工具] ⚠️ 从数据库获取公司名失败，使用股票代码: {clean_ticker}，错误: {e}")
                        real_name = clean_ticker
                    
                    # 使用 real_name 替代原来的 stock_name 变量
                    stock_name = real_name
                    
                    if not stock_name or stock_name == ticker:
                        # 尝试获取中文名称
                        try:
                            if is_hk:
                                from tradingagents.dataflows.interface import get_hk_stock_info_unified
                                info = get_hk_stock_info_unified(ticker)
                            else:
                                from tradingagents.dataflows.interface import get_china_stock_info_unified
                                info = get_china_stock_info_unified(ticker)
                            
                            if isinstance(info, dict) and 'name' in info:
                                stock_name = info['name']
                        except:
                            pass
                    
                    # 再次清理名称 (防止带有"港股"前缀)
                    if stock_name:
                        stock_name = stock_name.replace('港股', '').replace('A股', '')
                        # 去除常见的后缀和冗余词 (如：京东集团-SW -> 京东)
                        # 1. 先进行NFKC标准化，将全角字符转为半角
                        import unicodedata
                        stock_name = unicodedata.normalize('NFKC', stock_name)
                        # 2. 去除集团、股份等后缀，以及 -SW, -W 等后缀
                        stock_name = re.sub(r'(集团|股份|有限公司|－.*|-.*|\(.*\)|（.*）)', '', stock_name)
                        stock_name = stock_name.strip()
                    
                    # 构造优化的搜索查询 (全网搜索，更宽松的关键词)
                    # 策略：使用公司名+情绪相关关键词，不限定特定网站
                    search_queries = []
                    
                    # 第一优先级：公司名 + 投资讨论关键词 (全网)
                    if stock_name and stock_name != ticker:
                        search_queries.append(f'{stock_name} 投资 分析 讨论')
                        search_queries.append(f'{stock_name} 股票 观点 评论')
                    
                    # 第二优先级：股票代码 + 关键词
                    search_queries.append(f'{clean_ticker} 股票 分析 观点')
                    
                    # 第三优先级：公司名 + 雪球/股吧 (作为fallback)
                    if stock_name and stock_name != ticker:
                        search_queries.append(f'{stock_name} site:xueqiu.com OR site:guba.eastmoney.com')
                    
                    logger.info(f"🔍 [Serper] 准备执行 {len(search_queries)} 个搜索策略")
                    
                    url = "https://google.serper.dev/search"
                    headers = {
                        'X-API-KEY': serper_api_key,
                        'Content-Type': 'application/json'
                    }
                    
                    def perform_search(query, time_range="qdr:w"):
                        """执行搜索，默认过去一周"""
                        payload = json.dumps({
                            "q": query,
                            "tbs": time_range,
                            "num": 15
                        })
                        response = requests.request("POST", url, headers=headers, data=payload, timeout=10)
                        return response.json().get('organic', [])
                    
                    organic_results = []
                    successful_query = None
                    
                    # 依次尝试各个查询策略
                    for query in search_queries:
                        logger.info(f"🔍 [Serper] 尝试查询: {query}")
                        results = perform_search(query)
                        if results:
                            organic_results = results
                            successful_query = query
                            logger.info(f"✅ [Serper] 查询成功，获取 {len(results)} 条结果")
                            break
                        else:
                            logger.warning(f"⚠️ [Serper] 查询无结果: {query}")
                    
                    # 如果所有策略都失败，尝试更宽松的查询 (过去一个月)
                    if not organic_results and stock_name:
                        logger.warning(f"⚠️ [Serper] 所有策略失败，尝试更宽松查询 (过去一个月)")
                        fallback_query = f'{stock_name} 股票'
                        organic_results = perform_search(fallback_query, "qdr:m")
                        if organic_results:
                            successful_query = fallback_query
                            logger.info(f"✅ [Serper] 宽松查询成功，获取 {len(organic_results)} 条结果")
                    
                    if organic_results:
                        discussions = []
                        for item in organic_results:
                            title = item.get('title', '')
                            snippet = item.get('snippet', '')
                            source = item.get('link', '')
                            
                            # 智能识别来源平台
                            platform = "网络"
                            if "xueqiu.com" in source:
                                platform = "雪球"
                            elif "eastmoney.com" in source or "guba" in source:
                                platform = "股吧"
                            elif "sina.com" in source:
                                platform = "新浪"
                            elif "163.com" in source:
                                platform = "网易"
                            elif "qq.com" in source:
                                platform = "腾讯"
                            elif "baidu.com" in source or "baijiahao" in source:
                                platform = "百度"
                            elif "zhihu.com" in source:
                                platform = "知乎"
                            elif "toutiao.com" in source:
                                platform = "头条"
                            elif "weibo.com" in source:
                                platform = "微博"
                            elif "36kr.com" in source:
                                platform = "36氪"
                            elif "wallstreetcn.com" in source:
                                platform = "华尔街见闻"
                            elif "cls.cn" in source:
                                platform = "财联社"
                                
                            discussions.append(f"- [{platform}] **{title}**: {snippet}")
                        
                        discussion_text = "\n".join(discussions)
                        
                        sentiment_summary = f"""
## 市场情绪与投资者观点分析 (Serper全网搜索)

**股票**: {ticker} ({stock_name})
**分析日期**: {curr_date}
**搜索策略**: {successful_query}
**结果数量**: {len(organic_results)} 条

### 投资者讨论与观点
{discussion_text}

### 情绪分析要求
请基于上述搜索结果，分析：
1. 投资者整体情绪倾向（乐观/悲观/中性）
2. 主要关注点和讨论话题
3. 潜在的风险点或利好因素
"""
                        result_data.append(sentiment_summary)
                        response_dict["content"] = sentiment_summary
                        response_dict["status"] = "success"
                        response_dict["source"] = "Serper/Google全网搜索"
                        logger.info(f"✅ [Serper] 成功获取 {len(organic_results)} 条投资者讨论")
                    else:
                        # 🔥 降级方案：Serper 无结果时，调用新闻工具补位
                        logger.warning(f"⚠️ [Serper] 搜不到社交媒体数据，尝试调用新闻工具补位...")
                        
                        # 调用 get_stock_news_unified 获取最新新闻
                        news_res = self.get_stock_news_unified(ticker, max_news=20)
                        news_content = news_res.get("content", "")
                        
                        if news_content and "无法获取" not in news_content:
                            sentiment_summary = f"""
## 市场情绪与舆情分析 (由于社交媒体数据受限，已切换至深度新闻舆情模式)

**股票**: {ticker} ({stock_name})
**分析日期**: {curr_date}
**补位源**: 核心公告与主流财经新闻

### 核心舆情内容
{news_content}

### 情绪判研执行指令
由于当前社交媒体（雪球/股吧）实时讨论抓取受限，请你作为分析师：
1. **以公告为准**：重点研读公告（Notice）中的回购、股权变动等实锤信息。
2. **舆情推测**：通过主流媒体（证券时报、财联社等）的报道基调，推断机构和散户的市场预期。
3. **情绪映射**：基于业务进展（cmsArticleWebOld）和资金流向，刻画当前市场对该标的的冷热程度。
"""
                            result_data.append(sentiment_summary)
                            response_dict["content"] = sentiment_summary
                            response_dict["status"] = "warning"
                            response_dict["source"] = "新闻舆情补位"
                            logger.info(f"✅ [情绪补位] 已通过新闻源成功补位，长度: {len(news_content)}")
                        else:
                            logger.warning(f"⚠️ [Serper] 且新闻源亦无数据，返回默认值")
                            response_dict["summary"] = f"当前暂无股票 {ticker} ({stock_name}) 的详细市场情绪数据，系统默认给予中性评级。请以市场客观指标为准。"
                            response_dict["company_name_check"] = f"请严格基于股票代码 {ticker} 确认公司名称，禁止臆测"
                            return response_dict


                except Exception as e:
                    # 🔥 捕获 Serper 异常（如 Key 缺失），同样尝试新闻补位
                    logger.error(f"❌ [Serper] 搜索失败: {e}，尝试执行新闻降级方案...")
                    
                    try:
                        news_res = self.get_stock_news_unified(ticker, max_news=20)
                        news_content = news_res.get("content", "")
                        
                        if news_content and "无法获取" not in news_content:
                             sentiment_summary = f"""
## 舆情热度分析报告 (备用模式)

**分析对象**: {ticker}
**分析日期**: {curr_date}
**数据来源**: 实时财经新闻与官方公告

{news_content}

---
**分析师提示**：当前社交平台数据接口维护中，请基于上述权威新闻和公告内容，研判投资者的心理预期和市场博弈形态。
"""
                             result_data.append(sentiment_summary)
                             response_dict["content"] = sentiment_summary
                             response_dict["status"] = "warning"
                             response_dict["source"] = "新闻舆情降级"
                             return response_dict
                    except Exception as nested_e:
                        logger.error(f"❌ [降级失败] 新闻补位也挂了: {nested_e}")

                    response_dict["summary"] = f"【系统提示】情绪分析失败: {str(e)}"
                    response_dict["status"] = "error"
                    response_dict["error"] = str(e)
                    return response_dict


            else:
                # 美股：使用Reddit情绪分析
                logger.info(f"🇺🇸 [统一情绪工具] 处理美股情绪...")

                try:
                    from tradingagents.dataflows.interface import get_reddit_sentiment

                    sentiment_data = get_reddit_sentiment(ticker, curr_date)
                    result_data.append(f"## 美股Reddit情绪\n{sentiment_data}")
                    response_dict["content"] = sentiment_data
                    response_dict["source"] = "Reddit"
                    response_dict["status"] = "success"
                except Exception as e:
                    result_data.append(f"## 美股Reddit情绪\n获取失败: {e}")
                    response_dict["content"] = f"## 美股Reddit情绪\n获取失败: {e}"
                    response_dict["status"] = "error"

            # 组合所有数据
            combined_result = f"""# {ticker} 情绪分析

**股票类型**: {market_info['market_name']}
**分析日期**: {curr_date}

{chr(10).join(result_data)}

---
*数据来源: Serper (Google Search) / Reddit*
"""
            response_dict["content"] = combined_result
            
            logger.info(f"😊 [统一情绪工具] 数据获取完成，总长度: {len(combined_result)}")
            return response_dict

        except Exception as e:
            error_msg = f"统一情绪分析工具执行失败: {str(e)}"
            logger.error(f"❌ [统一情绪工具] {error_msg}")
            return {
                "status": "error",
                "error": str(e),
                "ticker": ticker,
                "content": error_msg
            }

    def _get_us_share_news(self, stock_code: str, max_news: int, model_info: str = "") -> str:
        """
        获取美股新闻 - 多源融合模式
        数据源：FinnHub + Alpha Vantage + Serper + 智能去重
        """
        logger.info(f"[统一新闻工具] 🇺🇸 获取美股 {stock_code} 新闻（多源融合模式）")
        
        all_content_parts = []  # 收集所有数据源的内容
        sources_used = []
        
        # ==================== 数据源1: FinnHub新闻（最丰富）====================
        try:
            logger.info(f"[统一新闻工具] 📰 [1/4] 从FinnHub获取新闻...")
            import requests
            import os
            from datetime import datetime, timedelta
            
            api_key = os.getenv('FINNHUB_API_KEY', '')
            if api_key:
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                url = f'https://finnhub.io/api/v1/company-news?symbol={stock_code}&from={start_date}&to={end_date}&token={api_key}'
                
                resp = requests.get(url, timeout=15)
                if resp.status_code == 200:
                    news_list = resp.json()
                    if news_list and len(news_list) > 0:
                        finnhub_content = f"=== 📰 FinnHub美股新闻 ===\n\n"
                        for n in news_list[:15]:  # 取前15条
                            headline = n.get('headline', '')
                            source = n.get('source', '')
                            summary = n.get('summary', '')[:200] + '...' if len(n.get('summary', '')) > 200 else n.get('summary', '')
                            pub_time = datetime.fromtimestamp(n.get('datetime', 0)).strftime('%Y-%m-%d %H:%M') if n.get('datetime') else ''
                            finnhub_content += f"### {headline}\n- **时间**: {pub_time}\n- **来源**: {source}\n- **摘要**: {summary}\n\n"
                        
                        logger.info(f"[统一新闻工具] ✅ FinnHub: {min(15, len(news_list))}条, {len(finnhub_content)} 字符")
                        all_content_parts.append(("FinnHub", finnhub_content))
                        sources_used.append("FinnHub")
            else:
                logger.warning("[统一新闻工具] ⚠️ FINNHUB_API_KEY未配置")
        except Exception as e:
            logger.warning(f"[统一新闻工具] ⚠️ FinnHub获取失败: {e}")
        
        # ==================== 数据源2: Alpha Vantage新闻 ====================
        try:
            logger.info(f"[统一新闻工具] 📈 [2/4] 从Alpha Vantage获取新闻...")
            from tradingagents.tools.alpha_vantage_news import get_alpha_vantage_news, format_alpha_vantage_news
            av_news = get_alpha_vantage_news(ticker=stock_code, limit=10)
            if av_news and len(av_news) > 0:
                formatted = format_alpha_vantage_news(av_news, stock_code)
                logger.info(f"[统一新闻工具] ✅ Alpha Vantage: {len(av_news)}条, {len(formatted)} 字符")
                all_content_parts.append(("Alpha Vantage", formatted))
                sources_used.append("Alpha Vantage")
        except Exception as e:
            logger.warning(f"[统一新闻工具] ⚠️ Alpha Vantage获取失败: {e}")
        
        # ==================== 数据源3: Serper实时搜索 ====================
        try:
            logger.info(f"[统一新闻工具] 🔍 [3/4] 从Serper获取实时新闻...")
            query = f"{stock_code} stock news earnings financial analysis"
            serper_result = self._search_news_with_serper(query, period="qdr:d")  # 过去1天
            if serper_result and len(serper_result) > 100:
                logger.info(f"[统一新闻工具] ✅ Serper: {len(serper_result)} 字符")
                all_content_parts.append(("Serper实时搜索", serper_result))
                sources_used.append("Serper")
        except Exception as e:
            logger.warning(f"[统一新闻工具] ⚠️ Serper获取失败: {e}")
        
        # ==================== 数据源4: 数据库缓存 ====================
        try:
            logger.info(f"[统一新闻工具] 📦 [4/4] 从数据库获取历史新闻...")
            db_news = self._get_news_from_database(stock_code, 10, stock_code)
            if db_news and len(db_news) > 100:
                logger.info(f"[统一新闻工具] ✅ 数据库缓存: {len(db_news)} 字符")
                all_content_parts.append(("数据库历史", db_news))
                sources_used.append("数据库历史")
        except Exception as e:
            logger.warning(f"[统一新闻工具] ⚠️ 数据库获取失败: {e}")
        
        # ==================== 融合所有数据源 ====================
        if not all_content_parts:
            logger.error(f"[统一新闻工具] ❌ 所有数据源均失败！")
            return "❌ 无法获取美股新闻数据，所有新闻源均不可用"
        
        # 🔥 智能去重
        deduplicator = NewsDeduplicator()
        deduplicated_parts = []
        total_before = 0
        
        for source_name, content in all_content_parts:
            lines = content.split('\n')
            kept_lines = []
            for line in lines:
                if line.startswith('###') or line.startswith('- **'):
                    total_before += 1
                    title = line.replace('###', '').replace('- **', '').strip()
                    if deduplicator.check_and_add(title):
                        kept_lines.append(line)
                else:
                    kept_lines.append(line)
            deduplicated_parts.append((source_name, '\n'.join(kept_lines)))
        
        stats = deduplicator.get_stats()
        logger.info(f"[统一新闻工具] 🔄 智能去重: {stats['duplicates_removed']} 条重复已移除 (原{stats['total_checked']}条 → {stats['unique_kept']}条)")
        
        # 构建最终报告
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        final_report = f"""# {stock_code} 综合新闻报告 (多源融合+智能去重)

📅 生成时间: {timestamp}
📊 数据来源: {', '.join(sources_used)} ({len(sources_used)}个)
📏 总数据量: {sum(len(c) for _, c in deduplicated_parts)} 字符
🔄 去重统计: {stats['duplicates_removed']} 条重复已移除

---

"""
        for source_name, content in deduplicated_parts:
            final_report += f"## 📌 来源: {source_name}\n\n{content}\n\n---\n\n"
        
        logger.info(f"[统一新闻工具] 🎉 美股融合完成: {len(sources_used)}个数据源, {len(final_report)} 字符")
        
        return final_report
    
    def _format_news_result(self, news_content: str, source: str, model_info: str = "") -> str:
        """格式化新闻结果"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 🔍 添加调试日志：打印原始新闻内容
        logger.info(f"[统一新闻工具] 📋 原始新闻内容预览 (前500字符): {news_content[:500]}")
        logger.info(f"[统一新闻工具] 📊 原始内容长度: {len(news_content)} 字符")
        
        # 检测是否为Google/Gemini模型
        is_google_model = any(keyword in model_info.lower() for keyword in ['google', 'gemini', 'gemma'])
        original_length = len(news_content)
        google_control_applied = False
        
        # 🔍 添加Google模型检测日志
        if is_google_model:
            logger.info(f"[统一新闻工具] 🤖 检测到Google模型，启用特殊处理")
        
        # 对Google模型进行特殊的长度控制
        if is_google_model and len(news_content) > 5000:  # 降低阈值到5000字符
            logger.warning(f"[统一新闻工具] 🔧 检测到Google模型，新闻内容过长({len(news_content)}字符)，进行长度控制...")
            
            # 更严格的长度控制策略
            lines = news_content.split('\n')
            important_lines = []
            char_count = 0
            target_length = 3000  # 目标长度设为3000字符
            
            # 第一轮：优先保留包含关键词的重要行
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # 检查是否包含重要关键词
                important_keywords = ['股票', '公司', '财报', '业绩', '涨跌', '价格', '市值', '营收', '利润', 
                                    '增长', '下跌', '上涨', '盈利', '亏损', '投资', '分析', '预期', '公告']
                
                is_important = any(keyword in line for keyword in important_keywords)
                
                if is_important and char_count + len(line) < target_length:
                    important_lines.append(line)
                    char_count += len(line)
                elif not is_important and char_count + len(line) < target_length * 0.7:  # 非重要内容更严格限制
                    important_lines.append(line)
                    char_count += len(line)
                
                # 如果已达到目标长度，停止添加
                if char_count >= target_length:
                    break
            
            # 如果提取的重要内容仍然过长，进行进一步截断
            if important_lines:
                processed_content = '\n'.join(important_lines)
                if len(processed_content) > target_length:
                    processed_content = processed_content[:target_length] + "...(内容已智能截断)"
                
                news_content = processed_content
                google_control_applied = True
                logger.info(f"[统一新闻工具] ✅ Google模型智能长度控制完成，从{original_length}字符压缩至{len(news_content)}字符")
            else:
                # 如果没有重要行，直接截断到目标长度
                news_content = news_content[:target_length] + "...(内容已强制截断)"
                google_control_applied = True
                logger.info(f"[统一新闻工具] ⚠️ Google模型强制截断至{target_length}字符")
        
        # 计算最终的格式化结果长度，确保总长度合理
        base_format_length = 300  # 格式化模板的大概长度
        if is_google_model and (len(news_content) + base_format_length) > 4000:
            # 如果加上格式化后仍然过长，进一步压缩新闻内容
            max_content_length = 3500
            if len(news_content) > max_content_length:
                news_content = news_content[:max_content_length] + "...(已优化长度)"
                google_control_applied = True
                logger.info(f"[统一新闻工具] 🔧 Google模型最终长度优化，内容长度: {len(news_content)}字符")
        
        # 构建格式化结果
        formatted_result = f"""
=== 📰 新闻数据来源: {source} ===
获取时间: {timestamp}
数据长度: {len(news_content)} 字符
{f"模型类型: {model_info}" if model_info else ""}
{f"🔧 Google模型长度控制已应用 (原长度: {original_length} 字符)" if google_control_applied else ""}

=== 📋 新闻内容 ===
{news_content}

=== ✅ 数据状态 ===
状态: 成功获取
来源: {source}
时间戳: {timestamp}
"""
        return formatted_result.strip()

    def _get_market_news_comprehensive(self, max_news_per_source: int = 3) -> str:
        """
        获取市场整体新闻（综合多个来源）
        调用分类.md中的新闻接口，提供市场整体视角的新闻
        
        Args:
            max_news_per_source: 每个数据源最多获取的新闻数量
            
        Returns:
            str: 格式化的市场新闻内容
        """
        from tradingagents.dataflows.providers.china.akshare import get_akshare_provider
        
        logger.info(f"[市场新闻] 开始获取市场整体新闻，每源限制{max_news_per_source}条")
        
        provider = get_akshare_provider()
        news_sections = []
        
        # 1. 财新网 - 财经内容精选
        try:
            logger.info("[市场新闻] 尝试获取财新网新闻...")
            df_cx = provider.stock_news_main_cx()
            if not df_cx.empty:
                formatted = self._format_caixin_news(df_cx, max_news_per_source)
                if formatted:
                    news_sections.append(formatted)
                    logger.info(f"[市场新闻] ✅ 财新网新闻获取成功: {len(df_cx)}条")
        except Exception as e:
            logger.warning(f"[市场新闻] ⚠️ 财新网新闻获取失败: {e}")
        
        # 2. 东财 - 财经早餐
        try:
            logger.info("[市场新闻] 尝试获取财经早餐...")
            df_breakfast = provider.stock_info_cjzc_em()
            if not df_breakfast.empty:
                formatted = self._format_breakfast_news(df_breakfast, max_news_per_source)
                if formatted:
                    news_sections.append(formatted)
                    logger.info(f"[市场新闻] ✅ 财经早餐获取成功: {len(df_breakfast)}条")
        except Exception as e:
            logger.warning(f"[市场新闻] ⚠️ 财经早餐获取失败: {e}")
        
        # 3-7. 全球财经快讯（完整的5个来源）
        sources = [
            ('东方财富', provider.stock_info_global_em),
            ('新浪财经', provider.stock_info_global_sina),
            ('同花顺', provider.stock_info_global_ths),
            ('财联社', provider.stock_info_global_cls),
            ('富途牛牛', provider.stock_info_global_futu)
        ]
        
        for source_name, source_func in sources:
            try:
                logger.info(f"[市场新闻] 尝试获取{source_name}快讯...")
                df = source_func()
                if not df.empty:
                    formatted = self._format_global_news(df, source_name, max_news_per_source)
                    if formatted:
                        news_sections.append(formatted)
                        logger.info(f"[市场新闻] ✅ {source_name}快讯获取成功: {len(df)}条")
            except Exception as e:
                logger.warning(f"[市场新闻] ⚠️ {source_name}快讯获取失败: {e}")
        
        # 组合所有数据
        if news_sections:
            result = "\n\n=== 📊 市场整体新闻补充 ===\n\n" + "\n\n".join(news_sections)
            logger.info(f"[市场新闻] ✅ 市场新闻汇总完成，共{len(news_sections)}个数据源")
            return result
        else:
            logger.warning("[市场新闻] ⚠️ 未获取到任何市场新闻数据")
            return ""

    def _format_caixin_news(self, df, max_news: int) -> str:
        """格式化财新网新闻"""
        try:
            import pandas as pd
            if df is None or df.empty:
                return ""
            
            result = "=== 📰 财新网财经内容精选 ===\n"
            
            for idx, row in df.head(max_news).iterrows():
                title = row.get('标题', '') or row.get('title', '')
                time = row.get('发布时间', '') or row.get('时间', '') or row.get('time', '')
                link = row.get('链接', '') or row.get('link', '')
                
                if title:
                    result += f"\n### {title}\n"
                    if time:
                        result += f"- **时间**: {time}\n"
                    if link:
                        result += f"- **链接**: {link}\n"
            
            return result if len(result) > 50 else ""
        except Exception as e:
            logger.warning(f"[市场新闻] 格式化财新网新闻失败: {e}")
            return ""

    def _format_breakfast_news(self, df, max_news: int) -> str:
        """格式化财经早餐数据"""
        try:
            import pandas as pd
            if df is None or df.empty:
                return ""
            
            result = "=== 🌅 东方财富财经早餐 ===\n"
            
            for idx, row in df.head(max_news).iterrows():
                title = row.get('标题', '') or row.get('title', '')
                date = row.get('日期', '') or row.get('date', '')
                link = row.get('链接', '') or row.get('link', '')
                
                if title:
                    result += f"\n### {title}\n"
                    if date:
                        result += f"- **日期**: {date}\n"
                    if link:
                        result += f"- **链接**: {link}\n"
            
            return result if len(result) > 50 else ""
        except Exception as e:
            logger.warning(f"[市场新闻] 格式化财经早餐失败: {e}")
            return ""

    def _format_global_news(self, df, source_name: str, max_news: int) -> str:
        """格式化全球财经快讯数据"""
        try:
            import pandas as pd
            if df is None or df.empty:
                return ""
            
            result = f"=== 🌐 {source_name}全球财经快讯 ===\n"
            
            for idx, row in df.head(max_news).iterrows():
                # 不同来源的字段名可能不同，需要适配
                title = row.get('标题', '') or row.get('title', '')
                content = row.get('内容', '') or row.get('content', '') or row.get('摘要', '') or row.get('简介', '')
                time = row.get('发布时间', '') or row.get('时间', '') or row.get('time', '') or row.get('date', '')
                
                # 如果没有标题，使用内容前50字符
                display_title = title if title else (content[:50] + "..." if content and len(content) > 50 else content)
                
                if display_title:
                    result += f"\n### {display_title}\n"
                    if time:
                        result += f"- **时间**: {time}\n"
                    if content and title:  # 如果有标题，显示完整内容
                        content_preview = content[:200] + "..." if len(content) > 200 else content
                        result += f"- **内容**: {content_preview}\n"
            
            return result if len(result) > 50 else ""
        except Exception as e:
            logger.warning(f"[市场新闻] 格式化{source_name}快讯失败: {e}")
            return ""
        
        formatted_result = f"""
=== 📰 新闻数据来源: {source} ===
获取时间: {timestamp}
数据长度: {len(news_content)} 字符
{f"模型类型: {model_info}" if model_info else ""}
{f"🔧 Google模型长度控制已应用 (原长度: {original_length} 字符)" if google_control_applied else ""}

=== 📋 新闻内容 ===
{news_content}

=== ✅ 数据状态 ===
状态: 成功获取
来源: {source}
时间戳: {timestamp}
"""
        return formatted_result.strip()


def create_unified_news_tool(toolkit):
    """创建统一新闻工具函数"""
    analyzer = UnifiedNewsAnalyzer(toolkit)
    
    def get_stock_news_unified(stock_code: str, max_news: int = 100, model_info: str = ""):
        """
        统一新闻获取工具
        
        Args:
            stock_code (str): 股票代码 (支持A股如000001、港股如0700.HK、美股如AAPL)
            max_news (int): 最大新闻数量，默认100
            model_info (str): 当前使用的模型信息，用于特殊处理
        """
        

        if not stock_code:
            return "❌ 错误: 未提供股票代码"
        
        return analyzer.get_stock_news_unified(stock_code, max_news, model_info)
    
    # 设置工具属性
    get_stock_news_unified.name = "get_stock_news_unified"
    get_stock_news_unified.description = """
统一新闻获取工具 - 根据股票代码自动获取相应市场的新闻

功能:
- 自动识别股票类型（A股/港股/美股）
- 根据股票类型选择最佳新闻源
- A股: 优先东方财富 -> Google中文 -> OpenAI
- 港股: 优先Google -> OpenAI -> 实时新闻
- 美股: 优先OpenAI -> Google英文 -> FinnHub
- 返回格式化的新闻内容
- 支持Google模型的特殊长度控制
"""
    
    def get_stock_sentiment_unified(ticker: str, curr_date: str) -> str:
        """
        统一的股票情绪分析工具
        自动识别股票类型（A股、港股、美股）并调用相应的情绪数据源
        
        Args:
            ticker: 股票代码
            curr_date: 当前日期
            
        """
        if not ticker:
            return "❌ 错误: 未提供股票代码"
            
        return analyzer.get_stock_sentiment_unified(ticker, curr_date)
    
    # 设置工具属性
    get_stock_sentiment_unified.name = "get_stock_sentiment_unified"
    get_stock_sentiment_unified.description = """
统一股票情绪分析工具 - 根据股票代码自动获取相应市场的情绪数据

功能:
- 自动识别股票类型（A股/港股/美股）
- 港股/A股: 使用Serper搜索雪球/股吧的散户讨论
- 美股: 使用Reddit/Twitter情绪数据
- 返回格式化的情绪分析报告
"""

    return get_stock_news_unified, get_stock_sentiment_unified