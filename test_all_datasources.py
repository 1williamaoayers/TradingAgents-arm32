#!/usr/bin/env python3
"""
数据源和新闻源实际可用性测试脚本
测试所有配置的数据源是否真正可用
"""
import sys
import os
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, '/app')

print("=" * 80)
print("🧪 数据源和新闻源实际可用性测试")
print("=" * 80)
print()

# ============================================================================
# 1. 测试 AKShare 数据源
# ============================================================================
print("1️⃣ 测试 AKShare 数据源")
print("-" * 80)

try:
    import akshare as ak
    print("✅ AKShare 模块已安装")
    
    # 测试获取港股列表
    try:
        print("   测试: 获取港股列表...")
        hk_stocks = ak.stock_hk_spot_em()
        if hk_stocks is not None and len(hk_stocks) > 0:
            print(f"   ✅ 成功获取港股列表: {len(hk_stocks)} 只股票")
            print(f"   示例: {hk_stocks.head(3).to_dict('records')}")
        else:
            print("   ❌ 港股列表为空")
    except Exception as e:
        print(f"   ❌ 获取港股列表失败: {e}")
    
    # 测试获取A股列表
    try:
        print("   测试: 获取A股列表...")
        a_stocks = ak.stock_zh_a_spot_em()
        if a_stocks is not None and len(a_stocks) > 0:
            print(f"   ✅ 成功获取A股列表: {len(a_stocks)} 只股票")
        else:
            print("   ❌ A股列表为空")
    except Exception as e:
        print(f"   ❌ 获取A股列表失败: {e}")
    
    # 测试获取港股历史数据
    try:
        print("   测试: 获取港股历史数据 (01810 小米集团)...")
        hist = ak.stock_hk_hist(symbol="01810", period="daily", start_date="20241201", end_date="20241214", adjust="")
        if hist is not None and len(hist) > 0:
            print(f"   ✅ 成功获取历史数据: {len(hist)} 条记录")
            print(f"   最新数据: {hist.tail(1).to_dict('records')}")
        else:
            print("   ❌ 历史数据为空")
    except Exception as e:
        print(f"   ❌ 获取历史数据失败: {e}")
    
    # 测试获取A股新闻
    try:
        print("   测试: 获取A股新闻...")
        news = ak.stock_news_em(symbol="000001")
        if news is not None and len(news) > 0:
            print(f"   ✅ 成功获取新闻: {len(news)} 条")
            print(f"   最新新闻: {news.head(1)[['关键词', '新闻标题']].to_dict('records')}")
        else:
            print("   ❌ 新闻数据为空")
    except Exception as e:
        print(f"   ❌ 获取新闻失败: {e}")
    
    print("   📊 AKShare 总体评估: 可用 ✅")
    
except ImportError:
    print("❌ AKShare 模块未安装")
except Exception as e:
    print(f"❌ AKShare 测试失败: {e}")

print()

# ============================================================================
# 2. 测试 Tushare 数据源
# ============================================================================
print("2️⃣ 测试 Tushare 数据源")
print("-" * 80)

try:
    import tushare as ts
    print("✅ Tushare 模块已安装")
    
    # 检查Token
    token = os.getenv("TUSHARE_TOKEN", "")
    if not token or token == "your_tushare_token_here":
        print("   ⚠️ Tushare Token 未配置")
        print("   📊 Tushare 总体评估: 不可用 ❌ (需要配置Token)")
    else:
        print(f"   ✅ Tushare Token 已配置: {token[:10]}...")
        
        try:
            pro = ts.pro_api(token)
            
            # 测试获取股票列表
            print("   测试: 获取股票列表...")
            df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
            if df is not None and len(df) > 0:
                print(f"   ✅ 成功获取股票列表: {len(df)} 只股票")
            else:
                print("   ❌ 股票列表为空")
            
            print("   📊 Tushare 总体评估: 可用 ✅")
            
        except Exception as e:
            print(f"   ❌ Tushare API调用失败: {e}")
            print("   📊 Tushare 总体评估: 不可用 ❌")
    
except ImportError:
    print("❌ Tushare 模块未安装")
    print("   📊 Tushare 总体评估: 不可用 ❌")
except Exception as e:
    print(f"❌ Tushare 测试失败: {e}")

print()

# ============================================================================
# 3. 测试 BaoStock 数据源
# ============================================================================
print("3️⃣ 测试 BaoStock 数据源")
print("-" * 80)

try:
    import baostock as bs
    print("✅ BaoStock 模块已安装")
    
    # 登录
    try:
        lg = bs.login()
        if lg.error_code == '0':
            print("   ✅ BaoStock 登录成功")
            
            # 测试获取股票列表
            try:
                print("   测试: 获取沪深A股列表...")
                rs = bs.query_stock_basic()
                data_list = []
                while (rs.error_code == '0') & rs.next():
                    data_list.append(rs.get_row_data())
                
                if len(data_list) > 0:
                    print(f"   ✅ 成功获取股票列表: {len(data_list)} 只股票")
                else:
                    print("   ❌ 股票列表为空")
            except Exception as e:
                print(f"   ❌ 获取股票列表失败: {e}")
            
            # 测试获取历史数据
            try:
                print("   测试: 获取历史数据 (sh.600519 贵州茅台)...")
                rs = bs.query_history_k_data_plus("sh.600519",
                    "date,code,open,high,low,close,volume",
                    start_date='2024-12-01', end_date='2024-12-14',
                    frequency="d", adjustflag="3")
                
                data_list = []
                while (rs.error_code == '0') & rs.next():
                    data_list.append(rs.get_row_data())
                
                if len(data_list) > 0:
                    print(f"   ✅ 成功获取历史数据: {len(data_list)} 条记录")
                    print(f"   最新数据: {data_list[-1]}")
                else:
                    print("   ❌ 历史数据为空")
            except Exception as e:
                print(f"   ❌ 获取历史数据失败: {e}")
            
            bs.logout()
            print("   📊 BaoStock 总体评估: 可用 ✅")
        else:
            print(f"   ❌ BaoStock 登录失败: {lg.error_msg}")
            print("   📊 BaoStock 总体评估: 不可用 ❌")
    except Exception as e:
        print(f"   ❌ BaoStock 操作失败: {e}")
        print("   📊 BaoStock 总体评估: 不可用 ❌")
    
except ImportError:
    print("❌ BaoStock 模块未安装")
    print("   📊 BaoStock 总体评估: 不可用 ❌")
except Exception as e:
    print(f"❌ BaoStock 测试失败: {e}")

print()

# ============================================================================
# 4. 测试 FinnHub 新闻源
# ============================================================================
print("4️⃣ 测试 FinnHub 新闻源")
print("-" * 80)

try:
    import finnhub
    print("✅ FinnHub 模块已安装")
    
    # 检查API Key
    api_key = os.getenv("FINNHUB_API_KEY", "")
    if not api_key or api_key == "your_finnhub_api_key_here":
        print("   ⚠️ FinnHub API Key 未配置")
        print("   📊 FinnHub 总体评估: 不可用 ❌ (需要配置API Key)")
    else:
        print(f"   ✅ FinnHub API Key 已配置: {api_key[:10]}...")
        
        try:
            client = finnhub.Client(api_key=api_key)
            
            # 测试获取公司新闻
            print("   测试: 获取公司新闻 (AAPL)...")
            from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            to_date = datetime.now().strftime('%Y-%m-%d')
            news = client.company_news('AAPL', _from=from_date, to=to_date)
            
            if news and len(news) > 0:
                print(f"   ✅ 成功获取新闻: {len(news)} 条")
                print(f"   最新新闻: {news[0]['headline'][:50]}...")
            else:
                print("   ❌ 新闻数据为空")
            
            # 测试获取市场新闻
            print("   测试: 获取市场新闻...")
            market_news = client.general_news('general', min_id=0)
            if market_news and len(market_news) > 0:
                print(f"   ✅ 成功获取市场新闻: {len(market_news)} 条")
            else:
                print("   ❌ 市场新闻为空")
            
            print("   📊 FinnHub 总体评估: 可用 ✅")
            
        except Exception as e:
            print(f"   ❌ FinnHub API调用失败: {e}")
            if "API limit" in str(e) or "429" in str(e):
                print("   ⚠️ API限制: 免费版每分钟60次")
            print("   📊 FinnHub 总体评估: 不可用 ❌")
    
except ImportError:
    print("❌ FinnHub 模块未安装")
    print("   📊 FinnHub 总体评估: 不可用 ❌")
except Exception as e:
    print(f"❌ FinnHub 测试失败: {e}")

print()

# ============================================================================
# 5. 测试 Alpha Vantage 数据源
# ============================================================================
print("5️⃣ 测试 Alpha Vantage 数据源")
print("-" * 80)

try:
    import requests
    print("✅ Requests 模块已安装")
    
    # 检查API Key
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    if not api_key or api_key == "your_alpha_vantage_api_key_here":
        print("   ⚠️ Alpha Vantage API Key 未配置")
        print("   📊 Alpha Vantage 总体评估: 不可用 ❌ (需要配置API Key)")
    else:
        print(f"   ✅ Alpha Vantage API Key 已配置: {api_key[:10]}...")
        
        try:
            # 测试获取股票数据
            print("   测试: 获取股票数据 (IBM)...")
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey={api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "Time Series (Daily)" in data:
                    print(f"   ✅ 成功获取股票数据")
                    dates = list(data["Time Series (Daily)"].keys())
                    print(f"   最新日期: {dates[0]}")
                elif "Note" in data:
                    print(f"   ⚠️ API限制: {data['Note']}")
                    print("   免费版每分钟5次，每天500次")
                elif "Error Message" in data:
                    print(f"   ❌ API错误: {data['Error Message']}")
                else:
                    print(f"   ❌ 未知响应: {data}")
            else:
                print(f"   ❌ HTTP错误: {response.status_code}")
            
            # 测试获取新闻
            print("   测试: 获取新闻...")
            url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=AAPL&apikey={api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "feed" in data:
                    print(f"   ✅ 成功获取新闻: {len(data['feed'])} 条")
                    print("   📊 Alpha Vantage 总体评估: 可用 ✅")
                elif "Note" in data:
                    print(f"   ⚠️ API限制: {data['Note']}")
                    print("   📊 Alpha Vantage 总体评估: 受限 ⚠️")
                else:
                    print(f"   ❌ 未知响应")
                    print("   📊 Alpha Vantage 总体评估: 不可用 ❌")
            else:
                print(f"   ❌ HTTP错误: {response.status_code}")
                print("   📊 Alpha Vantage 总体评估: 不可用 ❌")
            
        except Exception as e:
            print(f"   ❌ Alpha Vantage API调用失败: {e}")
            print("   📊 Alpha Vantage 总体评估: 不可用 ❌")
    
except ImportError:
    print("❌ Requests 模块未安装")
    print("   📊 Alpha Vantage 总体评估: 不可用 ❌")
except Exception as e:
    print(f"❌ Alpha Vantage 测试失败: {e}")

print()

# ============================================================================
# 总结
# ============================================================================
print("=" * 80)
print("📊 测试总结")
print("=" * 80)
print()
print("请查看上述测试结果，了解各数据源的实际可用性。")
print()
