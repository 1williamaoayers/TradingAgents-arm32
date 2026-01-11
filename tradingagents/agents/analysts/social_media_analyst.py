from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
import inspect

# 导入统一日志系统和分析模块日志装饰器
from tradingagents.utils.logging_init import get_logger
from tradingagents.utils.tool_logging import log_analyst_module
logger = get_logger("analysts.social_media")

# 导入Google工具调用处理器
from tradingagents.agents.utils.google_tool_handler import GoogleToolCallHandler


def _get_company_name_for_social_media(ticker: str, market_info: dict) -> str:
    """
    为社交媒体分析师获取公司名称

    Args:
        ticker: 股票代码
        market_info: 市场信息字典

    Returns:
        str: 公司名称
    """
    try:
        if market_info['is_china']:
            # 中国A股：使用统一接口获取股票信息
            from tradingagents.dataflows.interface import get_china_stock_info_unified
            stock_info = get_china_stock_info_unified(ticker)

            logger.debug(f"📊 [社交媒体分析师] 获取股票信息返回: {stock_info[:200] if stock_info else 'None'}...")

            # 解析股票名称
            if stock_info and "股票名称:" in stock_info:
                company_name = stock_info.split("股票名称:")[1].split("\n")[0].strip()
                logger.info(f"✅ [社交媒体分析师] 成功获取中国股票名称: {ticker} -> {company_name}")
                return company_name
            else:
                # 降级方案：尝试直接从数据源管理器获取
                logger.warning(f"⚠️ [社交媒体分析师] 无法从统一接口解析股票名称: {ticker}，尝试降级方案")
                try:
                    from tradingagents.dataflows.data_source_manager import get_china_stock_info_unified as get_info_dict
                    info_dict = get_info_dict(ticker)
                    if info_dict and info_dict.get('name'):
                        company_name = info_dict['name']
                        logger.info(f"✅ [社交媒体分析师] 降级方案成功获取股票名称: {ticker} -> {company_name}")
                        return company_name
                except Exception as e:
                    logger.error(f"❌ [社交媒体分析师] 降级方案也失败: {e}")

                logger.error(f"❌ [社交媒体分析师] 所有方案都无法获取股票名称: {ticker}")
                return f"股票代码{ticker}"

        elif market_info['is_hk']:
            # 港股：使用改进的港股工具
            try:
                from tradingagents.dataflows.providers.hk.improved_hk import get_hk_company_name_improved
                company_name = get_hk_company_name_improved(ticker)
                logger.debug(f"📊 [社交媒体分析师] 使用改进港股工具获取名称: {ticker} -> {company_name}")
                return company_name
            except Exception as e:
                logger.debug(f"📊 [社交媒体分析师] 改进港股工具获取名称失败: {e}")
                # 降级方案：生成友好的默认名称
                clean_ticker = ticker.replace('.HK', '').replace('.hk', '')
                return f"港股{clean_ticker}"

        elif market_info['is_us']:
            # 美股：使用简单映射或返回代码
            us_stock_names = {
                'AAPL': '苹果公司',
                'TSLA': '特斯拉',
                'NVDA': '英伟达',
                'MSFT': '微软',
                'GOOGL': '谷歌',
                'AMZN': '亚马逊',
                'META': 'Meta',
                'NFLX': '奈飞'
            }

            company_name = us_stock_names.get(ticker.upper(), f"美股{ticker}")
            logger.debug(f"📊 [社交媒体分析师] 美股名称映射: {ticker} -> {company_name}")
            return company_name

        else:
            return f"股票{ticker}"

    except Exception as e:
        logger.error(f"❌ [社交媒体分析师] 获取公司名称失败: {e}")
        return f"股票{ticker}"


def create_social_media_analyst(llm, toolkit):
    @log_analyst_module("social_media")
    def social_media_analyst_node(state):
        # 🔧 工具调用计数器 - 防止无限循环
        tool_call_count = state.get("sentiment_tool_call_count", 0)
        max_tool_calls = 3  # 最大工具调用次数
        logger.info(f"🔧 [死循环修复] 当前工具调用次数: {tool_call_count}/{max_tool_calls}")

        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        # 获取股票市场信息
        from tradingagents.utils.stock_utils import StockUtils
        market_info = StockUtils.get_market_info(ticker)

        # 获取公司名称
        company_name = _get_company_name_for_social_media(ticker, market_info)
        logger.info(f"[社交媒体分析师] 公司名称: {company_name}")

        def _invoke_tool(tool, args: dict):
            if hasattr(tool, 'invoke'):
                return tool.invoke(args)
            if callable(tool):
                try:
                    sig = inspect.signature(tool)
                    filtered_args = {k: v for k, v in (args or {}).items() if k in sig.parameters}
                    return tool(**filtered_args)
                except Exception:
                    return tool(**(args or {}))
            raise TypeError(f"Unsupported tool type: {type(tool)}")

        # 🔥 使用更稳健的多数据源情绪分析：优先统一情绪工具，失败时可降级到新闻/中文市场情绪
        from tradingagents.tools.unified_news_tool import create_unified_news_tool
        unified_news_tool, unified_sentiment_tool = create_unified_news_tool(toolkit)

        tools = []
        if market_info['is_us']:
            logger.info(f"[社交媒体分析师] 使用多数据源情绪分析（美股优先Alpha Vantage/备用新闻）")
            from tradingagents.dataflows.tools.sentiment_tools import get_combined_sentiment
            tools = [get_combined_sentiment, unified_news_tool]
        else:
            logger.info(f"[社交媒体分析师] 使用多数据源情绪分析（A股/港股优先中文市场情绪/备用新闻）")
            tools = [unified_sentiment_tool, toolkit.get_chinese_social_sentiment, unified_news_tool]

        system_message = (
            """您是一位专业的中国市场社交媒体和投资情绪分析师，负责分析中国投资者对特定股票的讨论和情绪变化。

您的主要职责包括：
1. 分析中国主要财经平台的投资者情绪（如雪球、东方财富股吧等）
2. 监控财经媒体和新闻对股票的报道倾向
3. 识别影响股价的热点事件和市场传言
4. 评估散户与机构投资者的观点差异
5. 分析政策变化对投资者情绪的影响
6. 评估情绪变化对股价的潜在影响

重点关注平台：
- 财经新闻：财联社、新浪财经、东方财富、腾讯财经
- 投资社区：雪球、东方财富股吧、同花顺
- 社交媒体：微博财经大V、知乎投资话题
- 专业分析：各大券商研报、财经自媒体

分析要点：
- 投资者情绪的变化趋势和原因
- 关键意见领袖(KOL)的观点和影响力
- 热点事件对股价预期的影响
- 政策解读和市场预期变化
- 散户情绪与机构观点的差异

📊 情绪影响分析要求：
- 量化投资者情绪强度（乐观/悲观程度）和情绪变化趋势
- 评估情绪变化对短期市场反应的影响（1-5天）
- 分析散户情绪与市场走势的相关性
- 识别情绪极端点和可能的情绪反转信号
- 提供基于情绪分析的市场预期和投资建议
- 评估市场情绪对投资者信心和决策的影响程度
- 不允许回复'无法评估情绪影响'或'需要更多数据'

💰 必须包含：
- 情绪指数评分（1-10分）
- 预期价格波动幅度
- 基于情绪的交易时机建议

请撰写详细的中文分析报告，并在报告末尾附上Markdown表格总结关键发现。
注意：如果社交媒体数据获取受限（如显示数据不足或API限制），**请务必使用提供的【财经新闻】数据**来推断市场舆论倾向和投资者关注点。即使没有直接的社交媒体评论，也要通过新闻报道的语气、频率和主题来分析市场情绪，切勿仅仅回复“无法分析”或“建议参考其他数据”。您的目标是在数据有限的情况下，依然通过新闻舆情提供有价值的洞察。"""
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "您是一位有用的AI助手，与其他助手协作。"
                    " 使用提供的工具来推进回答问题。"
                    " 如果您无法完全回答，没关系；具有不同工具的其他助手"
                    " 将从您停下的地方继续帮助。执行您能做的以取得进展。"
                    " 如果您或任何其他助手有最终交易提案：**买入/持有/卖出**或可交付成果，"
                    " 请在您的回应前加上最终交易提案：**买入/持有/卖出**，以便团队知道停止。"
                    " 您可以访问以下工具：{tool_names}。\n{system_message}"
                    "\n\n📋 分析对象（必须严格遵守，不得混淆为其他股票）："
                    "\n- 公司名称：{company_name}"
                    "\n- 股票代码：{ticker}"
                    "\n- 所属市场：{market_name}"
                    "\n\n⚠️ 身份识别强制约束："
                    "\n1. 你分析的唯一对象是 **{company_name}**（代码 {ticker}）。"
                    "\n2. **绝对禁止**混淆为其他市场的同名或同代码股票。"
                    "\n3. 如果代码是纯数字（如 01810），必须结合其所属市场（港股）确认为“小米集团”，而不是其他可能的含义。"
                    "\n\n供您参考，当前日期是{current_date}。请用中文撰写所有分析内容。",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        # 安全地获取工具名称，处理函数和工具对象
        tool_names = []
        for tool in tools:
            if hasattr(tool, 'name'):
                tool_names.append(tool.name)
            elif hasattr(tool, '__name__'):
                tool_names.append(tool.__name__)
            else:
                tool_names.append(str(tool))

        prompt = prompt.partial(tool_names=", ".join(tool_names))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)
        prompt = prompt.partial(company_name=company_name)
        prompt = prompt.partial(market_name=market_info['market_name'])

        chain = prompt | llm.bind_tools(tools)

        # 修复：传递字典而不是直接传递消息列表，以便 ChatPromptTemplate 能正确处理所有变量
        result = chain.invoke({"messages": state["messages"]})

        # 使用统一的Google工具调用处理器
        if GoogleToolCallHandler.is_google_model(llm):
            logger.info(f"📊 [社交媒体分析师] 检测到Google模型，使用统一工具调用处理器")
            
            # 创建分析提示词
            analysis_prompt_template = GoogleToolCallHandler.create_analysis_prompt(
                ticker=ticker,
                company_name=company_name,
                analyst_type="社交媒体情绪分析",
                specific_requirements="重点关注投资者情绪、社交媒体讨论热度、舆论影响等。"
            )
            
            # 处理Google模型工具调用
            report, messages = GoogleToolCallHandler.handle_google_tool_calls(
                result=result,
                llm=llm,
                tools=tools,
                state=state,
                analysis_prompt_template=analysis_prompt_template,
                analyst_name="社交媒体分析师"
            )
        else:
            # 非Google模型的处理逻辑（完整版本，从market_analyst复制）
            logger.info(f"📊 [社交媒体分析师] 非Google模型 ({llm.__class__.__name__})，使用标准处理逻辑")
            
            # 处理情绪分析报告
            if len(result.tool_calls) == 0:
                # 没有工具调用：强制拉取一次情绪/新闻数据，避免输出无数据的空泛报告
                logger.warning(f"📊 [社交媒体分析师] ⚠️ 未检测到工具调用，执行强制数据获取以提升报告质量")
                try:
                    from langchain_core.messages import ToolMessage

                    forced_tool = None
                    forced_args = None
                    fallback_tool = None
                    fallback_args = None

                    if market_info['is_us']:
                        forced_tool = next((t for t in tools if getattr(t, 'name', getattr(t, '__name__', '')) == 'get_combined_sentiment'), None)
                        forced_args = {"ticker": ticker}
                    else:
                        fallback_tool = next((t for t in tools if getattr(t, 'name', getattr(t, '__name__', '')) == 'get_chinese_social_sentiment'), None)
                        fallback_args = {"ticker": ticker, "curr_date": current_date}

                        # 优先尝试 Serper 统一情绪（更像“社交媒体”），但如果没配置 key 直接降级
                        import os
                        serper_api_key = os.getenv("SERPER_API_KEY")
                        if serper_api_key:
                            forced_tool = next((t for t in tools if getattr(t, 'name', getattr(t, '__name__', '')) == 'get_stock_sentiment_unified'), None)
                            forced_args = {"ticker": ticker, "curr_date": current_date}
                        else:
                            forced_tool = fallback_tool
                            forced_args = fallback_args

                    if forced_tool is None:
                        raise RuntimeError("No available sentiment tool for forced fetch")

                    forced_result = _invoke_tool(forced_tool, forced_args)

                    # 如果美股情绪工具不可用（例如缺少ALPHA_VANTAGE_API_KEY），降级到统一新闻
                    if market_info['is_us']:
                        forced_result_str = str(forced_result)
                        forced_result_is_error = False
                        if isinstance(forced_result, dict) and forced_result.get("status") == "error":
                            forced_result_is_error = True
                        if "ALPHA_VANTAGE_API_KEY" in forced_result_str or "API Key" in forced_result_str or "未配置" in forced_result_str:
                            forced_result_is_error = True
                        if forced_result_is_error:
                            logger.warning("📊 [社交媒体分析师] ⚠️ Alpha Vantage情绪不可用，降级到统一新闻工具")
                            news_tool = next((t for t in tools if getattr(t, 'name', getattr(t, '__name__', '')) == 'get_stock_news_unified'), None)
                            if news_tool is not None:
                                forced_result = _invoke_tool(news_tool, {"stock_code": ticker, "max_news": 36})

                    # 如果统一情绪工具返回错误（例如缺少SERPER_API_KEY），尝试降级到中文市场情绪
                    if (not market_info['is_us']) and fallback_tool is not None and fallback_tool is not forced_tool:
                        forced_result_str = str(forced_result)
                        forced_result_is_error = False
                        if isinstance(forced_result, dict) and forced_result.get("status") == "error":
                            forced_result_is_error = True
                        if "SERPER_API_KEY" in forced_result_str or "未配置SERPER_API_KEY" in forced_result_str:
                            forced_result_is_error = True
                        if forced_result_is_error:
                            logger.warning("📊 [社交媒体分析师] ⚠️ 统一情绪工具不可用，降级到中文市场情绪工具")
                            forced_result = _invoke_tool(fallback_tool, fallback_args)

                    tool_messages_for_report = [ToolMessage(content=str(forced_result), tool_call_id="forced_social_sentiment")]

                    # 如果中文市场情绪数据仍然过短/信息量不足，补充统一新闻数据
                    if not market_info['is_us']:
                        forced_result_str = str(forced_result)
                        sentiment_too_short = len(forced_result_str.strip()) < 400
                        sentiment_seems_limited = ("数据获取限制" in forced_result_str) or ("API" in forced_result_str) or ("新闻数量: 0" in forced_result_str) or ("数据不足" in forced_result_str)
                        if sentiment_too_short or sentiment_seems_limited:
                            news_tool = next((t for t in tools if getattr(t, 'name', getattr(t, '__name__', '')) == 'get_stock_news_unified'), None)
                            if news_tool is not None:
                                logger.info("📊 [社交媒体分析师] 补充获取统一新闻数据以提升报告质量")
                                news_result = _invoke_tool(news_tool, {"stock_code": ticker, "max_news": 36})
                                tool_messages_for_report.append(ToolMessage(content=str(news_result), tool_call_id="forced_social_news"))

                    updated_messages = state["messages"] + tool_messages_for_report

                    final_prompt = ChatPromptTemplate.from_messages([
                        (
                            "system",
                            "你是一位专业的社交媒体和投资情绪分析师。"
                            "\n\n📋 分析对象（必须严格遵守，不得混淆为其他股票）："
                            "\n- 公司名称：{company_name}"
                            "\n- 股票代码：{ticker}"
                            "\n- 所属市场：{market_name}"
                            "\n\n⚠️ 身份识别强制约束："
                            "\n1. 你分析的唯一对象是 **{company_name}**（代码 {ticker}）。"
                            "\n2. **绝对禁止**混淆为其他市场的同名或同代码股票。"
                            "\n\n请基于提供的工具数据，生成一份完整的市场情绪分析报告。"
                        ),
                        MessagesPlaceholder(variable_name="messages"),
                        ("human", "请基于上述工具数据，生成完整的市场情绪分析报告。")
                    ])

                    final_chain = (
                        final_prompt.partial(company_name=company_name)
                        .partial(ticker=ticker)
                        .partial(market_name=market_info['market_name'])
                        | llm
                    )
                    final_result = final_chain.invoke({"messages": updated_messages})
                    report = final_result.content
                    logger.info(f"📊 [社交媒体分析师] ✅ 强制数据获取后报告生成完成，长度: {len(report)}")
                except Exception as e:
                    report = result.content
                    logger.error(f"❌ [社交媒体分析师] 强制数据获取失败，回退到直接回复: {e}")
            else:
                # 有工具调用，执行工具并生成完整分析报告
                logger.info(f"📊 [社交媒体分析师] 🔧 检测到工具调用: {[call.get('name', 'unknown') for call in result.tool_calls]}")

                try:
                    # 执行工具调用
                    from langchain_core.messages import ToolMessage, HumanMessage

                    tool_messages = []
                    for tool_call in result.tool_calls:
                        tool_name = tool_call.get('name')
                        tool_args = tool_call.get('args', {})
                        tool_id = tool_call.get('id')

                        logger.info(f"📊 [社交媒体分析师] 执行工具: {tool_name}, 参数: {tool_args}")

                        # 找到对应的工具并执行
                        tool_result = None
                        for tool in tools:
                            # 安全地获取工具名称进行比较
                            current_tool_name = None
                            if hasattr(tool, 'name'):
                                current_tool_name = tool.name
                            elif hasattr(tool, '__name__'):
                                current_tool_name = tool.__name__

                            if current_tool_name == tool_name:
                                try:
                                    tool_result = _invoke_tool(tool, tool_args)
                                    logger.info(f"📊 [社交媒体分析师] 工具执行成功，结果长度: {len(str(tool_result))}")
                                    break
                                except Exception as tool_error:
                                    logger.error(f"❌ [社交媒体分析师] 工具执行失败: {tool_error}")
                                    tool_result = f"工具执行失败: {str(tool_error)}"

                        if tool_result is None:
                            tool_result = f"未找到工具: {tool_name}"

                        # 创建工具消息
                        tool_message = ToolMessage(
                            content=str(tool_result),
                            tool_call_id=tool_id
                        )
                        tool_messages.append(tool_message)

                    logger.info(f"📊 [社交媒体分析师] 工具执行完成，共{len(tool_messages)}个结果")

                    # 将工具结果添加到消息历史
                    updated_messages = state["messages"] + [result] + tool_messages

                    # 要求LLM基于工具结果生成最终报告
                    logger.info(f"📊 [社交媒体分析师] 要求LLM生成最终报告...")
                    final_prompt = ChatPromptTemplate.from_messages([
                        (
                            "system",
                            "你是一位专业的社交媒体和投资情绪分析师。"
                            "\n\n📋 分析对象（必须严格遵守，不得混淆为其他股票）："
                            "\n- 公司名称：{company_name}"
                            "\n- 股票代码：{ticker}"
                            "\n- 所属市场：{market_name}"
                            "\n\n⚠️ 身份识别强制约束："
                            "\n1. 你分析的唯一对象是 **{company_name}**（代码 {ticker}）。"
                            "\n2. **绝对禁止**混淆为其他市场的同名或同代码股票。"
                            "\n\n请基于工具返回的数据，生成一份完整的市场情绪分析报告。"
                        ),
                        MessagesPlaceholder(variable_name="messages"),
                        ("human", "请基于上述工具数据，生成完整的市场情绪分析报告。")
                    ])

                    final_chain = (
                        final_prompt.partial(company_name=company_name)
                        .partial(ticker=ticker)
                        .partial(market_name=market_info['market_name'])
                        | llm
                    )
                    final_result = final_chain.invoke({"messages": updated_messages})
                    report = final_result.content
                    logger.info(f"📊 [社交媒体分析师] ✅ 最终报告生成完成，长度: {len(report)}")

                except Exception as e:
                    logger.error(f"❌ [社交媒体分析师] 工具调用处理失败: {e}")
                    import traceback
                    traceback.print_exc()
                    report = f"情绪分析失败: {str(e)}"

        # 🔧 更新工具调用计数器
        return {
            "messages": [result],
            "sentiment_report": report,
            "sentiment_tool_call_count": tool_call_count + 1
        }

    return social_media_analyst_node
