#!/usr/bin/env python3
"""
自选股管理页面
用户可以添加、删除、查看自选股列表
系统会自动收集这些股票的历史新闻数据
"""

import streamlit as st
from datetime import datetime
import json
from pathlib import Path


def render_watchlist_management():
    """渲染自选股管理页面"""
    
    st.title("⭐ 自选股管理")
    st.markdown("---")
    
    # 初始化自选股列表
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = load_watchlist()
    
    # 顶部操作区
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader(f"📊 当前自选股 ({len(st.session_state.watchlist)}只)")
    
    with col2:
        if st.button("🔄 刷新", use_container_width=True):
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
                    add_to_watchlist(symbol.strip().upper(), market)
                    st.success(f"✅ 已添加 {symbol}")
                    time.sleep(0.5)
                    st.rerun()
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
                        
                        with col2:
                            st.write(f"📅 添加: {stock['added_date']}")
                        
                        with col3:
                            st.write(f"📰 新闻: {stock.get('news_count', 0)}条")
                        
                        with col4:
                            if st.button("🗑️", key=f"del_{stock['symbol']}", help="删除"):
                                remove_from_watchlist(stock['symbol'])
                                st.success(f"✅ 已删除 {stock['symbol']}")
                                time.sleep(0.5)
                                st.rerun()
    else:
        st.info("📝 暂无自选股,请添加")
    
    st.markdown("---")
    
    # 新闻收集设置
    st.subheader("⚙️ 新闻收集设置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        auto_collect = st.checkbox(
            "🔄 自动收集新闻",
            value=True,
            help="每天自动收集自选股的新闻数据"
        )
        
        collection_days = st.number_input(
            "📅 收集天数",
            min_value=7,
            max_value=90,
            value=30,
            help="收集最近N天的历史新闻"
        )
    
    with col2:
        collection_time = st.time_input(
            "⏰ 收集时间",
            value=datetime.strptime("02:00", "%H:%M").time(),
            help="每天自动收集的时间"
        )
        
        if st.button("💾 保存设置", use_container_width=True):
            save_collection_settings(auto_collect, collection_days, str(collection_time))
            st.success("✅ 设置已保存")
    
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


def load_watchlist():
    """加载自选股列表"""
    watchlist_file = Path("data/watchlist.json")
    if watchlist_file.exists():
        with open(watchlist_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_watchlist():
    """保存自选股列表"""
    watchlist_file = Path("data/watchlist.json")
    watchlist_file.parent.mkdir(parents=True, exist_ok=True)
    with open(watchlist_file, 'w', encoding='utf-8') as f:
        json.dump(st.session_state.watchlist, f, ensure_ascii=False, indent=2)


def add_to_watchlist(symbol, market):
    """添加到自选股"""
    # 检查是否已存在
    if any(s["symbol"] == symbol for s in st.session_state.watchlist):
        return False
    
    stock = {
        "symbol": symbol,
        "market": market,
        "added_date": datetime.now().strftime("%Y-%m-%d"),
        "news_count": 0
    }
    
    st.session_state.watchlist.append(stock)
    save_watchlist()
    return True


def remove_from_watchlist(symbol):
    """从自选股移除"""
    st.session_state.watchlist = [
        s for s in st.session_state.watchlist if s["symbol"] != symbol
    ]
    save_watchlist()


def save_collection_settings(auto_collect, days, time):
    """保存收集设置"""
    settings = {
        "auto_collect": auto_collect,
        "collection_days": days,
        "collection_time": time
    }
    
    settings_file = Path("data/collection_settings.json")
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_file, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import time
    render_watchlist_management()
