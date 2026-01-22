#!/usr/bin/env python3
"""
自选股管理页面
用户可以添加、删除、查看自选股列表
数据存储在 MongoDB 数据库中
"""

import streamlit as st
from datetime import datetime
import sys
from pathlib import Path
import time  # 添加time模块导入
from pymongo import MongoClient  # 🔥 添加 MongoClient 导入

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.utils.logging_manager import get_logger

logger = get_logger(__name__)


def check_database_connection():
    """检查数据库连接状态"""
    try:
        
        # 强制使用 localhost，与验证脚本保持一致
        mongo_uri = "mongodb://admin:tradingagents123@mongodb:27017/?authSource=admin"
        
        print(f"[DEBUG] 尝试连接: {mongo_uri}")  # 调试输出
        
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        client.server_info()
        client.close()
        return True, "数据库连接正常"
    except Exception as e:
        print(f"[ERROR] 连接失败: {e}")  # 调试输出
        return False, f"数据库连接失败: {str(e)}"


def fetch_watchlist_from_db():
    """从 MongoDB 获取自选股列表（包含真实新闻数量）"""
    try:
        from pymongo import MongoClient
        
        mongo_uri = "mongodb://admin:tradingagents123@mongodb:27017/?authSource=admin"
        
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client["tradingagents"]
        
        # 使用默认用户 ID
        user_id = "default_user"
        user_doc = db.user_favorites.find_one({"user_id": user_id})
        
        if not user_doc:
            client.close()
            return []
        
        favorites = user_doc.get("favorites", [])
        result = []
        
        for fav in favorites:
            stock_code = fav.get("stock_code")
            
            # 🔥 查询真实新闻数量
            news_count = db.stock_news.count_documents({"symbol": stock_code})
            
            result.append({
                "symbol": stock_code,
                "stock_name": fav.get("stock_name", stock_code),
                "market": fav.get("market", "港股"),
                "added_date": fav.get("added_at").strftime("%Y-%m-%d") 
                    if isinstance(fav.get("added_at"), datetime) 
                    else str(fav.get("added_at", ""))[:10],
                "news_count": news_count,  # 🔥 使用真实数量
                "tags": fav.get("tags", []),
                "notes": fav.get("notes", "")
            })
        
        client.close()
        return result
        
    except Exception as e:
        st.error(f"❌ 获取自选股失败: {e}")
        return []



def add_stock_to_db(symbol, market):
    """添加股票到 MongoDB（改进版：获取真实股票名称）"""
    try:
        from pymongo import MongoClient
        
        # 强制使用 localhost，与验证脚本保持一致
        mongo_uri = "mongodb://admin:tradingagents123@mongodb:27017/?authSource=admin"
        
        print(f"[DEBUG] add_stock 连接: {mongo_uri}")  # 调试输出
        
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client["tradingagents"]
        
        user_id = "default_user"
        
        # 标准化股票代码用于比较
        clean_symbol = symbol.replace('.HK', '').replace('.SH', '').replace('.SZ', '')
        
        # 检查是否已存在（检查两种格式）
        user_doc = db.user_favorites.find_one({"user_id": user_id})
        
        if user_doc:
            for fav in user_doc.get("favorites", []):
                existing_code = fav.get("stock_code", "")
                existing_name = fav.get("stock_name", existing_code)
                existing_clean = existing_code.replace('.HK', '').replace('.SH', '').replace('.SZ', '')
                
                # 比较标准化后的代码
                if existing_clean == clean_symbol:
                    client.close()
                    print(f"[DEBUG] 股票已存在: {existing_code} - {existing_name}")
                    return False, f"⚠️ 该股票已在自选股中\n{existing_code} - {existing_name}"
        
        print(f"[DEBUG] 股票不存在，可以添加: {symbol}")
        
        # 从本地缓存获取股票名称（快速且准确）
        stock_name = symbol  # 默认使用代码
        try:
            clean_symbol = symbol.replace('.HK', '').replace('.SH', '').replace('.SZ', '')
            
            # 1. 从缓存查询 (优先)
            cache = db.stock_names_cache.find_one({'code': clean_symbol})
            if cache:
                stock_name = cache.get('name', symbol)
                print(f"[DEBUG] 从缓存获取: {symbol} -> {stock_name}")
            
            # 2. 尝试从 stock_basic_info 查询 (A股备份)
            elif db.stock_basic_info.find_one({'code': clean_symbol}):
                basic = db.stock_basic_info.find_one({'code': clean_symbol})
                stock_name = basic.get('name', symbol)
                print(f"[DEBUG] 从 stock_basic_info 获取: {symbol} -> {stock_name}")
            
            # 3. 尝试实时获取 (最终回退)
            else:
                print(f"[DEBUG] 本地数据未找到，尝试实时查询: {symbol}")
                try:
                    # 动态导入防止循环依赖
                    from tradingagents.dataflows.interface import get_china_stock_info_unified
                    
                    # 映射市场类型
                    market_map = {"A股": "CN", "港股": "HK", "美股": "US"}
                    # 注意：get_china_stock_info_unified 可能需要带后缀的代码
                    # 这里直接传原始 symbol (如 00700.HK, 600519)
                    
                    stock_info = get_china_stock_info_unified(symbol)
                    if isinstance(stock_info, dict) and 'name' in stock_info:
                         # 只有当名字不为空且不是代码本身时才采用
                         fetched_name = stock_info['name']
                         if fetched_name and fetched_name != symbol:
                             stock_name = fetched_name
                             print(f"[DEBUG] 实时查询成功: {symbol} -> {stock_name}")
                         
                         # 可选：写入缓存，方便下次使用
                         try:
                             db.stock_names_cache.update_one(
                                 {'code': clean_symbol},
                                 {'$set': {'name': stock_name, 'updated_at': datetime.utcnow()}},
                                 upsert=True
                             )
                         except:
                             pass
                except Exception as api_err:
                    print(f"[WARNING] 实时查询失败: {api_err}")
                    
        except Exception as e:
            print(f"[WARNING] 名称查询流程异常: {e}")
        
        # 添加到数据库
        favorite_stock = {
            "stock_code": symbol,
            "stock_name": stock_name,  # ✨ 使用真实名称
            "market": market,
            "added_at": datetime.utcnow(),
            "tags": [],
            "notes": "",
            "alert_price_high": None,
            "alert_price_low": None
        }
        
        result = db.user_favorites.update_one(
            {"user_id": user_id},
            {
                "$setOnInsert": {
                    "user_id": user_id,
                    "created_at": datetime.utcnow()
                },
                "$push": {"favorites": favorite_stock},
                "$set": {"updated_at": datetime.utcnow()}
            },
            upsert=True
        )
        
        client.close()
        
        return result.acknowledged, f"添加成功：{stock_name}"
    except Exception as e:
        return False, f"添加失败: {e}"


def remove_stock_from_db(symbol):
    """从 MongoDB 删除自选股"""
    try:
        from pymongo import MongoClient
        
        # 强制使用 localhost，与验证脚本保持一致
        mongo_uri = "mongodb://admin:tradingagents123@mongodb:27017/?authSource=admin"
        
        print(f"[DEBUG] remove_stock 连接: {mongo_uri}")  # 调试输出
        
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client["tradingagents"]
        
        user_id = "default_user"
        
        result = db.user_favorites.update_one(
            {"user_id": user_id},
            {
                "$pull": {"favorites": {"stock_code": symbol}},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        client.close()
        
        if result.modified_count > 0:
            return True, "删除成功"
        else:
            return False, "未找到该股票"
    except Exception as e:
        return False, f"删除失败: {e}"


def render_watchlist_management():
    """渲染自选股管理页面"""
    
    st.title("⭐ 自选股管理")
    
    # 顶部状态栏
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("---")
    with col2:
        db_connected, db_message = check_database_connection()
        if db_connected:
            st.success("🟢 已连接")
        else:
            st.error("🔴 未连接")
            st.caption(db_message)
    
    # 如果数据库未连接，显示错误信息并停止
    if not db_connected:
        st.error("⚠️ 无法连接到数据库服务器，请检查 MongoDB 服务是否正常运行。")
        st.info("💡 提示：请确保 MongoDB 服务已启动，或联系管理员。")
        return
    
    # 初始化自选股列表 - 每次都重新获取确保数据最新
    if 'watchlist' not in st.session_state or st.button("🔄 刷新", key="refresh_top"):
        st.session_state.watchlist = fetch_watchlist_from_db()
    
    # 在添加/删除后强制刷新
    if 'force_refresh' in st.session_state and st.session_state.force_refresh:
        st.session_state.watchlist = fetch_watchlist_from_db()
        st.session_state.force_refresh = False
    
    # 顶部操作区
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader(f"📊 当前自选股 ({len(st.session_state.watchlist)}只)")
    
    with col2:
        if st.button("🔄 刷新", use_container_width=True, key="refresh_main"):
            st.session_state.watchlist = fetch_watchlist_from_db()
            st.rerun()
    
    with col3:
        if st.button("📥 导入", use_container_width=True):
            st.info("导入功能开发中...")
    
    st.markdown("---")
    
    # 添加自选股
    with st.expander("➕ 添加自选股", expanded=True):
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            market = st.selectbox(
                "市场",
                ["A股", "港股", "美股"],
                key="add_market"
            )
        
        with col2:
            if market == "A股":
                placeholder = "如: 000001, 600519"
            elif market == "港股":
                placeholder = "如: 0700.HK, 9988.HK"
            else:
                placeholder = "如: AAPL, TSLA"
            
            symbol = st.text_input(
                "股票代码",
                placeholder=placeholder,
                key="add_symbol"
            )
        
        with col3:
            st.write("")  # 占位
            st.write("")  # 占位
            if st.button("➕ 添加", use_container_width=True):
                if symbol:
                    symbol_upper = symbol.strip().upper()
                    success, message = add_stock_to_db(symbol_upper, market)
                    
                    if success:
                        st.success(f"✅ {message}: {symbol_upper}")
                        # 设置刷新标志
                        st.session_state.force_refresh = True
                        st.rerun()
                    else:
                        st.warning(f"⚠️ {message}")
                else:
                    st.warning("⚠️ 请输入股票代码")
    
    # 显示自选股列表
    if st.session_state.watchlist:
        st.subheader("📋 自选股列表")
        
        # 按市场分组显示
        markets = {"A股": [], "港股": [], "美股": []}
        for stock in st.session_state.watchlist:
            markets[stock["market"]].append(stock)
        
        for market, stocks in markets.items():
            if stocks:
                with st.expander(f"{market} ({len(stocks)}只)", expanded=True):
                    for stock in stocks:
                        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                        
                        with col1:
                            st.write(f"**{stock['symbol']}**")
                            if stock.get('stock_name') and stock['stock_name'] != stock['symbol']:
                                st.caption(stock['stock_name'])
                        
                        with col2:
                            st.write(f"📅 添加: {stock['added_date']}")
                        
                        with col3:
                            st.write(f"📰 新闻: {stock.get('news_count', 0)}条")
                        
                        with col4:
                            if st.button("🗑️", key=f"del_{stock['symbol']}", help="删除"):
                                success, message = remove_stock_from_db(stock['symbol'])
                                
                                if success:
                                    st.success(f"✅ {message}: {stock['symbol']}")
                                    # 设置刷新标志
                                    st.session_state.force_refresh = True
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
    else:
        st.info("📝 暂无自选股，请添加")
    
    st.markdown("---")
    
    # 新闻收集设置
    st.subheader("⚙️ 新闻收集设置")
    
    # 初始化 session_state
    if 'schedule_times' not in st.session_state:
        st.session_state.schedule_times = ["02:00"]
    if 'config_loaded' not in st.session_state:
        st.session_state.config_loaded = False
    
    # 从数据库加载配置（只加载一次）
    if not st.session_state.config_loaded:
        try:
            mongo_uri = "mongodb://admin:tradingagents123@mongodb:27017/?authSource=admin"
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
            db = client["tradingagents"]
            
            config_doc = db.system_config.find_one({"user_id": "default_user"})
            if config_doc:
                st.session_state.auto_collect = config_doc.get("auto_collect", True)
                st.session_state.collection_days = config_doc.get("collection_days", 30)
                st.session_state.schedule_times = config_doc.get("schedule_times", ["02:00"])
            else:
                st.session_state.auto_collect = True
                st.session_state.collection_days = 30
                st.session_state.schedule_times = ["02:00"]
            
            st.session_state.config_loaded = True
            client.close()
        except Exception as e:
            print(f"加载配置失败: {e}")
            st.session_state.auto_collect = True
            st.session_state.collection_days = 30
            st.session_state.schedule_times = ["02:00"]
            st.session_state.config_loaded = True
    
    col1, col2 = st.columns(2)
    
    with col1:
        auto_collect = st.checkbox(
            "🔄 自动收集新闻",
            value=st.session_state.auto_collect,
            help="每天自动收集自选股的新闻数据"
        )
        
        collection_days = st.number_input(
            "📅 收集天数",
            min_value=7,
            max_value=90,
            value=st.session_state.collection_days,
            help="收集最近N天的历史新闻"
        )
    
    with col2:
        st.markdown("**⏰ 收集时间**（北京时间）")
        st.caption("支持设置多个时间点，格式：HH:MM（如 08:30）")
        
        # 显示现有时间
        times_to_remove = []
        for i, time_str in enumerate(st.session_state.schedule_times):
            col_time, col_del = st.columns([4, 1])
            with col_time:
                # 使用文本输入框，用户可以自由输入
                new_time = st.text_input(
                    f"时间 {i+1}",
                    value=time_str,
                    key=f"time_{i}",
                    placeholder="HH:MM",
                    label_visibility="collapsed"
                )
                # 验证并更新时间格式
                try:
                    # 验证格式是否正确
                    datetime.strptime(new_time.strip(), "%H:%M")
                    st.session_state.schedule_times[i] = new_time.strip()
                except:
                    if new_time.strip():
                        st.warning(f"⚠️ 时间格式错误，请使用 HH:MM 格式")
            
            with col_del:
                if len(st.session_state.schedule_times) > 1:  # 至少保留一个时间
                    if st.button("🗑️", key=f"del_{i}", help="删除此时间"):
                        times_to_remove.append(i)
        
        # 删除标记的时间
        for i in reversed(times_to_remove):
            st.session_state.schedule_times.pop(i)
            st.rerun()
        
        # 添加新时间按钮
        if st.button("➕ 添加时间", use_container_width=True):
            st.session_state.schedule_times.append("12:00")
            st.rerun()

    
    # 保存按钮
    if st.button("💾 保存设置", use_container_width=True, type="primary"):
        try:
            # 保存到 MongoDB
            mongo_uri = "mongodb://admin:tradingagents123@mongodb:27017/?authSource=admin"
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
            db = client["tradingagents"]
            
            # 准备配置文档
            config_doc = {
                "user_id": "default_user",
                "auto_collect": auto_collect,
                "collection_days": collection_days,
                "schedule_times": st.session_state.schedule_times,
                "updated_at": datetime.now()
            }
            
            # 保存到数据库
            result = db.system_config.update_one(
                {"user_id": "default_user"},
                {"$set": config_doc},
                upsert=True
            )
            
            client.close()
            
            # 更新 session_state
            st.session_state.auto_collect = auto_collect
            st.session_state.collection_days = collection_days
            
            st.success(f"✅ 设置已保存到数据库！时间点: {', '.join(st.session_state.schedule_times)}")
            
        except Exception as e:
            st.error(f"❌ 保存失败: {e}")
    
    # 统计信息
    st.markdown("---")
    st.subheader("📊 统计信息")
    
    # 从数据库查询真实统计
    try:
        mongo_uri = "mongodb://admin:tradingagents123@mongodb:27017/?authSource=admin"
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        db = client["tradingagents"]
        
        # 自选股代码列表
        watchlist_symbols = [s["symbol"] for s in st.session_state.watchlist]
        
        # 新闻总数（只统计自选股的）
        total_news = db.stock_news.count_documents({"symbol": {"$in": watchlist_symbols}}) if watchlist_symbols else 0
        
        # 分析报告总数（查询analysis_results集合）
        total_analysis = db.analysis_results.count_documents({"symbol": {"$in": watchlist_symbols}}) if watchlist_symbols else 0
        
        client.close()
    except Exception as e:
        total_news = sum(s.get("news_count", 0) for s in st.session_state.watchlist)
        total_analysis = 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("自选股总数", len(st.session_state.watchlist))
    
    with col2:
        st.metric("新闻总数", total_news)
    
    with col3:
        st.metric("分析报告", total_analysis)
    
    with col4:
        hk_count = len([s for s in st.session_state.watchlist if s["market"] == "港股"])
        st.metric("港股", hk_count)

    
    # 底部信息
    st.markdown("---")
    st.caption("💾 数据存储: MongoDB 数据库")
    st.caption("🔐 用户: default_user (演示模式)")


if __name__ == "__main__":
    render_watchlist_management()
