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
    """从 MongoDB 获取自选股列表"""
    try:
        from pymongo import MongoClient
        
        # 强制使用 localhost，与验证脚本保持一致
        mongo_uri = "mongodb://admin:tradingagents123@mongodb:27017/?authSource=admin"
        
        print(f"[DEBUG] fetch_watchlist 连接: {mongo_uri}")  # 调试输出
        
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client["tradingagents"]
        
        # 使用默认用户 ID（后续可以改为真实用户认证）
        user_id = "default_user"
        user_doc = db.user_favorites.find_one({"user_id": user_id})
        
        client.close()
        
        if user_doc:
            favorites = user_doc.get("favorites", [])
            # 转换为前端格式
            return [
                {
                    "symbol": fav.get("stock_code"),
                    "stock_name": fav.get("stock_name", fav.get("stock_code")),
                    "market": fav.get("market", "港股"),
                    "added_date": fav.get("added_at").strftime("%Y-%m-%d") 
                        if isinstance(fav.get("added_at"), datetime) 
                        else str(fav.get("added_at", ""))[:10],
                    "news_count": 0,
                    "tags": fav.get("tags", []),
                    "notes": fav.get("notes", "")
                }
                for fav in favorites
            ]
        return []
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
        
        # 检查是否已存在
        existing = db.user_favorites.find_one({
            "user_id": user_id,
            "favorites.stock_code": symbol
        })
        
        if existing:
            client.close()
            return False, "该股票已在自选股中"
        
        # ✨ 改进：获取真实股票名称
        stock_name = symbol  # 默认使用代码
        try:
            # 标准化代码
            clean_symbol = symbol.replace('.HK', '').replace('.SH', '').replace('.SZ', '')
            
            # 1. 先尝试从stock_basic_info获取（A股）
            basic_info = db.stock_basic_info.find_one({"symbol": clean_symbol})
            if basic_info:
                stock_name = basic_info.get('name', symbol)
                print(f"[DEBUG] 从数据库获取: {symbol} -> {stock_name}")
            else:
                # 2. 如果是港股，使用AKShare API实时获取
                if '.HK' in symbol or market == "港股":
                    try:
                        import akshare as ak
                        # 使用AKShare获取港股名称
                        hk_info = ak.stock_hk_spot_em()
                        # 查找匹配的股票
                        matched = hk_info[hk_info['代码'] == clean_symbol]
                        if not matched.empty:
                            stock_name = matched.iloc[0]['名称']
                            print(f"[DEBUG] 从AKShare获取: {symbol} -> {stock_name}")
                        else:
                            print(f"[WARNING] AKShare未找到 {symbol}")
                    except Exception as e:
                        print(f"[WARNING] AKShare查询失败: {e}")
        except Exception as e:
            print(f"[WARNING] 获取股票名称失败: {e}")
        
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
    
    # 初始化自选股列表
    if 'watchlist' not in st.session_state or st.button("🔄 刷新", key="refresh_top"):
        st.session_state.watchlist = fetch_watchlist_from_db()
    
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
                        time.sleep(0.5)
                        st.session_state.watchlist = fetch_watchlist_from_db()
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
                                    time.sleep(0.5)
                                    st.session_state.watchlist = fetch_watchlist_from_db()
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
        st.markdown("**⏰ 收集时间**")
        st.caption("支持设置多个时间点")
        
        # 显示现有时间
        times_to_remove = []
        for i, time_str in enumerate(st.session_state.schedule_times):
            col_time, col_del = st.columns([4, 1])
            with col_time:
                try:
                    default_time = datetime.strptime(time_str, "%H:%M").time()
                except:
                    default_time = datetime.strptime("02:00", "%H:%M").time()
                
                new_time = st.time_input(
                    f"时间 {i+1}",
                    value=default_time,
                    key=f"time_{i}",
                    label_visibility="collapsed"
                )
                # 更新时间
                st.session_state.schedule_times[i] = new_time.strftime("%H:%M")
            
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
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("自选股总数", len(st.session_state.watchlist))
    
    with col2:
        a_count = len([s for s in st.session_state.watchlist if s["market"] == "A股"])
        st.metric("A股", a_count)
    
    with col3:
        hk_count = len([s for s in st.session_state.watchlist if s["market"] == "港股"])
        st.metric("港股", hk_count)
    
    with col4:
        us_count = len([s for s in st.session_state.watchlist if s["market"] == "美股"])
        st.metric("美股", us_count)
    
    # 底部信息
    st.markdown("---")
    st.caption("💾 数据存储: MongoDB 数据库")
    st.caption("🔐 用户: default_user (演示模式)")


if __name__ == "__main__":
    render_watchlist_management()
