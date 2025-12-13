#!/usr/bin/env python3
"""
配置向导页面
提供可视化的配置界面,让用户轻松配置API密钥
"""

import streamlit as st
from utils.config_manager import config_manager
import time


def render_config_wizard():
    """渲染配置向导"""
    
    st.title("⚙️ 系统配置向导")
    st.markdown("---")
    
    # 初始化步骤
    if 'config_step' not in st.session_state:
        st.session_state.config_step = 1
    
    # 显示进度
    progress = st.session_state.config_step / 5
    st.progress(progress)
    
    # 步骤指示器
    steps = ["AI模型", "数据源", "数据库", "高级设置", "完成"]
    cols = st.columns(5)
    for i, (col, step) in enumerate(zip(cols, steps), 1):
        with col:
            if i < st.session_state.config_step:
                st.success(f"✅ {step}")
            elif i == st.session_state.config_step:
                st.info(f"▶️ {step}")
            else:
                st.write(f"⚪ {step}")
    
    st.markdown("---")
    
    # 渲染当前步骤
    if st.session_state.config_step == 1:
        render_ai_model_config()
    elif st.session_state.config_step == 2:
        render_data_source_config()
    elif st.session_state.config_step == 3:
        render_database_config()
    elif st.session_state.config_step == 4:
        render_advanced_config()
    elif st.session_state.config_step == 5:
        render_completion()


def render_ai_model_config():
    """渲染AI模型配置"""
    
    st.header("🤖 步骤1: AI模型配置")
    st.info("💡 至少配置一个AI模型API密钥,推荐DeepSeek(性价比最高)")
    
    # 获取当前配置
    config = config_manager.get_config()
    ai_models = config["ai_models"]
    
    # DeepSeek配置
    with st.expander("⭐ DeepSeek V3 (推荐)", expanded=True):
        st.markdown("""
        **优势**:
        - 💰 性价比最高
        - 🚀 响应速度快
        - 🇨🇳 国内访问稳定
        
        **获取方式**: [platform.deepseek.com](https://platform.deepseek.com/)
        """)
        
        deepseek_key = st.text_input(
            "API密钥",
            value="" if not ai_models["deepseek"]["configured"] else ai_models["deepseek"]["masked_key"],
            type="password",
            key="deepseek_key",
            placeholder="sk-xxxxxxxxxxxxxxxxxxxxx",
            help="从DeepSeek平台获取的API密钥"
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔍 验证", key="verify_deepseek", use_container_width=True):
                if deepseek_key and not deepseek_key.startswith("sk-****"):
                    with st.spinner("验证中..."):
                        result = config_manager.verify_api_key("deepseek", deepseek_key)
                        if result["verified"]:
                            st.success("✅ 验证成功!")
                            st.session_state.deepseek_verified = True
                        else:
                            st.error(f"❌ {result['message']}")
                            st.session_state.deepseek_verified = False
                else:
                    st.warning("⚠️ 请输入有效的API密钥")
        
        with col2:
            if st.button("💾 保存", key="save_deepseek", use_container_width=True):
                if deepseek_key and not deepseek_key.startswith("sk-****"):
                    result = config_manager.update_config("DEEPSEEK_API_KEY", deepseek_key)
                    if result["success"]:
                        st.success("✅ 已保存")
                        time.sleep(0.5)
                        st.rerun()
                else:
                    st.warning("⚠️ 请输入有效的API密钥")
        
        with col3:
            if ai_models["deepseek"]["configured"]:
                st.success("✅ 已配置")
    
    # 通义千问配置
    with st.expander("🇨🇳 通义千问 (备用)", expanded=False):
        st.markdown("""
        **优势**:
        - 🇨🇳 国产大模型
        - 🔒 数据安全
        - 📚 中文理解好
        
        **获取方式**: [dashscope.aliyun.com](https://dashscope.aliyun.com/)
        """)
        
        dashscope_key = st.text_input(
            "API密钥",
            value="" if not ai_models["dashscope"]["configured"] else ai_models["dashscope"]["masked_key"],
            type="password",
            key="dashscope_key",
            placeholder="sk-xxxxxxxxxxxxxxxxxxxxx"
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔍 验证", key="verify_dashscope", use_container_width=True):
                if dashscope_key and not dashscope_key.startswith("sk-****"):
                    with st.spinner("验证中..."):
                        result = config_manager.verify_api_key("dashscope", dashscope_key)
                        if result["verified"]:
                            st.success("✅ 验证成功!")
                        else:
                            st.error(f"❌ {result['message']}")
        
        with col2:
            if st.button("💾 保存", key="save_dashscope", use_container_width=True):
                if dashscope_key and not dashscope_key.startswith("sk-****"):
                    result = config_manager.update_config("DASHSCOPE_API_KEY", dashscope_key)
                    if result["success"]:
                        st.success("✅ 已保存")
                        time.sleep(0.5)
                        st.rerun()
        
        with col3:
            if ai_models["dashscope"]["configured"]:
                st.success("✅ 已配置")
    
    # OpenAI配置
    with st.expander("🌍 OpenAI GPT (可选)", expanded=False):
        st.markdown("""
        **优势**:
        - 🎯 功能强大
        - 🌐 生态完善
        
        **注意**: 需要国外网络
        
        **获取方式**: [platform.openai.com](https://platform.openai.com/)
        """)
        
        openai_key = st.text_input(
            "API密钥",
            value="" if not ai_models["openai"]["configured"] else ai_models["openai"]["masked_key"],
            type="password",
            key="openai_key",
            placeholder="sk-xxxxxxxxxxxxxxxxxxxxx"
        )
        
        col1, col2, col3 = st.columns(3)
        with col2:
            if st.button("💾 保存", key="save_openai", use_container_width=True):
                if openai_key and not openai_key.startswith("sk-****"):
                    result = config_manager.update_config("OPENAI_API_KEY", openai_key)
                    if result["success"]:
                        st.success("✅ 已保存")
                        time.sleep(0.5)
                        st.rerun()
        
        with col3:
            if ai_models["openai"]["configured"]:
                st.success("✅ 已配置")
    
    # 导航按钮
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        # 检查是否至少配置了一个模型
        has_model = any(model["configured"] for model in ai_models.values())
        
        if st.button("下一步 →", key="next_step_1", use_container_width=True, disabled=not has_model):
            st.session_state.config_step = 2
            st.rerun()
        
        if not has_model:
            st.warning("⚠️ 请至少配置一个AI模型")


def render_data_source_config():
    """渲染数据源配置"""
    
    st.header("📊 步骤2: 数据源配置 (可选)")
    st.info("💡 配置数据源API密钥可获取更多新闻和数据")
    
    config = config_manager.get_config()
    data_sources = config["data_sources"]
    
    # FinnHub
    with st.expander("📰 FinnHub (推荐)", expanded=True):
        st.markdown("""
        **用途**: 美股/港股新闻
        
        **免费额度**: 60次/分钟
        
        **获取方式**: [finnhub.io](https://finnhub.io/)
        """)
        
        finnhub_key = st.text_input(
            "API密钥",
            value="" if not data_sources["finnhub"]["configured"] else data_sources["finnhub"]["masked_key"],
            type="password",
            key="finnhub_key"
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔍 验证", key="verify_finnhub", use_container_width=True):
                if finnhub_key:
                    with st.spinner("验证中..."):
                        result = config_manager.verify_api_key("finnhub", finnhub_key)
                        if result["verified"]:
                            st.success("✅ 验证成功!")
                        else:
                            st.error(f"❌ {result['message']}")
        
        with col2:
            if st.button("💾 保存", key="save_finnhub", use_container_width=True):
                if finnhub_key:
                    result = config_manager.update_config("FINNHUB_API_KEY", finnhub_key)
                    if result["success"]:
                        st.success("✅ 已保存")
                        time.sleep(0.5)
                        st.rerun()
        
        with col3:
            if data_sources["finnhub"]["configured"]:
                st.success("✅ 已配置")
    
    # Alpha Vantage
    with st.expander("📈 Alpha Vantage (可选)", expanded=False):
        st.markdown("""
        **用途**: 美股数据
        
        **免费额度**: 5次/分钟
        
        **获取方式**: [alphavantage.co](https://www.alphavantage.co/)
        """)
        
        alpha_key = st.text_input(
            "API密钥",
            value="" if not data_sources["alpha_vantage"]["configured"] else data_sources["alpha_vantage"]["masked_key"],
            type="password",
            key="alpha_key"
        )
        
        col1, col2, col3 = st.columns(3)
        with col2:
            if st.button("💾 保存", key="save_alpha", use_container_width=True):
                if alpha_key:
                    result = config_manager.update_config("ALPHA_VANTAGE_API_KEY", alpha_key)
                    if result["success"]:
                        st.success("✅ 已保存")
                        time.sleep(0.5)
                        st.rerun()
        
        with col3:
            if data_sources["alpha_vantage"]["configured"]:
                st.success("✅ 已配置")
    
    # 导航按钮
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("← 上一步", key="prev_step_2", use_container_width=True):
            st.session_state.config_step = 1
            st.rerun()
    
    with col2:
        if st.button("跳过", key="skip_step_2", use_container_width=True):
            st.session_state.config_step = 3
            st.rerun()
    
    with col3:
        if st.button("下一步 →", key="next_step_2", use_container_width=True):
            st.session_state.config_step = 3
            st.rerun()


def render_database_config():
    """渲染数据库配置"""
    
    st.header("💾 步骤3: 数据存储配置")
    
    # 自动启用数据库
    st.success("✅ 数据库已自动配置并启用")
    
    st.info("""
    **已启用的服务**:
    - 📊 **MongoDB**: 用于存储分析报告、用户数据、历史新闻
    - ⚡ **Redis**: 用于缓存加速、会话管理
    - 📁 **本地文件**: 用于配置和日志存储
    
    💡 **说明**: 数据库已使用Docker默认配置自动启用,无需手动配置
    """)
    
    # 显示配置信息
    with st.expander("📋 查看数据库配置"):
        st.code("""
MongoDB配置:
  主机: mongodb
  端口: 27017
  数据库: tradingagents

Redis配置:
  主机: redis
  端口: 6379
        """, language="yaml")
    
    # 自动保存配置
    if 'db_config_saved' not in st.session_state:
        config_manager.update_config("USE_MONGODB_STORAGE", "true")
        config_manager.update_config("MONGODB_HOST", "mongodb")
        config_manager.update_config("MONGODB_PORT", "27017")
        config_manager.update_config("MONGODB_DATABASE", "tradingagents")
        config_manager.update_config("REDIS_ENABLED", "true")
        config_manager.update_config("REDIS_HOST", "redis")
        config_manager.update_config("REDIS_PORT", "6379")
        st.session_state.db_config_saved = True
    
    # 导航按钮
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("← 上一步", key="prev_step_3", use_container_width=True):
            st.session_state.config_step = 2
            st.rerun()
    
    with col2:
        if st.button("跳过", key="skip_step_3", use_container_width=True):
            st.session_state.config_step = 4
            st.rerun()
    
    with col3:
        if st.button("下一步 →", key="next_step_3", use_container_width=True):
            st.session_state.config_step = 4
            st.rerun()


def render_advanced_config():
    """渲染高级配置"""
    
    st.header("🔧 步骤4: 高级设置 (可选)")
    
    config = config_manager.get_config()
    system = config["system"]
    
    # 时区
    timezone = st.selectbox(
        "时区",
        ["Asia/Shanghai", "Asia/Hong_Kong", "America/New_York", "Europe/London"],
        index=0 if system["timezone"] == "Asia/Shanghai" else 0
    )
    
    # 日志级别
    log_level = st.selectbox(
        "日志级别",
        ["DEBUG", "INFO", "WARNING", "ERROR"],
        index=["DEBUG", "INFO", "WARNING", "ERROR"].index(system["log_level"])
    )
    
    # 内存功能
    memory_enabled = st.checkbox(
        "启用内存功能",
        value=system["memory_enabled"],
        help="Windows 10用户建议关闭"
    )
    
    if st.button("💾 保存高级配置", use_container_width=True):
        config_manager.update_config("TZ", timezone)
        config_manager.update_config("LOG_LEVEL", log_level)
        config_manager.update_config("MEMORY_ENABLED", "true" if memory_enabled else "false")
        st.success("✅ 高级配置已保存")
        time.sleep(0.5)
        st.rerun()
    
    # 导航按钮
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("← 上一步", key="prev_step_4", use_container_width=True):
            st.session_state.config_step = 3
            st.rerun()
    
    with col2:
        if st.button("跳过", key="skip_step_4", use_container_width=True):
            st.session_state.config_step = 5
            st.rerun()
    
    with col3:
        if st.button("完成配置 →", key="next_step_4", use_container_width=True):
            st.session_state.config_step = 5
            st.rerun()


def render_completion():
    """渲染完成页面"""
    
    st.header("🎉 配置完成!")
    
    config = config_manager.get_config()
    
    # 配置摘要
    st.subheader("📋 配置摘要")
    
    # AI模型
    st.write("**AI模型**:")
    for key, model in config["ai_models"].items():
        if model["configured"]:
            st.success(f"✅ {model['name']}")
    
    # 数据源
    st.write("**数据源**:")
    for key, source in config["data_sources"].items():
        if source["configured"]:
            st.success(f"✅ {source['name']}")
        else:
            st.info(f"⚪ {source['name']} (未配置)")
    
    # 数据库
    st.write("**数据库**:")
    if config["databases"]["mongodb"]["enabled"]:
        st.success("✅ MongoDB")
    else:
        st.info("⚪ MongoDB (未启用)")
    
    if config["databases"]["redis"]["enabled"]:
        st.success("✅ Redis")
    else:
        st.info("⚪ Redis (未启用)")
    
    st.markdown("---")
    
    st.success("✅ 配置已保存,可以开始使用了!")
    
    # 导航按钮
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("← 返回修改", use_container_width=True):
            st.session_state.config_step = 1
            st.rerun()
    
    with col2:
        if st.button("开始使用 →", use_container_width=True):
            # 跳转到主页
            st.switch_page("app.py")


if __name__ == "__main__":
    render_config_wizard()
