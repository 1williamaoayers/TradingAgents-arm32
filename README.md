# 🤖 TradingAgents - AI驱动的股票分析助手

> 🚀 **一键部署** | 🎨 **Web配置** | 🌍 **多市场支持** | 🐳 **Docker容器化**

[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![Multi-Arch](https://img.shields.io/badge/Arch-amd64%20%7C%20arm64-green)](https://github.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## ✨ 特性

- 🤖 **AI多智能体协作** - 市场分析师、新闻分析师、基本面分析师、风险评估团队
- 🌍 **多市场支持** - 美股、A股、港股全覆盖
- 🎨 **Web配置向导** - 无需编辑配置文件,浏览器内可视化配置
- 🐳 **Docker一键部署** - 支持x86_64和ARM64架构(VPS/NAS/树莓派)
- 📱 **响应式设计** - 支持PC、平板、手机、折叠屏
- 💾 **自动数据持久化** - MongoDB + Redis自动配置
- 🔄 **实时新闻聚合** - 整合多个新闻源,15分钟缓存

---

## 🚀 快速开始

### 方式1: Docker一键部署 (推荐)

**适用于**: VPS、NAS、本地服务器

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/TradingAgents-arm32.git
cd TradingAgents-arm32

# 2. 一键部署
bash scripts/deploy.sh

# 3. 访问应用
# 浏览器打开: http://localhost:8501
```

**就这么简单!** 🎉

---

### 方式2: 本地运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.docker .env
# 编辑.env文件,填入API密钥

# 3. 启动应用
streamlit run web/app.py
```

---

## ⚙️ 配置

### 🎨 Web配置向导 (推荐)

1. 启动应用后,访问 http://localhost:8501
2. 点击侧边栏 **"⚙️ 配置向导"**
3. 按步骤填写:
   - **步骤1**: AI模型API密钥 (必填)
   - **步骤2**: 数据源API密钥 (可选)
   - **步骤3**: 数据库配置 (自动)
   - **步骤4**: 高级设置 (可选)
4. 点击 **"保存"** - 配置立即生效!

### 📝 手动配置

编辑 `.env` 文件:

```bash
# AI模型 (至少配置一个)
DEEPSEEK_API_KEY=sk-your-deepseek-key    # 推荐,性价比高
DASHSCOPE_API_KEY=sk-your-dashscope-key  # 可选
OPENAI_API_KEY=sk-your-openai-key        # 可选

# 数据源 (推荐配置)
FINNHUB_API_KEY=your-finnhub-key          # 美股/港股新闻
ALPHA_VANTAGE_API_KEY=your-alpha-key      # 美股数据
```

**获取API密钥**:
- DeepSeek: https://platform.deepseek.com/
- 通义千问: https://dashscope.aliyun.com/
- FinnHub: https://finnhub.io/
- Alpha Vantage: https://www.alphavantage.co/

---

## 📖 使用说明

### 1. 选择市场

在主页选择要分析的市场:
- 🇺🇸 美股 (如: AAPL, TSLA)
- 🇨🇳 A股 (如: 000001, 600519)
- 🇭🇰 港股 (如: 0700.HK, 9988.HK)

### 2. 输入股票代码

根据市场输入对应格式的股票代码

### 3. 选择分析师

- 📈 市场分析师 - 技术面分析
- 💭 社交媒体分析师 - 情绪分析 (A股不支持)
- 📰 新闻分析师 - 新闻事件分析
- 💰 基本面分析师 - 财务数据分析

### 4. 设置研究深度

- **1级** - 快速分析 (1-2分钟)
- **3级** - 标准分析 (3-5分钟,推荐)
- **5级** - 全面分析 (10-15分钟)

### 5. 开始分析

点击 **"🚀 开始分析"** 按钮,等待AI团队完成分析

---

## 🏗️ 架构

```
┌─────────────────────────────────────────┐
│         Streamlit Web界面                │
│  (配置向导 + 分析表单 + 结果展示)         │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         AI多智能体系统                   │
│  ┌──────────┐  ┌──────────┐             │
│  │市场分析师│  │新闻分析师│             │
│  └──────────┘  └──────────┘             │
│  ┌──────────┐  ┌──────────┐             │
│  │基本面分析│  │风险评估  │             │
│  └──────────┘  └──────────┘             │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         数据层                           │
│  ┌──────────┐  ┌──────────┐             │
│  │新闻聚合  │  │市场数据  │             │
│  └──────────┘  └──────────┘             │
│  ┌──────────┐  ┌──────────┐             │
│  │MongoDB   │  │Redis缓存 │             │
│  └──────────┘  └──────────┘             │
└─────────────────────────────────────────┘
```

---

## 🐳 Docker部署详情

### 支持的架构

- ✅ **x86_64** (Intel/AMD)
- ✅ **ARM64** (Apple Silicon, ARM服务器, 树莓派4)

### 目录结构

```
TradingAgents-arm32/
├── .env              # 配置文件 (自动创建)
├── data/             # 分析结果
├── logs/             # 日志文件
├── cache/            # 缓存数据
└── backups/          # 配置备份
```

### 常用命令

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 更新应用
docker-compose pull && docker-compose up -d
```

---

## 📊 功能特性

### AI模型支持

- 🇨🇳 **DeepSeek V3** (推荐) - 性价比最高
- 🇨🇳 **通义千问** - 国产稳定
- 🌍 **OpenAI GPT** - 功能强大
- 🌍 **Google Gemini** - 多模态
- 🔧 **自定义OpenAI端点** - 支持兼容API

### 数据源

- 📰 **FinnHub** - 美股/港股新闻
- 📈 **Alpha Vantage** - 美股数据
- 🇨🇳 **AKShare** - A股数据
- 📱 **财联社** - 中文财经新闻
- 🌐 **Yahoo Finance** - 全球市场数据

### 分析维度

- 📈 **技术分析** - K线、均线、MACD、RSI等
- 📰 **新闻分析** - 实时新闻、舆情分析
- 💰 **基本面分析** - 财务数据、估值分析
- ⚠️ **风险评估** - 多角度风险评估
- 💭 **情绪分析** - 社交媒体情绪 (美股/港股)

---

## 🔧 高级功能

### 自选股管理

1. 添加关注的股票
2. 系统自动收集历史新闻
3. 定时分析和报告

### 配置管理

- 📋 查看当前配置
- ✏️ 在线编辑配置
- 💾 配置备份/恢复
- 📜 配置变更审计

### 分析历史

- 📊 查看历史分析
- 🔍 搜索和筛选
- 📥 导出报告
- 📈 趋势分析

---

## 🛠️ 开发

### 技术栈

- **前端**: Streamlit
- **后端**: Python 3.11
- **AI框架**: LangGraph
- **数据库**: MongoDB (可选)
- **缓存**: Redis (可选)
- **容器**: Docker + Docker Compose

### 项目结构

```
TradingAgents-arm32/
├── web/                    # Web前端
│   ├── app.py             # 主应用
│   ├── pages/             # 页面
│   ├── components/        # 组件
│   └── utils/             # 工具
├── tradingagents/         # 核心逻辑
│   ├── agents/            # AI智能体
│   ├── dataflows/         # 数据流
│   └── graph/             # 工作流图
├── scripts/               # 部署脚本
├── Dockerfile             # Docker镜像
└── docker-compose.yml     # 容器编排
```

---

## 📱 响应式设计

完美支持各种设备:

- 💻 **桌面端** (1920x1080+)
- 📱 **平板** (768-1024px)
- 📱 **手机** (320-767px)
- 📱 **折叠屏** - 自动适配展开/折叠状态

---

## 🤝 贡献

欢迎提交Issue和Pull Request!

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [Streamlit](https://streamlit.io/) - Web框架
- [LangGraph](https://github.com/langchain-ai/langgraph) - AI工作流
- [DeepSeek](https://www.deepseek.com/) - AI模型
- [FinnHub](https://finnhub.io/) - 金融数据
- [AKShare](https://github.com/akfamily/akshare) - A股数据

---

## 📞 联系方式

- 📧 Email: your-email@example.com
- 💬 Issues: [GitHub Issues](https://github.com/yourusername/TradingAgents-arm32/issues)

---

## ⭐ Star History

如果这个项目对你有帮助,请给个Star⭐支持一下!

---

<p align="center">
  Made with ❤️ by TradingAgents Team
</p>
