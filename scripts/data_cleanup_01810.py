#!/usr/bin/env python3
"""
01810 历史噪声数据清理脚本
用于删除 MongoDB 中误标记为 01810 的基金相关新闻。
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from tradingagents.config.database_manager import get_database_manager

def cleanup_01810_noise():
    mgr = get_database_manager()
    if not mgr.is_mongodb_available():
        print("❌ MongoDB 不可用，请检查配置。")
        return

    db = mgr.get_mongodb_db()
    col = db.stock_news

    # 定义噪声特征关键词
    noise_keywords = ["基金", "份额", "净值", "中欧", "分红", "派息", "认购", "回购(基金)"]
    
    # 构建正则表达式
    pattern = "|".join(noise_keywords)
    
    query = {
        "symbol": "01810",
        "$or": [
            {"title": {"$regex": pattern}},
            {"content": {"$regex": pattern}},
            {"summary": {"$regex": pattern}}
        ]
    }

    # 先统计
    count = col.count_documents(query)
    print(f"🔍 发现 {count} 条疑似 01810 基金噪声数据。")

    if count > 0:
        # 执行删除
        result = col.delete_many(query)
        print(f"✅ 成功清理 {result.deleted_count} 条条噪音数据。")
    else:
        print("⭕️ 未发现需要清理的数据。")

if __name__ == "__main__":
    cleanup_01810_noise()
