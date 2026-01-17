import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# 环境准备
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

from app.worker.news_utils.keyword_generator import get_keyword_generator
from tradingagents.dataflows.providers.china.akshare import get_akshare_provider
from openai import OpenAI

# 模拟 NewsAnalyst 的核心提示词 (从 news_analyst.py 提取)
SYSTEM_PROMPT = """您是一位专业的财经新闻分析师。
... (省略中间重复部分)
🧠 联想分析：若新闻摘要较短，请结合公司背景及近期关联关键词（如涉及的产品、关联人物、核心业务线）进行深度解读。
🚫 降噪提示：若发现抓取的新闻与主体公司明显不相关，请在报告开头用【数据噪声警告】明确标注。
请撰写详细的中文分析报告。"""

async def run_closed_loop_verification():
    symbol = "01810"
    print(f"🎬 开始【閉環驗證】: {symbol} (小米集团)")
    
    # 1. 环节一：AI 联想关键词
    print("\n--- [环节 1: AI 联想] ---")
    kw_gen = get_keyword_generator()
    keywords = await kw_gen.generate_keywords(symbol, "小米集团")
    print(f"✅ 生成关键词: {keywords}")
    
    # 2. 环节二：底层分流抓取 (使用修正后的补位逻辑)
    print("\n--- [环节 2: 精准抓取] ---")
    provider = get_akshare_provider()
    search_query = " ".join(keywords)
    # 扩大抓取数量以包含回购等技术新闻
    news_df = provider._get_stock_news_direct(symbol, limit=15, query=search_query)
    
    if news_df is None or news_df.empty:
        print("❌ 抓取失败，无法进行后续验证。")
        return
        
    news_items = []
    # 包含类型信息，帮助 AI 识别
    for _, row in news_df.iterrows():
        n_type = row.get('新闻类型', 'news')
        news_items.append(f"【{n_type}】标题: {row['新闻标题']}\n发布时间: {row['发布时间']}\n内容: {row['新闻内容']}")
    
    all_news_text = "\n\n".join(news_items)
    print(f"✅ 成功抓取到 {len(news_items)} 条高相关性内容 (含公告/回购)。")
    
    # 3. 环节三：AI 分析闭环 (模拟 NewsAnalyst 节点)
    print("\n--- [环节 3: AI 分析闭环] ---")
    
    # 使用最新的 Prompt 指令
    EXTENDED_PROMPT = SYSTEM_PROMPT + "\n📊 **分析核心**：必须主动研讨公司官方公告（Notice）、股权变动、股份回购、以及南向资金/北向资金流向。"
    
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    )
    
    user_input = f"请分析以下股票的新闻：\n股票代码: {symbol}\n关联词: {keywords}\n\n抓取到的内容清单:\n{all_news_text}"
    
    print("🚀 正在调用 LLM 进行最终分析...")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": EXTENDED_PROMPT},
            {"role": "user", "content": user_input}
        ]
    )
    
    report = response.choices[0].message.content
    print("\n" + "🏮" * 20)
    print("🎯 最終閉環分析報告結果:")
    print("🏮" * 20)
    print(report)
    print("\n" + "🏮" * 20)
    
    # 保存结果供用户查看
    with open("final_closed_loop_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n✅ 報告已保存至: final_closed_loop_report.md")

if __name__ == "__main__":
    asyncio.run(run_closed_loop_verification())
