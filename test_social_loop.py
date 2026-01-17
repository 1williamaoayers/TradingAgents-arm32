
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 环境准备
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))
load_dotenv()

from tradingagents.tools.unified_news_tool import UnifiedNewsAnalyzer
from openai import OpenAI

# 模拟 SocialMediaAnalyst 的核心提示词
SYSTEM_PROMPT = """您是一位专业的中国市场社交媒体和投资情绪分析师，负责分析中国投资者对特定股票的讨论和情绪变化。

您的主要职责包括：
1. 分析中国主要财经平台的投资者情绪（如雪球、东方财富股吧等）
2. 监控财经媒体和新闻对股票的报道倾向
3. 评估情绪变化对股价的潜在影响

📈 必须包含：
- 情绪指数评分（1-10分）
- 投资者关注的核心话题
- 风险/利好研判

请撰写详细的中文分析报告。"""

class RealToolkit:
    def __init__(self):
        pass

async def run_sentiment_closed_loop():
    symbol = "01810" # 小米集团
    print(f"🎬 开始【情绪分析闭环验证】: {symbol} (小米集团)")
    
    # 1. 环节一：获取满血版社交舆情数据 (使用真实的 Serper)
    print("\n--- [环节 1: 真实舆情抓取] ---")
    analyzer = UnifiedNewsAnalyzer(RealToolkit())
    res = analyzer.get_stock_sentiment_unified(symbol, datetime.now().strftime("%Y-%m-%d"))
    
    sentiment_data = res.get("content", "")
    if not sentiment_data or res.get("status") == "error":
        print(f"❌ 舆情数据获取失败: {res.get('summary')}")
        return
        
    print(f"✅ 成功获取舆情数据，来源: {res.get('source')}, 长度: {len(sentiment_data)}")
    
    # 2. 环节二：AI 深度解读
    print("\n--- [环节 2: AI 深度解读] ---")
    
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    )
    
    user_input = f"请基于以下抓取到的实时社交媒体讨论和新闻，分析该股票的市场情绪：\n\n{sentiment_data}"
    
    print("🚀 正在调用 LLM 生成深度情绪报告...")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ]
    )
    
    report = response.choices[0].message.content
    print("\n" + "🌟" * 20)
    print("🎯 最終滿血版情緒分析報告:")
    print("🌟" * 20)
    print(report)
    print("\n" + "🌟" * 20)
    
    # 保存结果
    output_path = Path("sentiment_full_report.md")
    output_path.write_text(report, encoding="utf-8")
    print(f"\n✅ 報告已保存至: {output_path.absolute()}")

if __name__ == "__main__":
    asyncio.run(run_sentiment_closed_loop())
