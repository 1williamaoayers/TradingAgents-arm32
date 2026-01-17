#!/usr/bin/env python3
"""
新闻同步监控页面 - 纯Streamlit版本
直接连接MongoDB，不依赖FastAPI
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import plotly.express as px
from pymongo import MongoClient
import os

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))

def utc_to_beijing(utc_time):
    """将UTC时间转换为北京时间"""
    if utc_time is None:
        return None
    if utc_time.tzinfo is None:
        utc_time = utc_time.replace(tzinfo=timezone.utc)
    return utc_time.astimezone(BEIJING_TZ)


# 页面配置
st.set_page_config(
    page_title="新闻同步监控",
    page_icon="📰",
    layout="wide"
)

# MongoDB连接
@st.cache_resource
def get_mongo_client():
    """获取MongoDB客户端"""
    mongo_uri = "mongodb://admin:tradingagents123@mongodb:27017/?authSource=admin"
    return MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)

def get_db():
    """获取数据库"""
    client = get_mongo_client()
    return client.tradingagents

# 获取统计数据
def get_news_stats():
    """获取新闻统计总览"""
    db = get_db()
    
    # 总新闻数
    total_news = db.stock_news.count_documents({})
    
    # 今日新增
    yesterday = datetime.utcnow() - timedelta(days=1)
    today_news = db.stock_news.count_documents({"created_at": {"$gte": yesterday}})
    
    # 自选股数量
    watchlist_count = db.user_favorites.count_documents({})
    
    # 最近同步时间
    last_sync = db.news_sync_history.find_one({}, sort=[("sync_time", -1)])
    last_sync_time = "未知"
    if last_sync and last_sync.get("sync_time"):
        delta = datetime.utcnow() - last_sync["sync_time"]
        hours = int(delta.total_seconds() / 3600)
        if hours < 1:
            minutes = int(delta.total_seconds() / 60)
            last_sync_time = f"{minutes}分钟前"
        elif hours < 24:
            last_sync_time = f"{hours}小时前"
        else:
            days = int(hours / 24)
            last_sync_time = f"{days}天前"
    
    return {
        "total_news": total_news,
        "today_news": today_news,
        "watchlist_count": watchlist_count,
        "last_sync_time": last_sync_time
    }

def get_source_stats():
    """获取各源统计"""
    db = get_db()
    pipeline = [
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    sources = []
    total = 0
    for item in db.stock_news.aggregate(pipeline):
        count = item["count"]
        total += count
        sources.append({"source": item["_id"] or "未知", "count": count})
    
    for s in sources:
        s["percentage"] = round(s["count"] / total * 100, 1) if total > 0 else 0
    
    return sources

def get_watchlist_stats():
    """获取watchlist统计"""
    db = get_db()
    
    # 获取所有自选股（去重）
    seen_codes = set()
    stocks = []
    
    for doc in db.user_favorites.find({}):
        for fav in doc.get("favorites", []):
            code = fav.get("stock_code")
            name = fav.get("stock_name", code)
            
            # 去重
            if code and code not in seen_codes:
                seen_codes.add(code)
                
                # 查询新闻数量
                total_count = db.stock_news.count_documents({"symbol": code})
                week_ago = datetime.utcnow() - timedelta(days=7)
                recent_count = db.stock_news.count_documents({
                    "symbol": code,
                    "created_at": {"$gte": week_ago}
                })
                
                stocks.append({
                    "code": code,
                    "name": name,
                    "total_count": total_count,
                    "recent_count": recent_count,
                    "status": "✅" if total_count > 10 else "⚠️"
                })
    
    return sorted(stocks, key=lambda x: x["total_count"], reverse=True)

def get_sync_history():
    """获取同步历史"""
    db = get_db()
    history = []
    
    for record in db.news_sync_history.find({}).sort("sync_time", -1).limit(10):
        sync_time = record.get("sync_time")
        if sync_time:
            # 转换为北京时间
            beijing_time = utc_to_beijing(sync_time)
            time_str = beijing_time.strftime("%Y-%m-%d %H:%M") + " (北京时间)"
        else:
            time_str = "N/A"
            
        history.append({
            "sync_time": time_str,
            "sync_type": record.get("sync_type", "unknown"),
            "status": record.get("status", "unknown"),
            "news_count": record.get("news_count", 0),
            "duration": round(record.get("duration", 0), 1)
        })
    
    return history

# 标题
st.title("📰 新闻同步监控")
st.markdown("---")

# 手动同步函数
def trigger_manual_sync():
    """触发手动新闻同步（使用subprocess避免事件循环冲突）"""
    import subprocess
    import json
    
    # 调用独立的同步脚本
    result = subprocess.run(
        ["python3", "/app/app/scheduler/manual_sync.py"],
        capture_output=True,
        text=True,
        timeout=120  # 2分钟超时
    )
    
    if result.returncode != 0:
        error_msg = result.stderr or result.stdout or "未知错误"
        raise Exception(f"同步脚本执行失败: {error_msg}")
    
    # 解析JSON结果（只解析最后一行，忽略日志）
    try:
        # 获取最后一行非空输出
        lines = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        if not lines:
            raise Exception("同步脚本无输出")
        
        # 解析最后一行JSON
        data = json.loads(lines[-1])
        if not data.get("success"):
            raise Exception(data.get("error", "同步失败"))
        return data
    except json.JSONDecodeError:
        raise Exception(f"无法解析同步结果: {result.stdout}")



# 操作按钮区
col_refresh, col_sync, col_empty = st.columns([1, 1, 8])

with col_refresh:
    if st.button("🔄 刷新数据", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

with col_sync:
    if st.button("📥 立即同步", use_container_width=True, type="primary"):
        with st.spinner("正在同步新闻数据..."):
            try:
                result = trigger_manual_sync()
                st.success(f"✅ 同步完成！获取 {result.get('news_count', 0)} 条新闻")
                st.cache_resource.clear()
                st.rerun()
            except Exception as e:
                st.error(f"❌ 同步失败: {str(e)}")


# 获取数据
try:
    stats = get_news_stats()
    source_stats = get_source_stats()
    watchlist_stats = get_watchlist_stats()
    sync_history = get_sync_history()
    
    # 总览统计
    st.subheader("📊 总览统计")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总新闻数", f"{stats['total_news']:,}")
    
    with col2:
        st.metric("今日新增", f"{stats['today_news']:,}")
    
    with col3:
        st.metric("自选股数", stats['watchlist_count'])
    
    with col4:
        st.metric("最近同步", stats['last_sync_time'])
    
    st.markdown("---")
    
    # 两列布局
    col_left, col_right = st.columns([1, 1])
    
    # 左列：各源统计
    with col_left:
        st.subheader("📈 各源统计")
        
        if source_stats:
            df_sources = pd.DataFrame(source_stats)
            
            st.dataframe(
                df_sources,
                column_config={
                    "source": st.column_config.TextColumn("新闻源", width="medium"),
                    "count": st.column_config.NumberColumn("新闻数", format="%d"),
                    "percentage": st.column_config.NumberColumn("占比", format="%.1f%%")
                },
                hide_index=True,
                use_container_width=True
            )
            
            # 饼图
            fig = px.pie(df_sources, values='count', names='source', title='新闻源分布')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无数据")
    
    # 右列：自选股统计
    with col_right:
        st.subheader("📋 自选股新闻统计")
        
        if watchlist_stats:
            df_stocks = pd.DataFrame(watchlist_stats)
            
            st.dataframe(
                df_stocks,
                column_config={
                    "code": st.column_config.TextColumn("代码", width="small"),
                    "name": st.column_config.TextColumn("名称", width="medium"),
                    "total_count": st.column_config.NumberColumn("总数", format="%d"),
                    "recent_count": st.column_config.NumberColumn("近7天", format="%d"),
                    "status": st.column_config.TextColumn("状态", width="small")
                },
                hide_index=True,
                use_container_width=True
            )
            
            # 柱状图
            fig = px.bar(df_stocks, x='code', y='total_count', 
                        title='各股票新闻数量',
                        labels={'code': '股票代码', 'total_count': '新闻数量'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无自选股数据")
    
    st.markdown("---")
    
    # 同步历史
    st.subheader("📜 同步历史")
    
    if sync_history:
        df_history = pd.DataFrame(sync_history)
        
        st.dataframe(
            df_history,
            column_config={
                "sync_time": st.column_config.TextColumn("同步时间", width="medium"),
                "sync_type": st.column_config.TextColumn("类型", width="small"),
                "status": st.column_config.TextColumn("状态", width="small"),
                "news_count": st.column_config.NumberColumn("新闻数", format="%d"),
                "duration": st.column_config.NumberColumn("耗时(秒)", format="%.1f")
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("暂无同步历史记录")
    
    # 页脚
    st.markdown("---")
    st.caption("💡 提示：点击「刷新数据」按钮更新统计信息")
    
except Exception as e:
    st.error(f"⚠️ 数据加载失败: {str(e)}")
    st.info("请检查MongoDB连接是否正常")
