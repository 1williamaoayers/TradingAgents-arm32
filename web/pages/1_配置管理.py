#!/usr/bin/env python3
"""
配置管理页面
提供配置的查看、编辑和管理功能
"""

import streamlit as st
from utils.config_manager import config_manager
import time


def render_config_management():
    """渲染配置管理页面"""
    
    st.title("⚙️ 配置管理")
    
    # 顶部操作按钮
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🧙 配置向导", use_container_width=True):
            st.switch_page("pages/2_配置向导.py")
    
    with col2:
        if st.button("🔄 刷新", use_container_width=True):
            st.rerun()
    
    with col3:
        if st.button("📥 导出配置", use_container_width=True):
            st.info("功能开发中...")
    
    with col4:
        if st.button("📤 导入配置", use_container_width=True):
            st.info("功能开发中...")
    
    st.markdown("---")
    
    # 获取配置
    config = config_manager.get_config()
    
    # AI模型配置
    st.subheader("🤖 AI模型")
    for key, model in config["ai_models"].items():
        with st.expander(f"{model['name']}", expanded=model["configured"]):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                if model["configured"]:
                    st.success(f"✅ 已配置: {model['masked_key']}")
                else:
                    st.info("⚪ 未配置")
            
            with col2:
                if st.button("编辑", key=f"edit_{key}"):
                    st.session_state[f"editing_{key}"] = True
            
            with col3:
                if model["configured"] and st.button("测试", key=f"test_{key}"):
                    st.info("测试功能开发中...")
            
            # 编辑模式
            if st.session_state.get(f"editing_{key}", False):
                new_key = st.text_input(
                    "新API密钥",
                    type="password",
                    key=f"new_key_{key}"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("保存", key=f"save_new_{key}"):
                        if new_key:
                            env_key = f"{key.upper()}_API_KEY"
                            result = config_manager.update_config(env_key, new_key)
                            if result["success"]:
                                st.success("✅ 已保存")
                                st.session_state[f"editing_{key}"] = False
                                time.sleep(0.5)
                                st.rerun()
                
                with col2:
                    if st.button("取消", key=f"cancel_{key}"):
                        st.session_state[f"editing_{key}"] = False
                        st.rerun()
    
    st.markdown("---")
    
    # 数据源配置
    st.subheader("📊 数据源")
    for key, source in config["data_sources"].items():
        with st.expander(f"{source['name']}", expanded=source["configured"]):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                if source["configured"]:
                    st.success(f"✅ 已配置: {source['masked_key']}")
                else:
                    st.info("⚪ 未配置")
            
            with col2:
                if st.button("编辑", key=f"edit_source_{key}"):
                    st.session_state[f"editing_source_{key}"] = True
            
            with col3:
                if source["configured"] and st.button("测试", key=f"test_source_{key}"):
                    with st.spinner("测试中..."):
                        # 这里可以添加实际的测试逻辑
                        st.info("测试功能开发中...")
    
    st.markdown("---")
    
    # 数据库配置
    st.subheader("💾 数据库")
    
    # MongoDB
    with st.expander("MongoDB", expanded=config["databases"]["mongodb"]["enabled"]):
        mongodb = config["databases"]["mongodb"]
        
        if mongodb["enabled"]:
            st.success("✅ 已启用")
            st.write(f"**主机**: {mongodb['host']}")
            st.write(f"**端口**: {mongodb['port']}")
            st.write(f"**数据库**: {mongodb['database']}")
        else:
            st.info("⚪ 未启用")
        
        if st.button("配置MongoDB", key="config_mongodb"):
            st.session_state.config_step = 3
            st.switch_page("pages/2_配置向导.py")
    
    # Redis
    with st.expander("Redis", expanded=config["databases"]["redis"]["enabled"]):
        redis = config["databases"]["redis"]
        
        if redis["enabled"]:
            st.success("✅ 已启用")
            st.write(f"**主机**: {redis['host']}")
            st.write(f"**端口**: {redis['port']}")
        else:
            st.info("⚪ 未启用")
        
        if st.button("配置Redis", key="config_redis"):
            st.session_state.config_step = 3
            st.switch_page("pages/2_配置向导.py")
    
    st.markdown("---")
    
    # 系统配置
    st.subheader("🔧 系统配置")
    system = config["system"]
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**时区**: {system['timezone']}")
        st.write(f"**日志级别**: {system['log_level']}")
    
    with col2:
        st.write(f"**内存功能**: {'✅ 启用' if system['memory_enabled'] else '❌ 禁用'}")
        st.write(f"**缓存策略**: {system['cache_strategy']}")
    
    if st.button("修改系统配置"):
        st.session_state.config_step = 4
        st.switch_page("pages/2_配置向导.py")


if __name__ == "__main__":
    render_config_management()
