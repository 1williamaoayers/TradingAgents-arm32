
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from pymongo import MongoClient
import shutil

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# Setup paths
if Path('/app').exists():
    BASE_DIR = Path('/app')
else:
    BASE_DIR = Path('/trae/TradingAgents-arm32')

sys.path.append(str(BASE_DIR))

# Import saving utility
from web.utils.mongodb_report_manager import MongoDBReportManager
from web.utils.report_exporter import save_modular_reports_to_results_dir

def recover_reports():
    print("开始恢复测试报告...")
    
    # Path to JSON log
    log_file = BASE_DIR / 'eval_results/01810.HK/TradingAgentsStrategy_logs/full_states_log.json'
    if not log_file.exists():
        print(f"❌ 日志文件不存在: {log_file}")
        sys.exit(1)
        
    # Read JSON
    with open(log_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Get the latest entry (key is date)
    latest_date = sorted(data.keys())[-1]
    print(f"找到最新记录: {latest_date}")
    state_data = data[latest_date]
    
    # Extract reports
    reports = {
        'market_report': state_data.get('market_report', ''),
        'sentiment_report': state_data.get('sentiment_report', ''),
        'news_report': state_data.get('news_report', ''),
        'fundamentals_report': state_data.get('fundamentals_report', ''),
        'investment_plan': state_data.get('investment_plan', ''),
        'trader_investment_plan': state_data.get('trader_investment_decision', ''),
        'final_trade_decision': state_data.get('final_trade_decision', ''),
    }
    
    # Extract debate history for detailed reports
    bull_history = state_data['investment_debate_state'].get('bull_history', [])
    bear_history = state_data['investment_debate_state'].get('bear_history', [])
    risk_judge_decision = state_data['risk_debate_state'].get('judge_decision', '')
    
    reports['research_team_decision'] = f"## 多方观点\n{bull_history}\n\n## 空方观点\n{bear_history}"
    reports['risk_management_decision'] = risk_judge_decision
    
    # Save to Disk
    stock_code = '01810'
    stock_name = '小米集团'
    analysis_date = datetime.now()
    analysis_id = f"{stock_code}_{analysis_date.strftime('%Y%m%d_%H%M%S')}"
    
    print("正在保存到文件系统...")
    # Mock analysis_results for exporter
    analysis_results = {
        "reports": reports,
        "parameters": {"ticker": stock_code},
        "analysis_date": analysis_date.strftime('%Y-%m-%d')
    }
    
    try:
        saved_files = save_modular_reports_to_results_dir(analysis_results, stock_code)
        print(f"✅ 文件保存成功，共 {len(saved_files)} 个文件")
        
        # 如果自动保存失败（文件数为0），强制手动保存
        if len(saved_files) == 0:
            print("⚠️ 自动保存文件数为0，尝试手动保存...")
            result_dir = BASE_DIR / 'results' / stock_code / analysis_date.strftime('%Y-%m-%d') / 'reports'
            result_dir.mkdir(parents=True, exist_ok=True)
            for name, content in reports.items():
                if content:
                    with open(result_dir / f"{name}.md", 'w', encoding='utf-8') as f:
                        f.write(content)
            print(f"✅ (手动) 文件保存成功到 {result_dir}")
            
    except Exception as e:
        print(f"❌ 文件保存失败: {e}")
        # Manual fallback
        result_dir = BASE_DIR / 'results' / stock_code / analysis_date.strftime('%Y-%m-%d') / 'reports'
        result_dir.mkdir(parents=True, exist_ok=True)
        for name, content in reports.items():
            if content:
                with open(result_dir / f"{name}.md", 'w', encoding='utf-8') as f:
                    f.write(content)
        print(f"✅ (手动) 文件保存成功到 {result_dir}")

    # Save to MongoDB
    print("正在保存到MongoDB...")
    try:
        mongo_manager = MongoDBReportManager()
        mongo_manager.save_analysis_report(
            stock_symbol=stock_code,
            analysis_results={
                "summary": state_data.get('final_trade_decision', ''),
                "analysts": ["market", "news", "fundamentals", "sentiment"],
                "research_depth": 1,
                "model_info": {"provider": "dashscope", "fast_model": "qwen-turbo", "deep_model": "qwen-plus"}
            },
            reports=reports
        )
        print("✅ MongoDB保存成功")
    except Exception as e:
        print(f"❌ MongoDB保存失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    recover_reports()
