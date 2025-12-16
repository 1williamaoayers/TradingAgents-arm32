#!/usr/bin/env python3
"""
快速测试改进后的数据库查询
"""
import sys
sys.path.insert(0, '/app')

print("=== 快速测试数据库查询改进 ===\n")

# 1. 检查数据库
from tradingagents.dataflows.cache.app_adapter import get_mongodb_client

client = get_mongodb_client()
db = client['tradingagents']
collection = db['stock_news']

total = collection.count_documents({})
print(f"1. 数据库总新闻数: {total}")

# 2. 查看是否有包含"京东"的新闻
jd_in_title = collection.count_documents({'title': {'$regex': '京东', '$options': 'i'}})
print(f"2. 标题包含'京东'的新闻: {jd_in_title}条")

# 3. 查看是否有包含"JD"的新闻
jd_code = collection.count_documents({'title': {'$regex': 'JD', '$options': 'i'}})
print(f"3. 标题包含'JD'的新闻: {jd_code}条")

# 4. 查看前5条新闻的标题
print(f"\n4. 前5条新闻标题:")
for i, news in enumerate(collection.find().limit(5), 1):
    title = news.get('title', '无标题')
    symbol = news.get('symbol', '无')
    print(f"   {i}. [{symbol}] {title[:50]}...")

print("\n测试完成！")
