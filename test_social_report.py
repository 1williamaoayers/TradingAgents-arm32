
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# 添加项目路径
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

# 加载环境变量
load_dotenv()

from tradingagents.agents.analysts.social_media_analyst import create_social_media_analyst
from tradingagents.utils.logging_init import setup_dataflow_logging
from langchain_openai import ChatOpenAI

class MockToolkit:
    def __init__(self):
        self.get_chinese_social_sentiment = lambda ticker, curr_date: "模拟社交情绪数据: 投资者普遍看好小米汽车进展。"

async def test():
    setup_dataflow_logging()
    
    # 初始化 LLM (使用 DeepSeek)
    llm = ChatOpenAI(
        model='deepseek-chat', 
        openai_api_key=os.getenv("DEEPSEEK_API_KEY"), 
        openai_api_base=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        max_tokens=2048
    )
    
    # 创建分析师节点
    toolkit = MockToolkit()
    analyst_node = create_social_media_analyst(llm, toolkit)
    
    # 构造状态
    state = {
        "messages": [],
        "trade_date": "2026-01-12",
        "company_of_interest": "01810",
        "sentiment_tool_call_count": 0
    }
    
    print("🚀 开始生成满血版社交舆情分析报告...")
    result =  analyst_node(state)
    
    report = result.get("sentiment_report", "")
    print("\n" + "="*50)
    print("📊 最终生成的社交舆情分析报告:")
    print("="*50 + "\n")
    print(report)
    print("\n" + "="*50)

    # 保存到文件
    output_path = Path("full_sentiment_test_report.md")
    output_path.write_text(report, encoding="utf-8")
    print(f"✅ 报告已保存至: {output_path.absolute()}")

if __name__ == "__main__":
    asyncio.run(test())
