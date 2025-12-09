#!/usr/bin/env python3
"""
响应式设计测试页面
用于测试移动端、平板端和折叠屏的显示效果
"""

import streamlit as st

# 设置页面配置
st.set_page_config(
    page_title="响应式设计测试",
    page_icon="📱",
    layout="wide"
)

st.title("📱 响应式设计测试页面")

st.markdown("""
这个页面用于测试前端在不同设备上的显示效果。

**测试方法**:
1. 打开浏览器开发者工具 (F12)
2. 切换到设备模拟模式
3. 选择不同的设备进行测试
""")

st.divider()

# 显示当前屏幕信息
st.subheader("📊 屏幕信息检测")

screen_info_js = """
<script>
const info = {
    width: window.innerWidth,
    height: window.innerHeight,
    ratio: (window.innerWidth / window.innerHeight).toFixed(2),
    devicePixelRatio: window.devicePixelRatio,
    orientation: window.innerWidth > window.innerHeight ? '横屏' : '竖屏'
};

document.write(`
    <div style="background: #f0f2f6; padding: 1rem; border-radius: 8px; font-family: monospace;">
        <p><strong>屏幕宽度:</strong> ${info.width}px</p>
        <p><strong>屏幕高度:</strong> ${info.height}px</p>
        <p><strong>宽高比:</strong> ${info.ratio}</p>
        <p><strong>设备像素比:</strong> ${info.devicePixelRatio}</p>
        <p><strong>屏幕方向:</strong> ${info.orientation}</p>
    </div>
`);
</script>
"""

st.components.v1.html(screen_info_js, height=200)

st.divider()

# 测试组件
st.subheader("🧪 组件测试")

# 按钮测试
st.write("**按钮测试**")
col1, col2, col3 = st.columns(3)
with col1:
    st.button("按钮 1")
with col2:
    st.button("按钮 2")
with col3:
    st.button("按钮 3")

st.divider()

# 输入框测试
st.write("**输入框测试**")
st.text_input("文本输入框", placeholder="请输入内容")
st.selectbox("下拉选择框", ["选项1", "选项2", "选项3"])

st.divider()

# 卡片测试
st.write("**卡片测试**")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("指标 1", "100", "+10%")
with col2:
    st.metric("指标 2", "200", "-5%")
with col3:
    st.metric("指标 3", "300", "+15%")
with col4:
    st.metric("指标 4", "400", "+20%")

st.divider()

# 表格测试
st.write("**表格测试**")
import pandas as pd

df = pd.DataFrame({
    '股票代码': ['01810.HK', '0700.HK', '000001.SZ', 'AAPL'],
    '股票名称': ['小米集团', '腾讯控股', '平安银行', '苹果'],
    '当前价格': [12.50, 350.00, 15.80, 180.00],
    '涨跌幅': ['+2.5%', '-1.2%', '+3.8%', '+0.5%'],
    '成交量': ['1.2亿', '800万', '5000万', '6000万']
})

st.dataframe(df, use_container_width=True)

st.divider()

# 标签页测试
st.write("**标签页测试**")
tab1, tab2, tab3, tab4 = st.tabs(["标签1", "标签2", "标签3", "标签4"])

with tab1:
    st.write("这是标签页 1 的内容")
    
with tab2:
    st.write("这是标签页 2 的内容")
    
with tab3:
    st.write("这是标签页 3 的内容")
    
with tab4:
    st.write("这是标签页 4 的内容")

st.divider()

# 展开器测试
st.write("**展开器测试**")
with st.expander("点击展开查看详情"):
    st.write("这是展开器的内容")
    st.write("可以放置任何组件")

st.divider()

# 设备测试建议
st.subheader("📱 推荐测试设备")

st.markdown("""
### 手机端
- iPhone SE (375×667)
- iPhone 12/13 (390×844)
- iPhone 14 Pro Max (430×932)
- Samsung Galaxy S20 (360×800)
- Pixel 5 (393×851)

### 平板端
- iPad Mini (768×1024)
- iPad Air (820×1180)
- iPad Pro (1024×1366)

### 折叠屏
- Samsung Galaxy Z Fold 5
  - 外屏: 904×2316
  - 内屏: 1812×2176
- 华为 Mate X5
  - 外屏: 1008×2504
  - 内屏: 2224×2496
- 小米 MIX Fold 3
  - 外屏: 1080×2520
  - 内屏: 2160×1914

### 测试要点
1. ✅ 侧边栏是否正确显示
2. ✅ 按钮是否全宽显示
3. ✅ 输入框字体是否为16px (防止iOS缩放)
4. ✅ 表格是否可以横向滚动
5. ✅ 列布局是否垂直堆叠
6. ✅ 触摸目标是否足够大 (≥44px)
""")

st.divider()

st.success("✅ 响应式设计已应用! 请在不同设备上测试效果。")
