from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage
from typing import List
from typing import Annotated
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import RemoveMessage
from langchain_core.tools import tool
from datetime import date, timedelta, datetime
import functools
import pandas as pd
import os
import re
import json
import requests
from dateutil.relativedelta import relativedelta
from langchain_openai import ChatOpenAI
import tradingagents.dataflows.interface as interface
from tradingagents.default_config import DEFAULT_CONFIG
from langchain_core.messages import HumanMessage

# 导入统一日志系统和工具日志装饰器
from tradingagents.utils.logging_init import get_logger
from tradingagents.utils.tool_logging import log_tool_call, log_analysis_step

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')


def create_msg_delete():
    def delete_messages(state):
        """Clear messages and add placeholder for Anthropic compatibility"""
        messages = state["messages"]
        
        # Remove all messages
        removal_operations = [RemoveMessage(id=m.id) for m in messages]
        
        # Add a minimal placeholder message
        placeholder = HumanMessage(content="Continue")
        
        return {"messages": removal_operations + [placeholder]}
    
    return delete_messages

def _search_with_serper(query: str, look_back_days: int = 90) -> str:
    """内部辅助函数：使用Serper API搜索深度内容"""
    try:
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            logger.warning("⚠️ [Serper] 未配置SERPER_API_KEY，无法进行深度搜索")
            return "未找到 (Missing API Key)"
            
        url = "https://google.serper.dev/search"
        headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }
        
        # 使用 qdr:d{days} 进行时间过滤
        payload = json.dumps({
            "q": query,
            "tbs": f"qdr:d{look_back_days}",
            "num": 10
        })
        
        logger.info(f"🔍 [Serper] API调用: {query}, tbs=qdr:d{look_back_days}")
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        
        if response.status_code != 200:
            logger.warning(f"⚠️ [Serper] API请求失败: {response.status_code}")
            return "未找到 (API Error)"
            
        results = response.json().get('organic', [])
        
        if not results:
            logger.info("⚠️ [Serper] 搜索结果为空")
            return "未找到相关结果"
            
        formatted_results = []
        for item in results:
            title = item.get('title', '')
            snippet = item.get('snippet', '')
            link = item.get('link', '')
            date = item.get('date', '近期')
            formatted_results.append(f"### {title}\n- **来源**: {link}\n- **时间**: {date}\n- **摘要**: {snippet}\n")
            
        return "\n".join(formatted_results)
        
    except Exception as e:
        logger.error(f"❌ [Serper] 执行出错: {e}")
        return f"搜索出错: {str(e)}"



class Toolkit:
    _config = DEFAULT_CONFIG.copy()

    @classmethod
    def update_config(cls, config):
        """Update the class-level configuration."""
        cls._config.update(config)

    @property
    def config(self):
        """Access the configuration."""
        return self._config

    def __init__(self, config=None):
        if config:
            self.update_config(config)

    @staticmethod
    @tool
    def get_reddit_news(
        curr_date: Annotated[str, "Date you want to get news for in yyyy-mm-dd format"],
    ) -> str:
        """
        Retrieve global news from Reddit within a specified time frame.
        Args:
            curr_date (str): Date you want to get news for in yyyy-mm-dd format
        Returns:
            str: A formatted dataframe containing the latest global news from Reddit in the specified time frame.
        """
        
        global_news_result = interface.get_reddit_global_news(curr_date, 7, 5)

        return global_news_result

    @staticmethod
    @tool
    def get_finnhub_news(
        ticker: Annotated[
            str,
            "Search query of a company, e.g. 'AAPL, TSM, etc.",
        ],
        start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
        end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest news about a given stock from Finnhub within a date range
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
            start_date (str): Start date in yyyy-mm-dd format
            end_date (str): End date in yyyy-mm-dd format
        Returns:
            str: A formatted dataframe containing news about the company within the date range from start_date to end_date
        """

        end_date_str = end_date

        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        look_back_days = (end_date - start_date).days

        finnhub_news_result = interface.get_finnhub_news(
            ticker, end_date_str, look_back_days
        )

        return finnhub_news_result

    @staticmethod
    @tool
    def get_reddit_stock_info(
        ticker: Annotated[
            str,
            "Ticker of a company. e.g. AAPL, TSM",
        ],
        curr_date: Annotated[str, "Current date you want to get news for"],
    ) -> str:
        """
        Retrieve the latest news about a given stock from Reddit, given the current date.
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
            curr_date (str): current date in yyyy-mm-dd format to get news for
        Returns:
            str: A formatted dataframe containing the latest news about the company on the given date
        """

        stock_news_results = interface.get_reddit_company_news(ticker, curr_date, 7, 5)

        return stock_news_results

    @staticmethod
    @tool
    def get_chinese_social_sentiment(
        ticker: Annotated[str, "Ticker of a company. e.g. AAPL, TSM"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ) -> str:
        """
        获取中国社交媒体和财经平台上关于特定股票的情绪分析和讨论热度。
        整合雪球、东方财富股吧、新浪财经等中国本土平台的数据。
        Args:
            ticker (str): 股票代码，如 AAPL, TSM
            curr_date (str): 当前日期，格式为 yyyy-mm-dd
        Returns:
            str: 包含中国投资者情绪分析、讨论热度、关键观点的格式化报告
        """
        try:
            # 这里可以集成多个中国平台的数据
            chinese_sentiment_results = interface.get_chinese_social_sentiment(ticker, curr_date)
            return chinese_sentiment_results
        except Exception as e:
            # 如果中国平台数据获取失败，回退到原有的Reddit数据
            return interface.get_reddit_company_news(ticker, curr_date, 7, 5)

    @staticmethod
    # @tool  # 已移除：请使用 get_stock_fundamentals_unified 或 get_stock_market_data_unified
    def get_china_stock_data(
        stock_code: Annotated[str, "中国股票代码，如 000001(平安银行), 600519(贵州茅台)"],
        start_date: Annotated[str, "开始日期，格式 yyyy-mm-dd"],
        end_date: Annotated[str, "结束日期，格式 yyyy-mm-dd"],
    ) -> str:
        """
        获取中国A股实时和历史数据，通过Tushare等高质量数据源提供专业的股票数据。
        支持实时行情、历史K线、技术指标等全面数据，自动使用最佳数据源。
        Args:
            stock_code (str): 中国股票代码，如 000001(平安银行), 600519(贵州茅台)
            start_date (str): 开始日期，格式 yyyy-mm-dd
            end_date (str): 结束日期，格式 yyyy-mm-dd
        Returns:
            str: 包含实时行情、历史数据、技术指标的完整股票分析报告
        """
        try:
            logger.debug(f"📊 [DEBUG] ===== agent_utils.get_china_stock_data 开始调用 =====")
            logger.debug(f"📊 [DEBUG] 参数: stock_code={stock_code}, start_date={start_date}, end_date={end_date}")

            from tradingagents.dataflows.interface import get_china_stock_data_unified
            logger.debug(f"📊 [DEBUG] 成功导入统一数据源接口")

            logger.debug(f"📊 [DEBUG] 正在调用统一数据源接口...")
            result = get_china_stock_data_unified(stock_code, start_date, end_date)

            logger.debug(f"📊 [DEBUG] 统一数据源接口调用完成")
            logger.debug(f"📊 [DEBUG] 返回结果类型: {type(result)}")
            logger.debug(f"📊 [DEBUG] 返回结果长度: {len(result) if result else 0}")
            logger.debug(f"📊 [DEBUG] 返回结果前200字符: {str(result)[:200]}...")
            logger.debug(f"📊 [DEBUG] ===== agent_utils.get_china_stock_data 调用结束 =====")

            return result
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"❌ [DEBUG] ===== agent_utils.get_china_stock_data 异常 =====")
            logger.error(f"❌ [DEBUG] 错误类型: {type(e).__name__}")
            logger.error(f"❌ [DEBUG] 错误信息: {str(e)}")
            logger.error(f"❌ [DEBUG] 详细堆栈:")
            print(error_details)
            logger.error(f"❌ [DEBUG] ===== 异常处理结束 =====")
            return f"中国股票数据获取失败: {str(e)}。请检查网络连接或稍后重试。"

    @staticmethod
    @tool
    def get_china_market_overview(
        curr_date: Annotated[str, "当前日期，格式 yyyy-mm-dd"],
    ) -> str:
        """
        获取中国股市整体概览，包括主要指数的实时行情。
        涵盖上证指数、深证成指、创业板指、科创50等主要指数。
        Args:
            curr_date (str): 当前日期，格式 yyyy-mm-dd
        Returns:
            str: 包含主要指数实时行情的市场概览报告
        """
        try:
            # 使用Tushare获取主要指数数据
            from tradingagents.dataflows.providers.china.tushare import get_tushare_adapter

            adapter = get_tushare_adapter()


            # 使用Tushare获取主要指数信息
            # 这里可以扩展为获取具体的指数数据
            return f"""# 中国股市概览 - {curr_date}

## 📊 主要指数
- 上证指数: 数据获取中...
- 深证成指: 数据获取中...
- 创业板指: 数据获取中...
- 科创50: 数据获取中...

## 💡 说明
市场概览功能正在从TDX迁移到Tushare，完整功能即将推出。
当前可以使用股票数据获取功能分析个股。

数据来源: Tushare专业数据源
更新时间: {curr_date}
"""

        except Exception as e:
            return f"中国市场概览获取失败: {str(e)}。正在从TDX迁移到Tushare数据源。"

    @staticmethod
    @tool
    def get_YFin_data(
        symbol: Annotated[str, "ticker symbol of the company"],
        start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
        end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    ) -> str:
        """
        Retrieve the stock price data for a given ticker symbol from Yahoo Finance.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            start_date (str): Start date in yyyy-mm-dd format
            end_date (str): End date in yyyy-mm-dd format
        Returns:
            str: A formatted dataframe containing the stock price data for the specified ticker symbol in the specified date range.
        """

        result_data = interface.get_YFin_data(symbol, start_date, end_date)

        return result_data

    @staticmethod
    @tool
    def get_YFin_data_online(
        symbol: Annotated[str, "ticker symbol of the company"],
        start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
        end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    ) -> str:
        """
        Retrieve the stock price data for a given ticker symbol from Yahoo Finance.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            start_date (str): Start date in yyyy-mm-dd format
            end_date (str): End date in yyyy-mm-dd format
        Returns:
            str: A formatted dataframe containing the stock price data for the specified ticker symbol in the specified date range.
        """

        result_data = interface.get_YFin_data_online(symbol, start_date, end_date)

        return result_data

    @staticmethod
    @tool
    def get_stockstats_indicators_report(
        symbol: Annotated[str, "ticker symbol of the company"],
        indicator: Annotated[
            str, "technical indicator to get the analysis and report of"
        ],
        curr_date: Annotated[
            str, "The current trading date you are trading on, YYYY-mm-dd"
        ],
        look_back_days: Annotated[int, "how many days to look back"] = 30,
    ) -> str:
        """
        Retrieve stock stats indicators for a given ticker symbol and indicator.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            indicator (str): Technical indicator to get the analysis and report of
            curr_date (str): The current trading date you are trading on, YYYY-mm-dd
            look_back_days (int): How many days to look back, default is 30
        Returns:
            str: A formatted dataframe containing the stock stats indicators for the specified ticker symbol and indicator.
        """

        result_stockstats = interface.get_stock_stats_indicators_window(
            symbol, indicator, curr_date, look_back_days, False
        )

        return result_stockstats

    @staticmethod
    @tool
    def get_stockstats_indicators_report_online(
        symbol: Annotated[str, "ticker symbol of the company"],
        indicator: Annotated[
            str, "technical indicator to get the analysis and report of"
        ],
        curr_date: Annotated[
            str, "The current trading date you are trading on, YYYY-mm-dd"
        ],
        look_back_days: Annotated[int, "how many days to look back"] = 30,
    ) -> str:
        """
        Retrieve stock stats indicators for a given ticker symbol and indicator.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            indicator (str): Technical indicator to get the analysis and report of
            curr_date (str): The current trading date you are trading on, YYYY-mm-dd
            look_back_days (int): How many days to look back, default is 30
        Returns:
            str: A formatted dataframe containing the stock stats indicators for the specified ticker symbol and indicator.
        """

        result_stockstats = interface.get_stock_stats_indicators_window(
            symbol, indicator, curr_date, look_back_days, True
        )

        return result_stockstats

    @staticmethod
    @tool
    def get_finnhub_company_insider_sentiment(
        ticker: Annotated[str, "ticker symbol for the company"],
        curr_date: Annotated[
            str,
            "current date of you are trading at, yyyy-mm-dd",
        ],
    ):
        """
        Retrieve insider sentiment information about a company (retrieved from public SEC information) for the past 30 days
        Args:
            ticker (str): ticker symbol of the company
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
            str: a report of the sentiment in the past 30 days starting at curr_date
        """

        data_sentiment = interface.get_finnhub_company_insider_sentiment(
            ticker, curr_date, 30
        )

        return data_sentiment

    @staticmethod
    @tool
    def get_finnhub_company_insider_transactions(
        ticker: Annotated[str, "ticker symbol"],
        curr_date: Annotated[
            str,
            "current date you are trading at, yyyy-mm-dd",
        ],
    ):
        """
        Retrieve insider transaction information about a company (retrieved from public SEC information) for the past 30 days
        Args:
            ticker (str): ticker symbol of the company
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
            str: a report of the company's insider transactions/trading information in the past 30 days
        """

        data_trans = interface.get_finnhub_company_insider_transactions(
            ticker, curr_date, 30
        )

        return data_trans

    @staticmethod
    @tool
    def get_simfin_balance_sheet(
        ticker: Annotated[str, "ticker symbol"],
        freq: Annotated[
            str,
            "reporting frequency of the company's financial history: annual/quarterly",
        ],
        curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
    ):
        """
        Retrieve the most recent balance sheet of a company
        Args:
            ticker (str): ticker symbol of the company
            freq (str): reporting frequency of the company's financial history: annual / quarterly
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
            str: a report of the company's most recent balance sheet
        """

        data_balance_sheet = interface.get_simfin_balance_sheet(ticker, freq, curr_date)

        return data_balance_sheet

    @staticmethod
    @tool
    def get_simfin_cashflow(
        ticker: Annotated[str, "ticker symbol"],
        freq: Annotated[
            str,
            "reporting frequency of the company's financial history: annual/quarterly",
        ],
        curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
    ):
        """
        Retrieve the most recent cash flow statement of a company
        Args:
            ticker (str): ticker symbol of the company
            freq (str): reporting frequency of the company's financial history: annual / quarterly
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
                str: a report of the company's most recent cash flow statement
        """

        data_cashflow = interface.get_simfin_cashflow(ticker, freq, curr_date)

        return data_cashflow

    @staticmethod
    @tool
    def get_simfin_income_stmt(
        ticker: Annotated[str, "ticker symbol"],
        freq: Annotated[
            str,
            "reporting frequency of the company's financial history: annual/quarterly",
        ],
        curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
    ):
        """
        Retrieve the most recent income statement of a company
        Args:
            ticker (str): ticker symbol of the company
            freq (str): reporting frequency of the company's financial history: annual / quarterly
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
                str: a report of the company's most recent income statement
        """

        data_income_stmt = interface.get_simfin_income_statements(
            ticker, freq, curr_date
        )

        return data_income_stmt

    @staticmethod
    @tool
    def get_google_news(
        query: Annotated[str, "Query to search with"],
        curr_date: Annotated[str, "Curr date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest news from Google News based on a query and date range.
        Args:
            query (str): Query to search with
            curr_date (str): Current date in yyyy-mm-dd format
            look_back_days (int): How many days to look back
        Returns:
            str: A formatted string containing the latest news from Google News based on the query and date range.
        """

        google_news_results = interface.get_google_news(query, curr_date, 7)

        return google_news_results

    @staticmethod
    @tool
    def get_realtime_stock_news(
        ticker: Annotated[str, "Ticker of a company. e.g. AAPL, TSM"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ) -> str:
        """
        获取股票的实时新闻分析，解决传统新闻源的滞后性问题。
        整合多个专业财经API，提供15-30分钟内的最新新闻。
        支持多种新闻源轮询机制，优先使用实时新闻聚合器，失败时自动尝试备用新闻源。
        对于A股和港股，会优先使用中文财经新闻源（如东方财富）。
        
        Args:
            ticker (str): 股票代码，如 AAPL, TSM, 600036.SH
            curr_date (str): 当前日期，格式为 yyyy-mm-dd
        Returns:
            str: 包含实时新闻分析、紧急程度评估、时效性说明的格式化报告
        """
        from tradingagents.dataflows.realtime_news_utils import get_realtime_stock_news
        return get_realtime_stock_news(ticker, curr_date, hours_back=6)

    @staticmethod
    @tool
    def get_stock_news_openai(
        ticker: Annotated[str, "the company's ticker"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest news about a given stock by using OpenAI's news API.
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
            curr_date (str): Current date in yyyy-mm-dd format
        Returns:
            str: A formatted string containing the latest news about the company on the given date.
        """

        openai_news_results = interface.get_stock_news_openai(ticker, curr_date)

        return openai_news_results

    @staticmethod
    @tool
    def get_global_news_openai(
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest macroeconomics news on a given date using OpenAI's macroeconomics news API.
        Args:
            curr_date (str): Current date in yyyy-mm-dd format
        Returns:
            str: A formatted string containing the latest macroeconomic news on the given date.
        """

        openai_news_results = interface.get_global_news_openai(curr_date)

        return openai_news_results

    @staticmethod
    # @tool  # 已移除：请使用 get_stock_fundamentals_unified
    def get_fundamentals_openai(
        ticker: Annotated[str, "the company's ticker"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest fundamental information about a given stock on a given date by using OpenAI's news API.
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
            curr_date (str): Current date in yyyy-mm-dd format
        Returns:
            str: A formatted string containing the latest fundamental information about the company on the given date.
        """
        logger.debug(f"📊 [DEBUG] get_fundamentals_openai 被调用: ticker={ticker}, date={curr_date}")

        # 检查是否为中国股票
        import re
        if re.match(r'^\d{6}$', str(ticker)):
            logger.debug(f"📊 [DEBUG] 检测到中国A股代码: {ticker}")
            # 使用统一接口获取中国股票名称
            try:
                from tradingagents.dataflows.interface import get_china_stock_info_unified
                stock_info = get_china_stock_info_unified(ticker)

                # 解析股票名称
                if "股票名称:" in stock_info:
                    company_name = stock_info.split("股票名称:")[1].split("\n")[0].strip()
                else:
                    company_name = f"股票代码{ticker}"

                logger.debug(f"📊 [DEBUG] 中国股票名称映射: {ticker} -> {company_name}")
            except Exception as e:
                logger.error(f"⚠️ [DEBUG] 从统一接口获取股票名称失败: {e}")
                company_name = f"股票代码{ticker}"

            # 修改查询以包含正确的公司名称
            modified_query = f"{company_name}({ticker})"
            logger.debug(f"📊 [DEBUG] 修改后的查询: {modified_query}")
        else:
            logger.debug(f"📊 [DEBUG] 检测到非中国股票: {ticker}")
            modified_query = ticker

        try:
            openai_fundamentals_results = interface.get_fundamentals_openai(
                modified_query, curr_date
            )
            logger.debug(f"📊 [DEBUG] OpenAI基本面分析结果长度: {len(openai_fundamentals_results) if openai_fundamentals_results else 0}")
            return openai_fundamentals_results
        except Exception as e:
            logger.error(f"❌ [DEBUG] OpenAI基本面分析失败: {str(e)}")
            return f"基本面分析失败: {str(e)}"

    @staticmethod
    # @tool  # 已移除：请使用 get_stock_fundamentals_unified
    def get_china_fundamentals(
        ticker: Annotated[str, "中国A股股票代码，如600036"],
        curr_date: Annotated[str, "当前日期，格式为yyyy-mm-dd"],
    ):
        """
        获取中国A股股票的基本面信息，使用中国股票数据源。
        Args:
            ticker (str): 中国A股股票代码，如600036, 000001
            curr_date (str): 当前日期，格式为yyyy-mm-dd
        Returns:
            str: 包含股票基本面信息的格式化字符串
        """
        logger.debug(f"📊 [DEBUG] get_china_fundamentals 被调用: ticker={ticker}, date={curr_date}")

        # 检查是否为中国股票
        import re
        if not re.match(r'^\d{6}$', str(ticker)):
            return f"错误：{ticker} 不是有效的中国A股代码格式"

        try:
            # 使用统一数据源接口获取股票数据（默认Tushare，支持备用数据源）
            from tradingagents.dataflows.interface import get_china_stock_data_unified
            logger.debug(f"📊 [DEBUG] 正在获取 {ticker} 的股票数据...")

            # 获取最近30天的数据用于基本面分析
            from datetime import datetime, timedelta
            end_date = datetime.strptime(curr_date, '%Y-%m-%d')
            start_date = end_date - timedelta(days=30)

            stock_data = get_china_stock_data_unified(
                ticker,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )

            logger.debug(f"📊 [DEBUG] 股票数据获取完成，长度: {len(stock_data) if stock_data else 0}")

            if not stock_data or "获取失败" in stock_data or "❌" in stock_data:
                return f"无法获取股票 {ticker} 的基本面数据：{stock_data}"

            # 调用真正的基本面分析
            from tradingagents.dataflows.optimized_china_data import OptimizedChinaDataProvider

            # 创建分析器实例
            analyzer = OptimizedChinaDataProvider()

            # 生成真正的基本面分析报告
            fundamentals_report = analyzer._generate_fundamentals_report(ticker, stock_data)

            logger.debug(f"📊 [DEBUG] 中国基本面分析报告生成完成")
            logger.debug(f"📊 [DEBUG] get_china_fundamentals 结果长度: {len(fundamentals_report)}")

            return fundamentals_report

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"❌ [DEBUG] get_china_fundamentals 失败:")
            logger.error(f"❌ [DEBUG] 错误: {str(e)}")
            logger.error(f"❌ [DEBUG] 堆栈: {error_details}")
            return f"中国股票基本面分析失败: {str(e)}"

    @staticmethod
    # @tool  # 已移除：请使用 get_stock_fundamentals_unified 或 get_stock_market_data_unified
    def get_hk_stock_data_unified(
        symbol: Annotated[str, "港股代码，如：0700.HK、9988.HK等"],
        start_date: Annotated[str, "开始日期，格式：YYYY-MM-DD"],
        end_date: Annotated[str, "结束日期，格式：YYYY-MM-DD"]
    ) -> str:
        """
        获取港股数据的统一接口，优先使用AKShare数据源，备用Yahoo Finance

        Args:
            symbol: 港股代码 (如: 0700.HK)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            str: 格式化的港股数据
        """
        logger.debug(f"🇭🇰 [DEBUG] get_hk_stock_data_unified 被调用: symbol={symbol}, start_date={start_date}, end_date={end_date}")

        try:
            from tradingagents.dataflows.interface import get_hk_stock_data_unified

            result = get_hk_stock_data_unified(symbol, start_date, end_date)

            logger.debug(f"🇭🇰 [DEBUG] 港股数据获取完成，长度: {len(result) if result else 0}")

            return result

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"❌ [DEBUG] get_hk_stock_data_unified 失败:")
            logger.error(f"❌ [DEBUG] 错误: {str(e)}")
            logger.error(f"❌ [DEBUG] 堆栈: {error_details}")
            return f"港股数据获取失败: {str(e)}"

    @staticmethod
    @tool
    @log_tool_call(tool_name="get_stock_fundamentals_unified", log_args=True)
    def get_stock_fundamentals_unified(
        ticker: Annotated[str, "股票代码（支持A股、港股、美股）"],
        start_date: Annotated[str, "开始日期，格式：YYYY-MM-DD"] = None,
        end_date: Annotated[str, "结束日期，格式：YYYY-MM-DD"] = None,
        curr_date: Annotated[str, "当前日期，格式：YYYY-MM-DD"] = None
    ) -> dict:
        """
        统一的股票基本面分析工具
        自动识别股票类型（A股、港股、美股）并调用相应的数据源
        支持基于分析级别的数据获取策略

        Args:
            ticker: 股票代码（如：000001、0700.HK、AAPL）
            start_date: 开始日期（可选，格式：YYYY-MM-DD）
            end_date: 结束日期（可选，格式：YYYY-MM-DD）
            curr_date: 当前日期（可选，格式：YYYY-MM-DD）

        Returns:
            dict: 基本面分析数据和报告
        """
        logger.info(f"📊 [统一基本面工具] 分析股票: {ticker}")

        # 🔧 获取分析级别配置，支持基于级别的数据获取策略
        research_depth = Toolkit._config.get('research_depth', '标准')
        logger.info(f"🔧 [分析级别] 当前分析级别: {research_depth}")
        
        # 数字等级到中文等级的映射
        numeric_to_chinese = {
            1: "快速",
            2: "基础", 
            3: "标准",
            4: "深度",
            5: "全面"
        }
        
        # 标准化研究深度：支持数字输入
        if isinstance(research_depth, (int, float)):
            research_depth = int(research_depth)
            if research_depth in numeric_to_chinese:
                chinese_depth = numeric_to_chinese[research_depth]
                logger.info(f"🔢 [等级转换] 数字等级 {research_depth} → 中文等级 '{chinese_depth}'")
                research_depth = chinese_depth
            else:
                logger.warning(f"⚠️ 无效的数字等级: {research_depth}，使用默认标准分析")
                research_depth = "标准"
        elif isinstance(research_depth, str):
            # 如果是字符串形式的数字，转换为整数
            if research_depth.isdigit():
                numeric_level = int(research_depth)
                if numeric_level in numeric_to_chinese:
                    chinese_depth = numeric_to_chinese[numeric_level]
                    logger.info(f"🔢 [等级转换] 字符串数字 '{research_depth}' → 中文等级 '{chinese_depth}'")
                    research_depth = chinese_depth
                else:
                    logger.warning(f"⚠️ 无效的字符串数字等级: {research_depth}，使用默认标准分析")
                    research_depth = "标准"
            # 如果已经是中文等级，直接使用
            elif research_depth in ["快速", "基础", "标准", "深度", "全面"]:
                logger.info(f"📝 [等级确认] 使用中文等级: '{research_depth}'")
            else:
                logger.warning(f"⚠️ 未知的研究深度: {research_depth}，使用默认标准分析")
                research_depth = "标准"
        else:
            logger.warning(f"⚠️ 无效的研究深度类型: {type(research_depth)}，使用默认标准分析")
            research_depth = "标准"
        
        # 根据分析级别调整数据获取策略
        # 🔧 修正映射关系：data_depth 应该与 research_depth 保持一致
        if research_depth == "快速":
            # 快速分析：获取基础数据，减少数据源调用
            data_depth = "basic"
            logger.info(f"🔧 [分析级别] 快速分析模式：获取基础数据")
        elif research_depth == "基础":
            # 基础分析：获取标准数据
            data_depth = "standard"
            logger.info(f"🔧 [分析级别] 基础分析模式：获取标准数据")
        elif research_depth == "标准":
            # 标准分析：获取标准数据（不是full！）
            data_depth = "standard"
            logger.info(f"🔧 [分析级别] 标准分析模式：获取标准数据")
        elif research_depth == "深度":
            # 深度分析：获取完整数据
            data_depth = "full"
            logger.info(f"🔧 [分析级别] 深度分析模式：获取完整数据")
        elif research_depth == "全面":
            # 全面分析：获取最全面的数据，包含所有可用数据源
            data_depth = "comprehensive"
            logger.info(f"🔧 [分析级别] 全面分析模式：获取最全面数据")
        else:
            # 默认使用标准分析
            data_depth = "standard"
            logger.info(f"🔧 [分析级别] 未知级别，使用标准分析模式")

        # 添加详细的股票代码追踪日志
        logger.info(f"🔍 [股票代码追踪] 统一基本面工具接收到的原始股票代码: '{ticker}' (类型: {type(ticker)})")
        logger.info(f"🔍 [股票代码追踪] 股票代码长度: {len(str(ticker))}")
        logger.info(f"🔍 [股票代码追踪] 股票代码字符: {list(str(ticker))}")

        # 保存原始ticker用于对比
        original_ticker = ticker

        try:
            from tradingagents.utils.stock_utils import StockUtils
            from datetime import datetime, timedelta

            # 自动识别股票类型
            market_info = StockUtils.get_market_info(ticker)
            is_china = market_info['is_china']
            is_hk = market_info['is_hk']
            is_us = market_info['is_us']

            logger.info(f"🔍 [股票代码追踪] StockUtils.get_market_info 返回的市场信息: {market_info}")
            logger.info(f"📊 [统一基本面工具] 股票类型: {market_info['market_name']}")
            logger.info(f"📊 [统一基本面工具] 货币: {market_info['currency_name']} ({market_info['currency_symbol']})")

            # 检查ticker是否在处理过程中发生了变化
            if str(ticker) != str(original_ticker):
                logger.warning(f"🔍 [股票代码追踪] 警告：股票代码发生了变化！原始: '{original_ticker}' -> 当前: '{ticker}'")

            # 设置默认日期
            if not curr_date:
                curr_date = datetime.now().strftime('%Y-%m-%d')
        
            # 基本面分析优化：不需要大量历史数据，只需要当前价格和财务数据
            # 根据数据深度级别设置不同的分析模块数量，而非历史数据范围
            # 🔧 修正映射关系：analysis_modules 应该与 data_depth 保持一致
            if data_depth == "basic":  # 快速分析：基础模块
                analysis_modules = "basic"
                logger.info(f"📊 [基本面策略] 快速分析模式：获取基础财务指标")
            elif data_depth == "standard":  # 基础/标准分析：标准模块
                analysis_modules = "standard"
                logger.info(f"📊 [基本面策略] 标准分析模式：获取标准财务分析")
            elif data_depth == "full":  # 深度分析：完整模块
                analysis_modules = "full"
                logger.info(f"📊 [基本面策略] 深度分析模式：获取完整基本面分析")
            elif data_depth == "comprehensive":  # 全面分析：综合模块
                analysis_modules = "comprehensive"
                logger.info(f"📊 [基本面策略] 全面分析模式：获取综合基本面分析")
            else:
                analysis_modules = "standard"  # 默认标准分析
                logger.info(f"📊 [基本面策略] 默认模式：获取标准基本面分析")
            
            # 基本面分析策略：
            # 1. 获取10天数据（保证能拿到数据，处理周末/节假日）
            # 2. 只使用最近2天数据参与分析（仅需当前价格）
            days_to_fetch = 10  # 固定获取10天数据
            days_to_analyze = 2  # 只分析最近2天

            logger.info(f"📅 [基本面策略] 获取{days_to_fetch}天数据，分析最近{days_to_analyze}天")

            if not start_date:
                start_date = (datetime.now() - timedelta(days=days_to_fetch)).strftime('%Y-%m-%d')

            if not end_date:
                end_date = curr_date

            result_data = []

            if is_china:
                # 中国A股：基本面分析优化策略 - 只获取必要的当前价格和基本面数据
                logger.info(f"🇨🇳 [统一基本面工具] 处理A股数据，数据深度: {data_depth}...")
                logger.info(f"🔍 [股票代码追踪] 进入A股处理分支，ticker: '{ticker}'")
                logger.info(f"💡 [优化策略] 基本面分析只获取当前价格和财务数据，不获取历史日线数据")

                # 优化策略：基本面分析不需要大量历史日线数据
                # 只获取当前股价信息（最近1-2天即可）和基本面财务数据
                try:
                    # 获取最新股价信息（只需要最近1-2天的数据）
                    from datetime import datetime, timedelta
                    recent_end_date = curr_date
                    recent_start_date = (datetime.strptime(curr_date, '%Y-%m-%d') - timedelta(days=2)).strftime('%Y-%m-%d')

                    from tradingagents.dataflows.interface import get_china_stock_data_unified
                    logger.info(f"🔍 [股票代码追踪] 调用 get_china_stock_data_unified（仅获取最新价格），传入参数: ticker='{ticker}', start_date='{recent_start_date}', end_date='{recent_end_date}'")
                    current_price_data = get_china_stock_data_unified(ticker, recent_start_date, recent_end_date)

                    # 🔍 调试：打印返回数据的前500字符
                    logger.info(f"🔍 [基本面工具调试] A股价格数据返回长度: {len(current_price_data)}")
                    logger.info(f"🔍 [基本面工具调试] A股价格数据前500字符:\n{current_price_data[:500]}")

                    result_data.append(f"## A股当前价格信息\n{current_price_data}")
                except Exception as e:
                    logger.error(f"❌ [基本面工具调试] A股价格数据获取失败: {e}")
                    result_data.append(f"## A股当前价格信息\n获取失败: {e}")
                    current_price_data = ""

                try:
                    # 获取基本面财务数据（这是基本面分析的核心）
                    from tradingagents.dataflows.optimized_china_data import OptimizedChinaDataProvider
                    analyzer = OptimizedChinaDataProvider()
                    logger.info(f"🔍 [股票代码追踪] 调用 OptimizedChinaDataProvider._generate_fundamentals_report，传入参数: ticker='{ticker}', analysis_modules='{analysis_modules}'")

                    # 传递分析模块参数到基本面分析方法
                    fundamentals_data = analyzer._generate_fundamentals_report(ticker, current_price_data, analysis_modules)

                    # 🔍 调试：打印返回数据的前500字符
                    logger.info(f"🔍 [基本面工具调试] A股基本面数据返回长度: {len(fundamentals_data)}")
                    logger.info(f"🔍 [基本面工具调试] A股基本面数据前500字符:\n{fundamentals_data[:500]}")

                    result_data.append(f"## A股基本面财务数据\n{fundamentals_data}")
                except Exception as e:
                    logger.error(f"❌ [基本面工具调试] A股基本面数据获取失败: {e}")
                    result_data.append(f"## A股基本面财务数据\n获取失败: {e}")

                # 🔥 [基本面补全] 补充最新的财报新闻
                try:
                    logger.info("🔍 [基本面补全] 尝试获取最新的A股财报新闻(2025)...")
                    from tradingagents.dataflows.interface import get_google_news
                    
                    # A股代码处理
                    clean_ticker = ticker
                    if "." in ticker:
                        clean_ticker = ticker.split(".")[0]
                        
                    # 获取当前年份
                    target_year = curr_date.split("-")[0] if curr_date else "2025"

                    # 🔍 优化 A股搜索词：年份 + 报表类型
                    search_query = f"{clean_ticker} {target_year} 季度财报 半年报 业绩公告"
                    
                    # 增加 look_back_days=90，使用 Serper API
                    financial_news = _search_with_serper(search_query, look_back_days=90)
                    
                    if financial_news and "未找到" not in financial_news and len(financial_news) > 50:
                        result_data.append(f"## 最新业绩公告与财报补充 ({target_year}年)\n> 来源：互联网公告搜索 (最近90天)\n> 内容：{target_year}年的季度财报、半年报及业绩公告摘要。\n\n{financial_news}")
                        logger.info(f"✅ [基本面补全] A股业绩公告补充成功")
                except Exception as news_e:
                    logger.warning(f"⚠️ [基本面补全] A股财报新闻获取失败: {news_e}")

            elif is_hk:
                # 港股：使用AKShare数据源，支持多重备用方案
                logger.info(f"🇭🇰 [统一基本面工具] 处理港股数据，数据深度: {data_depth}...")

                hk_data_success = False

                # 🔥 统一策略：所有级别都获取完整数据
                # 原因：提示词是统一的，如果数据不完整会导致LLM基于不存在的数据进行分析（幻觉）
                logger.info(f"🔍 [港股基本面] 统一策略：获取完整数据（忽略 data_depth 参数）")

                # 主要数据源：AKShare
                try:
                    from tradingagents.dataflows.interface import get_hk_stock_data_unified
                    hk_data = get_hk_stock_data_unified(ticker, start_date, end_date)

                    # 🔍 调试：打印返回数据的前500字符
                    logger.info(f"🔍 [基本面工具调试] 港股数据返回长度: {len(hk_data)}")
                    logger.info(f"🔍 [基本面工具调试] 港股数据前500字符:\n{hk_data[:500]}")

                    # 检查数据质量
                    if hk_data and len(hk_data) > 100 and "❌" not in hk_data:
                        result_data.append(f"## 港股数据\n{hk_data}")
                        hk_data_success = True
                        logger.info(f"✅ [统一基本面工具] 港股主要数据源成功")
                    else:
                        logger.warning(f"⚠️ [统一基本面工具] 港股主要数据源质量不佳")

                except Exception as e:
                    logger.error(f"❌ [基本面工具调试] 港股数据获取失败: {e}")

                # 🔥 [基本面补全] 补充最新的财报新闻（弥补结构化数据只有年报的不足）
                try:
                    logger.info("🔍 [基本面补全] 尝试获取最新的财报新闻(2025)以补充结构化数据的滞后...")
                    from tradingagents.utils.stock_utils import StockUtils
                    
                    # 尝试获取公司名称以提高搜索准确度
                    clean_ticker = ticker.replace('.HK', '').replace('.hk', '')
                    
                    try:
                        # 🔥 关键修复：调用 improved_hk 获取中文名称（如 "小米集团"）
                        from tradingagents.dataflows.providers.hk.improved_hk import get_hk_company_name_improved
                        company_name = get_hk_company_name_improved(ticker)
                        # 如果返回的是默认的 "港股01810"，则只用代码，避免搜索 "港股01810 研报" 这种奇怪组合
                        if company_name and "港股" not in company_name:
                            # 清理名称后缀（如 －Ｗ, －Ｓ 等港股特殊标记）
                            company_name = company_name.split('－')[0].split('-')[0]
                            logger.info(f"🔍 [基本面补全] 获取到公司名称: {company_name}")
                        else:
                            company_name = clean_ticker
                    except Exception as name_e:
                        logger.warning(f"⚠️ [基本面补全] 获取公司名称失败: {name_e}")
                        company_name = clean_ticker

                    # 获取当前年份
                    target_year = curr_date.split("-")[0] if curr_date else "2025"

                    # 🔍 优化搜索词：名称 + 代码 + 年份 + 报表类型 (响应用户需求：季报/半年报)
                    search_query = f"{company_name} {clean_ticker} {target_year} 季度财报 半年报 业绩公告"
                    logger.info(f"🔍 [基本面补全] 执行搜索: '{search_query}'")
                    
                    # 获取新闻（最近90天 - 对应一个季度）
                    # 使用 Serper API (qdr:d90)
                    financial_news = _search_with_serper(search_query, look_back_days=90)
                    
                    if financial_news and "未找到" not in financial_news and len(financial_news) > 50:
                        result_data.append(f"## 最新业绩公告与财报补充 ({target_year}年)\n> 来源：互联网公告搜索 (最近90天)\n> 内容：{target_year}年的季度财报、半年报及业绩公告摘要。\n\n{financial_news}")
                        logger.info(f"✅ [基本面补全] 成功补充业绩公告")
                    else:
                        logger.info(f"⚠️ [基本面补全] 未找到显著的业绩公告")

                except Exception as news_e:
                    logger.warning(f"⚠️ [基本面补全] 获取研报分析失败: {news_e}")

                # 备用方案：基础港股信息
                if not hk_data_success:
                    try:
                        from tradingagents.dataflows.interface import get_hk_stock_info_unified
                        hk_info = get_hk_stock_info_unified(ticker)

                        basic_info = f"""## 港股基础信息

**股票代码**: {ticker}
**股票名称**: {hk_info.get('name', f'港股{ticker}')}
**交易货币**: 港币 (HK$)
**交易所**: 香港交易所 (HKG)
**数据源**: {hk_info.get('source', '基础信息')}

⚠️ 注意：详细的价格和财务数据暂时无法获取，建议稍后重试或使用其他数据源。

**基本面分析建议**：
- 建议查看公司最新财报
- 关注港股市场整体走势
- 考虑汇率因素对投资的影响
"""
                        result_data.append(basic_info)
                        logger.info(f"✅ [统一基本面工具] 港股备用信息成功")

                    except Exception as e2:
                        # 最终备用方案
                        fallback_info = f"""## 港股信息（备用）

**股票代码**: {ticker}
**股票类型**: 港股
**交易货币**: 港币 (HK$)
**交易所**: 香港交易所 (HKG)

❌ 数据获取遇到问题: {str(e2)}

**建议**：
- 请稍后重试
- 或使用其他数据源
- 检查股票代码格式是否正确
"""
                        result_data.append(fallback_info)
                        logger.error(f"❌ [统一基本面工具] 港股所有数据源都失败: {e2}")

            else:
                # 美股：使用AKShare多源数据（替代OpenAI）
                logger.info(f"🇺🇸 [统一基本面工具] 处理美股数据（AKShare多源模式）...")

                # 🔥 统一策略：所有级别都获取完整数据
                logger.info(f"🔍 [美股基本面] 使用AKShare数据源：实时行情+历史K线+公司信息+财务指标+估值")

                import akshare as ak
                from datetime import datetime, timedelta
                
                us_data_parts = []
                
                # 1. 实时行情 - 东财
                try:
                    logger.info(f"📊 [美股1/5] 获取实时行情...")
                    spot_df = ak.stock_us_spot_em()
                    ticker_data = spot_df[spot_df['代码'].str.contains(ticker, na=False)]
                    if len(ticker_data) > 0:
                        row = ticker_data.iloc[0]
                        spot_info = f"""### 实时行情 (东方财富)
- **股票代码**: {row.get('代码', ticker)}
- **股票名称**: {row.get('名称', ticker)}
- **最新价**: ${row.get('最新价', 'N/A')}
- **涨跌幅**: {row.get('涨跌幅', 'N/A')}%
- **总市值**: ${row.get('总市值', 0)/1e9:.2f}B
- **市盈率(PE)**: {row.get('市盈率', 'N/A')}
- **成交量**: {row.get('成交量', 0)/1e6:.2f}M
- **成交额**: ${row.get('成交额', 0)/1e9:.2f}B
"""
                        us_data_parts.append(spot_info)
                        logger.info(f"✅ [美股1/5] 实时行情获取成功")
                except Exception as e:
                    logger.warning(f"⚠️ [美股1/5] 实时行情获取失败: {e}")
                
                # 2. 历史K线
                try:
                    logger.info(f"📈 [美股2/5] 获取历史K线...")
                    # 确定股票代码格式（东财美股格式：市场代码.股票代码，如105.TSLA）
                    us_code = f"105.{ticker}" if '.' not in ticker else ticker
                    end_dt = datetime.now()
                    start_dt = end_dt - timedelta(days=30)
                    hist_df = ak.stock_us_hist(
                        symbol=us_code, 
                        period='daily', 
                        start_date=start_dt.strftime('%Y%m%d'), 
                        end_date=end_dt.strftime('%Y%m%d'), 
                        adjust='qfq'
                    )
                    if len(hist_df) > 0:
                        latest = hist_df.iloc[-1]
                        high_30d = hist_df['最高'].max()
                        low_30d = hist_df['最低'].min()
                        avg_vol = hist_df['成交量'].mean() / 1e6
                        hist_info = f"""### 近30天行情走势
- **30天最高价**: ${high_30d:.2f}
- **30天最低价**: ${low_30d:.2f}
- **30天平均成交量**: {avg_vol:.2f}M
- **最新收盘**: ${latest.get('收盘', 'N/A')}
- **数据天数**: {len(hist_df)}天
"""
                        us_data_parts.append(hist_info)
                        logger.info(f"✅ [美股2/5] 历史K线获取成功: {len(hist_df)}天")
                except Exception as e:
                    logger.warning(f"⚠️ [美股2/5] 历史K线获取失败: {e}")
                
                # 3. 公司基本信息 - 雪球
                try:
                    logger.info(f"📋 [美股3/5] 获取公司信息...")
                    info_df = ak.stock_individual_basic_info_us_xq(symbol=ticker)
                    if len(info_df) > 0:
                        info_dict = dict(zip(info_df.iloc[:, 0], info_df.iloc[:, 1])) if len(info_df.columns) >= 2 else {}
                        company_info = f"""### 公司基本信息 (雪球)
- **公司名称**: {info_dict.get('公司名称', info_dict.get('name', ticker))}
- **所属行业**: {info_dict.get('所属行业', info_dict.get('industry', 'N/A'))}
- **上市日期**: {info_dict.get('上市日期', info_dict.get('list_date', 'N/A'))}
- **官网**: {info_dict.get('公司官网', info_dict.get('website', 'N/A'))}
"""
                        us_data_parts.append(company_info)
                        logger.info(f"✅ [美股3/5] 公司信息获取成功")
                except Exception as e:
                    logger.warning(f"⚠️ [美股3/5] 公司信息获取失败: {e}")
                
                # 4. 财务分析指标 - 东财
                try:
                    logger.info(f"💰 [美股4/5] 获取财务分析指标...")
                    fin_df = ak.stock_financial_us_analysis_indicator_em(symbol=ticker)
                    if len(fin_df) > 0:
                        # 获取第一行数据
                        fin_row = fin_df.iloc[0]
                        fin_info = f"""### 财务分析指标 (东方财富)
- **股票代码**: {fin_row.get('SECURITY_CODE', ticker)}
- **公司名称**: {fin_row.get('SECURITY_NAME_ABBR', ticker)}
- **会计准则**: {fin_row.get('ACCOUNTING_STANDARDS', 'N/A')}
{"- **详细指标**: " + str(len(fin_df)) + "项财务数据可用"}
"""
                        us_data_parts.append(fin_info)
                        logger.info(f"✅ [美股4/5] 财务分析指标获取成功: {len(fin_df)}项")
                except Exception as e:
                    logger.warning(f"⚠️ [美股4/5] 财务分析指标获取失败: {e}")
                
                # 5. 估值数据 - 百度
                try:
                    logger.info(f"📉 [美股5/5] 获取估值数据...")
                    val_df = ak.stock_us_valuation_baidu(symbol=ticker, indicator='总市值', period='近一年')
                    if len(val_df) > 0:
                        latest_val = val_df.iloc[-1] if len(val_df) > 0 else {}
                        max_val = val_df.iloc[:, 1].max() if len(val_df.columns) > 1 else 'N/A'
                        min_val = val_df.iloc[:, 1].min() if len(val_df.columns) > 1 else 'N/A'
                        val_info = f"""### 估值历史 (百度)
- **近一年估值数据**: {len(val_df)}条
- **一年最高市值**: {max_val}
- **一年最低市值**: {min_val}
"""
                        us_data_parts.append(val_info)
                        logger.info(f"✅ [美股5/5] 估值数据获取成功: {len(val_df)}条")
                except Exception as e:
                    logger.warning(f"⚠️ [美股5/5] 估值数据获取失败: {e}")
                
                # 汇总美股数据
                if us_data_parts:
                    us_combined = f"""## 美股基本面数据 ({ticker})

**数据来源**: AKShare (东方财富 + 雪球 + 百度)
**获取时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**成功模块**: {len(us_data_parts)}/5

{''.join(us_data_parts)}
"""
                    result_data.append(us_combined)
                    logger.info(f"✅ [统一基本面工具] 美股数据获取成功: {len(us_data_parts)}/5 模块")
                else:
                    result_data.append(f"## 美股基本面数据\n获取失败: 所有AKShare接口均不可用")
                    logger.error(f"❌ [统一基本面工具] 美股所有数据源都失败")

            # 组合所有数据
            combined_result = f"""# {ticker} 基本面分析数据

**股票类型**: {market_info['market_name']}
**货币**: {market_info['currency_name']} ({market_info['currency_symbol']})
**分析日期**: {curr_date}
**数据深度级别**: {data_depth}

{chr(10).join(result_data)}

---
*数据来源: 根据股票类型自动选择最适合的数据源*
"""

            # 添加详细的数据获取日志
            logger.info(f"📊 [统一基本面工具] ===== 数据获取完成摘要 =====")
            logger.info(f"📊 [统一基本面工具] 股票代码: {ticker}")
            logger.info(f"📊 [统一基本面工具] 股票类型: {market_info['market_name']}")
            logger.info(f"📊 [统一基本面工具] 数据深度级别: {data_depth}")
            logger.info(f"📊 [统一基本面工具] 获取的数据模块数量: {len(result_data)}")
            logger.info(f"📊 [统一基本面工具] 总数据长度: {len(combined_result)} 字符")
            
            # 记录每个数据模块的详细信息
            for i, data_section in enumerate(result_data, 1):
                section_lines = data_section.split('\n')
                section_title = section_lines[0] if section_lines else "未知模块"
                section_length = len(data_section)
                logger.info(f"📊 [统一基本面工具] 数据模块 {i}: {section_title} ({section_length} 字符)")
                
                # 如果数据包含错误信息，特别标记
                if "获取失败" in data_section or "❌" in data_section:
                    logger.warning(f"⚠️ [统一基本面工具] 数据模块 {i} 包含错误信息")
                else:
                    logger.info(f"✅ [统一基本面工具] 数据模块 {i} 获取成功")
            
            # 根据数据深度级别记录具体的获取策略
            if data_depth in ["basic", "standard"]:
                logger.info(f"📊 [统一基本面工具] 基础/标准级别策略: 仅获取核心价格数据和基础信息")
            elif data_depth in ["full", "detailed", "comprehensive"]:
                logger.info(f"📊 [统一基本面工具] 完整/详细/全面级别策略: 获取价格数据 + 基本面数据")
            else:
                logger.info(f"📊 [统一基本面工具] 默认策略: 获取完整数据")
            
            logger.info(f"📊 [统一基本面工具] ===== 数据获取摘要结束 =====")
            
            return {
                "report": combined_result,
                "ticker": ticker,
                "market": market_info['market_name'],
                "status": "success"
            }

        except Exception as e:
            error_msg = f"统一基本面分析工具执行失败: {str(e)}"
            logger.error(f"❌ [统一基本面工具] {error_msg}")
            return {
                "status": "error",
                "error": str(e),
                "report": error_msg
            }

    @staticmethod
    @tool
    @log_tool_call(tool_name="get_stock_market_data_unified", log_args=True)
    def get_stock_market_data_unified(
        ticker: Annotated[str, "股票代码（支持A股、港股、美股）"],
        start_date: Annotated[str, "开始日期，格式：YYYY-MM-DD。注意：系统会自动扩展到配置的回溯天数（通常为365天），你只需要传递分析日期即可"],
        end_date: Annotated[str, "结束日期，格式：YYYY-MM-DD。通常与start_date相同，传递当前分析日期即可"]
    ) -> dict:
        """
        统一的股票市场数据工具
        自动识别股票类型（A股、港股、美股）并调用相应的数据源获取价格和技术指标数据

        ⚠️ 重要：系统会自动扩展日期范围到配置的回溯天数（通常为365天），以确保技术指标计算有足够的历史数据。
        你只需要传递当前分析日期作为 start_date 和 end_date 即可，无需手动计算历史日期范围。

        Args:
            ticker: 股票代码（如：000001、0700.HK、AAPL）
            start_date: 开始日期（格式：YYYY-MM-DD）。传递当前分析日期即可，系统会自动扩展
            end_date: 结束日期（格式：YYYY-MM-DD）。传递当前分析日期即可

        Returns:
            dict: 市场数据和技术分析报告

        示例：
            如果分析日期是 2025-11-09，传递：
            - ticker: "00700.HK"
            - start_date: "2025-11-09"
            - end_date: "2025-11-09"
            系统会自动获取 2024-11-09 到 2025-11-09 的365天历史数据
        """
        logger.info(f"📈 [统一市场工具] 分析股票: {ticker}")

        try:
            from tradingagents.utils.stock_utils import StockUtils

            # 自动识别股票类型
            market_info = StockUtils.get_market_info(ticker)
            is_china = market_info['is_china']
            is_hk = market_info['is_hk']
            is_us = market_info['is_us']

            logger.info(f"📈 [统一市场工具] 股票类型: {market_info['market_name']}")
            logger.info(f"📈 [统一市场工具] 货币: {market_info['currency_name']} ({market_info['currency_symbol']}")

            result_data = []

            if is_china:
                # 中国A股：使用中国股票数据源
                logger.info(f"🇨🇳 [统一市场工具] 处理A股市场数据...")

                try:
                    from tradingagents.dataflows.interface import get_china_stock_data_unified
                    stock_data = get_china_stock_data_unified(ticker, start_date, end_date)

                    # 🔍 调试：打印返回数据的前500字符
                    logger.info(f"🔍 [市场工具调试] A股数据返回长度: {len(stock_data)}")
                    logger.info(f"🔍 [市场工具调试] A股数据前500字符:\n{stock_data[:500]}")

                    result_data.append(f"## A股市场数据\n{stock_data}")
                except Exception as e:
                    logger.error(f"❌ [市场工具调试] A股数据获取失败: {e}")
                    result_data.append(f"## A股市场数据\n获取失败: {e}")

            elif is_hk:
                # 港股：使用AKShare数据源
                logger.info(f"🇭🇰 [统一市场工具] 处理港股市场数据...")

                try:
                    from tradingagents.dataflows.interface import get_hk_stock_data_unified
                    hk_data = get_hk_stock_data_unified(ticker, start_date, end_date)

                    # 🔍 调试：打印返回数据的前500字符
                    logger.info(f"🔍 [市场工具调试] 港股数据返回长度: {len(hk_data)}")
                    logger.info(f"🔍 [市场工具调试] 港股数据前500字符:\n{hk_data[:500]}")

                    result_data.append(f"## 港股市场数据\n{hk_data}")
                except Exception as e:
                    logger.error(f"❌ [市场工具调试] 港股数据获取失败: {e}")
                    result_data.append(f"## 港股市场数据\n获取失败: {e}")

            else:
                # 美股：优先使用FINNHUB API数据源
                logger.info(f"🇺🇸 [统一市场工具] 处理美股市场数据...")

                try:
                    from tradingagents.dataflows.providers.us.optimized import get_us_stock_data_cached
                    us_data = get_us_stock_data_cached(ticker, start_date, end_date)
                    result_data.append(f"## 美股市场数据\n{us_data}")
                except Exception as e:
                    result_data.append(f"## 美股市场数据\n获取失败: {e}")

            # 组合所有数据
            combined_result = f"""# {ticker} 市场数据分析

**股票类型**: {market_info['market_name']}
**货币**: {market_info['currency_name']} ({market_info['currency_symbol']})
**分析期间**: {start_date} 至 {end_date}

{chr(10).join(result_data)}

---
*数据来源: 根据股票类型自动选择最适合的数据源*
"""

            logger.info(f"📈 [统一市场工具] 数据获取完成，总长度: {len(combined_result)}")
            return {
                "report": combined_result,
                "ticker": ticker,
                "market": market_info['market_name'],
                "status": "success"
            }

        except Exception as e:
            error_msg = f"统一市场数据工具执行失败: {str(e)}"
            logger.error(f"❌ [统一市场工具] {error_msg}")
            return {
                "status": "error",
                "error": str(e),
                "report": error_msg
            }

    @staticmethod
    @tool
    @log_tool_call(tool_name="get_stock_news_unified", log_args=True)
    def get_stock_news_unified(
        ticker: Annotated[str, "股票代码（支持A股、港股、美股）"],
        curr_date: Annotated[str, "当前日期，格式：YYYY-MM-DD"]
    ) -> str:
        """
        统一的股票新闻工具
        自动识别股票类型（A股、港股、美股）并调用相应的新闻数据源

        Args:
            ticker: 股票代码（如：000001、0700.HK、AAPL）
            curr_date: 当前日期（格式：YYYY-MM-DD）

        Returns:
            str: 新闻分析报告
        """
        logger.info(f"📰 [统一新闻工具] 分析股票: {ticker}")

        try:
            from tradingagents.utils.stock_utils import StockUtils
            from datetime import datetime, timedelta

            # 自动识别股票类型
            market_info = StockUtils.get_market_info(ticker)
            is_china = market_info['is_china']
            is_hk = market_info['is_hk']
            is_us = market_info['is_us']

            logger.info(f"📰 [统一新闻工具] 股票类型: {market_info['market_name']}")

            # 计算新闻查询的日期范围
            end_date = datetime.strptime(curr_date, '%Y-%m-%d')
            start_date = end_date - timedelta(days=7)
            start_date_str = start_date.strftime('%Y-%m-%d')

            result_data = []

            if is_china or is_hk:
                # 中国A股和港股：使用AKShare东方财富新闻和Google新闻（中文搜索）
                logger.info(f"🇨🇳🇭🇰 [统一新闻工具] 处理中文新闻...")

                # 1. 尝试获取AKShare东方财富新闻
                try:
                    # 处理股票代码
                    clean_ticker = ticker.replace('.SH', '').replace('.SZ', '').replace('.SS', '')\
                                   .replace('.HK', '').replace('.XSHE', '').replace('.XSHG', '')
                    
                    logger.info(f"🇨🇳🇭🇰 [统一新闻工具] 尝试获取东方财富新闻: {clean_ticker}")

                    # 通过 AKShare Provider 获取新闻
                    from tradingagents.dataflows.providers.china.akshare import AKShareProvider

                    provider = AKShareProvider()

                    # 获取东方财富新闻
                    news_df = provider.get_stock_news_sync(symbol=clean_ticker)

                    if news_df is not None and not news_df.empty:
                        # 格式化东方财富新闻
                        em_news_items = []
                        for _, row in news_df.iterrows():
                            # AKShare 返回的字段名
                            news_title = row.get('新闻标题', '') or row.get('标题', '')
                            news_time = row.get('发布时间', '') or row.get('时间', '')
                            news_url = row.get('新闻链接', '') or row.get('链接', '')

                            news_item = f"- **{news_title}** [{news_time}]({news_url})"
                            em_news_items.append(news_item)
                        
                        # 添加到结果中
                        if em_news_items:
                            em_news_text = "\n".join(em_news_items)
                            result_data.append(f"## 东方财富新闻\n{em_news_text}")
                            logger.info(f"🇨🇳🇭🇰 [统一新闻工具] 成功获取{len(em_news_items)}条东方财富新闻")
                except Exception as em_e:
                    logger.error(f"❌ [统一新闻工具] 东方财富新闻获取失败: {em_e}")
                    result_data.append(f"## 东方财富新闻\n获取失败: {em_e}")

                # 2. 获取Google新闻作为补充
                try:
                    # 获取公司中文名称用于搜索
                    if is_china:
                        # A股使用股票代码搜索，添加更多中文关键词
                        clean_ticker = ticker.replace('.SH', '').replace('.SZ', '').replace('.SS', '')\
                                       .replace('.XSHE', '').replace('.XSHG', '')
                        search_query = f"{clean_ticker} 股票 公司 财报 新闻"
                        logger.info(f"🇨🇳 [统一新闻工具] A股Google新闻搜索关键词: {search_query}")
                    else:
                        # 港股使用代码搜索
                        search_query = f"{ticker} 港股"
                        logger.info(f"🇭🇰 [统一新闻工具] 港股Google新闻搜索关键词: {search_query}")

                    from tradingagents.dataflows.interface import get_google_news
                    news_data = get_google_news(search_query, curr_date)
                    result_data.append(f"## Google新闻\n{news_data}")
                    logger.info(f"🇨🇳🇭🇰 [统一新闻工具] 成功获取Google新闻")
                except Exception as google_e:
                    logger.error(f"❌ [统一新闻工具] Google新闻获取失败: {google_e}")
                    result_data.append(f"## Google新闻\n获取失败: {google_e}")

            else:
                # 美股：使用Finnhub新闻
                logger.info(f"🇺🇸 [统一新闻工具] 处理美股新闻...")

                try:
                    from tradingagents.dataflows.interface import get_finnhub_news
                    news_data = get_finnhub_news(ticker, start_date_str, curr_date)
                    result_data.append(f"## 美股新闻\n{news_data}")
                except Exception as e:
                    result_data.append(f"## 美股新闻\n获取失败: {e}")

            # 组合所有数据
            combined_result = f"""# {ticker} 新闻分析

**股票类型**: {market_info['market_name']}
**分析日期**: {curr_date}
**新闻时间范围**: {start_date_str} 至 {curr_date}

{chr(10).join(result_data)}

---
*数据来源: 根据股票类型自动选择最适合的新闻源*
"""

            logger.info(f"📰 [统一新闻工具] 数据获取完成，总长度: {len(combined_result)}")
            return combined_result

        except Exception as e:
            error_msg = f"统一新闻工具执行失败: {str(e)}"
            logger.error(f"❌ [统一新闻工具] {error_msg}")
            return error_msg

    @staticmethod
    @tool
    @log_tool_call(tool_name="get_stock_sentiment_unified", log_args=True)
    def get_stock_sentiment_unified(
        ticker: Annotated[str, "股票代码（支持A股、港股、美股）"],
        curr_date: Annotated[str, "当前日期，格式：YYYY-MM-DD"]
    ) -> dict:
        """
        统一的股票情绪分析工具
        自动识别股票类型（A股、港股、美股）并调用相应的情绪数据源

        Args:
            ticker: 股票代码（如：000001、0700.HK、AAPL）
            curr_date: 当前日期（格式：YYYY-MM-DD）

        Returns:
            dict: 情绪分析报告
        """
        try:
            # 委托给统一新闻工具处理，确保逻辑一致性
            from tradingagents.tools.unified_news_tool import UnifiedNewsAnalyzer
            
            # 创建分析器实例 (不需要toolkit，因为此方法不使用其他工具)
            analyzer = UnifiedNewsAnalyzer(None)
            
            # 调用统一实现
            return analyzer.get_stock_sentiment_unified(ticker, curr_date)
            
        except Exception as e:
            error_msg = f"统一情绪分析工具执行失败: {str(e)}"
            logger.error(f"❌ [统一情绪工具] {error_msg}")
            return {
                "status": "error",
                "error": str(e),
                "content": error_msg,
                "summary": error_msg
            }
