
import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# 修复 sqlite3 版本问题
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# 加载环境变量
load_dotenv()

# 添加项目根目录到 Python 路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入必要的模块
from tradingagents.graph import TradingAgentsGraph
from tradingagents.agents.utils.agent_states import AgentState

def check_environment():
    """检查环境变量"""
    required_keys = [
        "DEEPSEEK_API_KEY",
        "DASHSCOPE_API_KEY"
    ]
    
    missing_keys = []
    for key in required_keys:
        if not os.getenv(key):
            missing_keys.append(key)
    
    if missing_keys:
        print(f"❌ 错误: 缺少必要的环境变量: {', '.join(missing_keys)}")
        sys.exit(1)
    
    # 检查社交媒体分析师特定的配置（如果有的话，目前主要是基于搜索）
    # 注意：如果代码使用 Serper 或 Twitter API，需要在这里检查
    # 根据现有代码，可能依赖搜索工具
    
    print("✅ 环境变量检查通过")

async def run_test():
    """运行测试"""
    print("🚀 开始社交媒体分析师模块测试: 09618.HK (京东集团-SW)")
    
    # 初始化图
    print("📦 初始化 TradingAgentsGraph (仅启用 Social Analyst)...")
    try:
        # 配置图参数
        config = {
            "llm_provider": "openai",  # 使用 OpenAI 兼容模式
            "deep_think_llm": "deepseek-chat", # 使用 DeepSeek V3
            "quick_think_llm": "deepseek-chat",
            "backend_url": "https://api.deepseek.com",
            "project_dir": project_root,
            "memory_enabled": True
        }
        
        # 仅启用社交媒体分析师
        selected_analysts = ["social"]
        
        graph = TradingAgentsGraph(
            selected_analysts=selected_analysts,
            debug=True,
            config=config
        )
        
        # 编译工作流
        workflow = graph.graph_setup.setup_graph(selected_analysts=selected_analysts)
        
        print("✅ 工作流编译成功")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 准备初始状态
    initial_state = {
        "messages": [],
        "company_of_interest": "09618.HK",
        "market_type": "HK",  # 显式设置为 HK
        "trade_date": datetime.now().strftime("%Y-%m-%d"),
        "start_date": "2024-01-01", 
        "end_date": datetime.now().strftime("%Y-%m-%d"),
        "analyst_signals": {},
        "debate_history": [],
        "investment_debate_state": {
            "bull_history": "",
            "bear_history": "",
            "history": "",
            "current_response": "",
            "judge_decision": "",
            "count": 0
        },
        "risk_debate_state": {
            "risky_history": "",
            "safe_history": "",
            "neutral_history": "",
            "history": "",
            "latest_speaker": "",
            "current_risky_response": "",
            "current_safe_response": "",
            "current_neutral_response": "",
            "judge_decision": "",
            "count": 0
        },
        "risk_assessment": {},
        "final_decision": {},
        # 初始化计数器
        "market_tool_call_count": 0,
        "news_tool_call_count": 0,
        "sentiment_tool_call_count": 0,
        "fundamentals_tool_call_count": 0,
        # 初始化为空报告，防止 KeyError
        "market_report": "",
        "sentiment_report": "",
        "news_report": "",
        "fundamentals_report": ""
    }
    
    print(f"🔄 开始执行工作流...")
    
    try:
        # 运行工作流
        final_state = await workflow.ainvoke(initial_state)
        
        print("\n" + "="*50)
        print("✅ 测试完成! 社交媒体分析师输出结果:")
        print("="*50)
        
        # 打印社交媒体分析师的信号
        if "analyst_signals" in final_state:
            signal = final_state["analyst_signals"].get("social")
            if signal:
                print(f"\n📊 [SOCIAL 分析师]:")
                print(f"信号: {signal.get('signal', 'N/A')}")
                print(f"置信度: {signal.get('confidence', 'N/A')}")
                print(f"摘要: {signal.get('reasoning', 'N/A')}")
                print("\n🔍 原始分析报告 (sentiment_report):")
                print("-" * 30)
                print(final_state.get("sentiment_report", "未找到 sentiment_report"))
            else:
                print("⚠️ 未找到 'social' 分析师的信号输出。")
        else:
            print("⚠️ final_state 中没有 analyst_signals 字段。")
            
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    check_environment()
    asyncio.run(run_test())
