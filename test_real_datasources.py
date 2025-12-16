#!/usr/bin/env python3
"""
真实数据源和新闻源可用性测试
使用真实API密钥，以港股09618（京东集团）为例
"""
import sys
import os
from datetime import datetime, timedelta

# 设置API密钥
os.environ['DASHSCOPE_API_KEY'] = 'sk-68ed54c06e434c108ee93cc6e482bb61'
os.environ['DEEPSEEK_API_KEY'] = 'sk-a1c794ab1969492aa06f7d1177af0451'
os.environ['FINNHUB_API_KEY'] = 'd3vh001r01qt2ctpo400d3vh001r01qt2ctpo40g'
os.environ['ALPHA_VANTAGE_API_KEY'] = 'MWB5V9SRYQ9ZH0UT'

sys.path.insert(0, '/app')

print("=" * 80)
print("🧪 真实数据源和新闻源可用性测试")
print("测试股票: 09618 (京东集团-SW)")
print("=" * 80)
print()

results = {
    'akshare': {'available': False, 'data': False, 'news': False},
    'tushare': {'available': False, 'data': False},
    'baostock': {'available': False, 'data': False},
    'finnhub': {'available': False, 'news': False},
    'alpha_vantage': {'available': False, 'news': False}
}

# ============================================================================
# 1. 测试 AKShare - 港股09618数据
# ============================================================================
print("1️⃣ 测试 AKShare 数据源 (港股09618)")
print("-" * 80)

try:
    import akshare as ak
    results['akshare']['available'] = True
    print("✅ AKShare 模块已安装")
    
    # 测试获取港股09618历史数据
    try:
        print("   测试: 获取09618历史数据...")
        hist = ak.stock_hk_hist(
            symbol="09618", 
            period="daily", 
            start_date="20241201", 
            end_date="20241214", 
            adjust=""
        )
        if hist is not None and len(hist) > 0:
            results['akshare']['data'] = True
            print(f"   ✅ 成功获取历史数据: {len(hist)} 条记录")
            print(f"   最新数据 (2024-12-13):")
            latest = hist.tail(1).to_dict('records')[0]
            print(f"      开盘: {latest['开盘']}, 收盘: {latest['收盘']}")
            print(f"      最高: {latest['最高']}, 最低: {latest['最低']}")
            print(f"      成交量: {latest['成交量']:,}")
        else:
            print("   ❌ 历史数据为空")
    except Exception as e:
        print(f"   ❌ 获取历史数据失败: {str(e)[:100]}")
    
    # 测试获取港股新闻（使用通用新闻）
    try:
        print("   测试: 获取港股新闻...")
        news = ak.stock_news_em(symbol="09618")
        if news is not None and len(news) > 0:
            results['akshare']['news'] = True
            print(f"   ✅ 成功获取新闻: {len(news)} 条")
            print(f"   最新新闻:")
            for i, item in enumerate(news.head(3).to_dict('records'), 1):
                print(f"      {i}. {item.get('新闻标题', 'N/A')[:50]}...")
        else:
            print("   ⚠️ 新闻数据为空")
    except Exception as e:
        print(f"   ⚠️ 获取新闻失败: {str(e)[:100]}")
    
except Exception as e:
    print(f"❌ AKShare 测试失败: {str(e)[:100]}")

print()

# ============================================================================
# 2. 测试 FinnHub - 港股新闻
# ============================================================================
print("2️⃣ 测试 FinnHub 新闻源")
print("-" * 80)

try:
    import finnhub
    results['finnhub']['available'] = True
    print("✅ FinnHub 模块已安装")
    print(f"✅ API Key: {os.environ['FINNHUB_API_KEY'][:15]}...")
    
    try:
        client = finnhub.Client(api_key=os.environ['FINNHUB_API_KEY'])
        
        # 测试获取JD.com新闻 (美股代码)
        print("   测试: 获取JD新闻 (美股代码JD)...")
        from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        news = client.company_news('JD', _from=from_date, to=to_date)
        
        if news and len(news) > 0:
            results['finnhub']['news'] = True
            print(f"   ✅ 成功获取JD新闻: {len(news)} 条")
            print(f"   最新新闻:")
            for i, item in enumerate(news[:3], 1):
                print(f"      {i}. {item['headline'][:60]}...")
                print(f"         来源: {item['source']}, 时间: {datetime.fromtimestamp(item['datetime']).strftime('%Y-%m-%d %H:%M')}")
        else:
            print("   ⚠️ JD新闻为空")
        
        # 测试获取通用市场新闻
        print("   测试: 获取通用市场新闻...")
        market_news = client.general_news('general', min_id=0)
        if market_news and len(market_news) > 0:
            print(f"   ✅ 成功获取市场新闻: {len(market_news)} 条")
            print(f"   示例新闻: {market_news[0]['headline'][:60]}...")
        else:
            print("   ⚠️ 市场新闻为空")
        
    except Exception as e:
        error_msg = str(e)
        print(f"   ❌ FinnHub API调用失败: {error_msg[:100]}")
        if "429" in error_msg or "limit" in error_msg.lower():
            print("   ⚠️ API限制: 免费版每分钟60次")
        
except Exception as e:
    print(f"❌ FinnHub 测试失败: {str(e)[:100]}")

print()

# ============================================================================
# 3. 测试 Alpha Vantage - 新闻
# ============================================================================
print("3️⃣ 测试 Alpha Vantage 新闻源")
print("-" * 80)

try:
    import requests
    results['alpha_vantage']['available'] = True
    print("✅ Requests 模块已安装")
    print(f"✅ API Key: {os.environ['ALPHA_VANTAGE_API_KEY'][:10]}...")
    
    try:
        # 测试获取JD新闻
        print("   测试: 获取JD新闻...")
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=JD&apikey={os.environ['ALPHA_VANTAGE_API_KEY']}"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if "feed" in data:
                results['alpha_vantage']['news'] = True
                print(f"   ✅ 成功获取新闻: {len(data['feed'])} 条")
                print(f"   最新新闻:")
                for i, item in enumerate(data['feed'][:3], 1):
                    print(f"      {i}. {item['title'][:60]}...")
                    print(f"         来源: {item['source']}, 时间: {item['time_published']}")
            elif "Note" in data:
                print(f"   ⚠️ API限制: {data['Note']}")
                print("   免费版: 每分钟5次，每天500次")
            elif "Information" in data:
                print(f"   ℹ️ {data['Information']}")
            else:
                print(f"   ❌ 未知响应: {list(data.keys())}")
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
        
    except Exception as e:
        print(f"   ❌ Alpha Vantage API调用失败: {str(e)[:100]}")
    
except Exception as e:
    print(f"❌ Alpha Vantage 测试失败: {str(e)[:100]}")

print()

# ============================================================================
# 4. 测试 Tushare
# ============================================================================
print("4️⃣ 测试 Tushare 数据源")
print("-" * 80)

try:
    import tushare as ts
    results['tushare']['available'] = True
    print("✅ Tushare 模块已安装")
    
    token = os.getenv("TUSHARE_TOKEN", "")
    if not token or token == "your_tushare_token_here":
        print("   ⚠️ Tushare Token 未配置")
        print("   💡 Tushare需要注册并获取Token")
    else:
        print(f"   ✅ Token已配置: {token[:10]}...")
        try:
            pro = ts.pro_api(token)
            df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name', limit=5)
            if df is not None and len(df) > 0:
                results['tushare']['data'] = True
                print(f"   ✅ API调用成功")
        except Exception as e:
            print(f"   ❌ API调用失败: {str(e)[:100]}")
    
except ImportError:
    print("❌ Tushare 模块未安装")
except Exception as e:
    print(f"❌ Tushare 测试失败: {str(e)[:100]}")

print()

# ============================================================================
# 5. 测试 BaoStock
# ============================================================================
print("5️⃣ 测试 BaoStock 数据源")
print("-" * 80)

try:
    import baostock as bs
    results['baostock']['available'] = True
    print("✅ BaoStock 模块已安装")
    
    try:
        lg = bs.login()
        if lg.error_code == '0':
            print("   ✅ 登录成功")
            
            # 测试获取数据
            rs = bs.query_history_k_data_plus("sh.600519",
                "date,code,close",
                start_date='2024-12-01', end_date='2024-12-14',
                frequency="d", adjustflag="3")
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            if len(data_list) > 0:
                results['baostock']['data'] = True
                print(f"   ✅ 成功获取数据: {len(data_list)} 条")
            
            bs.logout()
        else:
            print(f"   ❌ 登录失败: {lg.error_msg}")
    except Exception as e:
        print(f"   ❌ 操作失败: {str(e)[:100]}")
    
except ImportError:
    print("❌ BaoStock 模块未安装")
except Exception as e:
    print(f"❌ BaoStock 测试失败: {str(e)[:100]}")

print()

# ============================================================================
# 总结
# ============================================================================
print("=" * 80)
print("📊 测试结果总结")
print("=" * 80)
print()

print("数据源可用性:")
print(f"  AKShare:       {'✅ 可用' if results['akshare']['available'] else '❌ 不可用'}")
print(f"    - 港股数据:  {'✅ 可用' if results['akshare']['data'] else '❌ 不可用'}")
print(f"    - 新闻数据:  {'✅ 可用' if results['akshare']['news'] else '❌ 不可用'}")
print(f"  Tushare:       {'✅ 可用' if results['tushare']['available'] else '❌ 不可用'} (需Token)")
print(f"  BaoStock:      {'✅ 可用' if results['baostock']['available'] else '❌ 不可用'} (仅A股)")
print()

print("新闻源可用性:")
print(f"  FinnHub:       {'✅ 可用' if results['finnhub']['news'] else '❌ 不可用'}")
print(f"  Alpha Vantage: {'✅ 可用' if results['alpha_vantage']['news'] else '❌ 不可用'}")
print(f"  AKShare新闻:   {'✅ 可用' if results['akshare']['news'] else '❌ 不可用'}")
print()

# 推荐配置
print("💡 推荐配置:")
if results['akshare']['data']:
    print("  ✅ 港股数据: 使用 AKShare (免费、可用)")
if results['finnhub']['news']:
    print("  ✅ 新闻数据: 使用 FinnHub (免费、可用)")
elif results['alpha_vantage']['news']:
    print("  ✅ 新闻数据: 使用 Alpha Vantage (免费、可用)")
elif results['akshare']['news']:
    print("  ✅ 新闻数据: 使用 AKShare (免费、可用)")
else:
    print("  ⚠️ 新闻数据: 所有源均不可用")

print()
print("=" * 80)
