# Google News 测试脚本集合

这个文件夹包含了所有用于测试和使用Google News的脚本。

## 📁 文件结构

```
google_news_scripts/
├── README.md                      # 本说明文档
├── test/                          # 测试脚本(验证可用性)
│   ├── test_basic.sh             # 基础测试(8项检查)
│   ├── test_with_dns_fix.sh      # 带DNS自动修复功能
│   ├── test_complete.sh          # 完整测试(含详细报告)
│   └── test_python.py            # Python完整测试
└── tools/                         # 实用工具(日常使用)
    ├── get_news.sh               # 一键获取新闻(Shell版)
    └── simple_news.py            # 简易新闻工具(Python版)
```

---

## 🚀 快速开始

### 第一次使用(验证环境)

```bash
# 进入脚本目录
cd google_news_scripts

# 运行完整测试
bash test/test_complete.sh
```

### 日常使用(获取新闻)

```bash
# 方式1: Shell脚本(推荐小白)
bash tools/get_news.sh

# 方式2: Python脚本(更灵活)
python3 tools/simple_news.py
```

---

## 📋 脚本详细说明

### 🔍 测试脚本 (test/ 目录)

#### 1. `test_basic.sh` - 基础测试
**用途**: 快速验证Google News是否可用  
**测试项**: 网络连接、DNS解析、HTTPS连接、内容获取等8项  
**使用场景**: 首次部署时快速检查  
**命令**: `bash test/test_basic.sh`

#### 2. `test_with_dns_fix.sh` - DNS修复测试
**用途**: 自动诊断并修复DNS问题  
**特点**: 
- 自动检测DNS配置
- 测试多个公共DNS服务器
- 提供临时和永久修复方案
- 支持交互式自动修复

**使用场景**: DNS解析失败时使用  
**命令**: `bash test/test_with_dns_fix.sh`

#### 3. `test_complete.sh` - 完整测试
**用途**: 全面测试Google News各项功能  
**测试项**:
- 基础网络连接
- DNS解析
- HTTPS连接
- 网页内容获取
- RSS Feed测试
- 多地区访问测试
- 响应时间测试
- Python环境测试

**使用场景**: 
- 首次部署验证
- 定期健康检查
- 问题排查

**命令**: `bash test/test_complete.sh`

#### 4. `test_python.py` - Python完整测试
**用途**: 测试Python GNews库的各项功能  
**测试项**:
- GNews库安装检查
- 获取头条新闻
- 关键词搜索
- 多地区新闻获取
- 文章详情获取

**使用场景**: Python开发前的环境验证  
**命令**: `python3 test/test_python.py`

---

### 🛠️ 实用工具 (tools/ 目录)

#### 1. `get_news.sh` - 一键获取新闻 ⭐
**用途**: 最简单的新闻获取工具  
**特点**:
- 自动检查并安装依赖
- 一键获取最新10条头条
- 显示标题、来源、链接
- 小白友好

**使用场景**: 日常快速查看新闻  
**命令**: `bash tools/get_news.sh`

**输出示例**:
```
==============================================================
📰 Google News - 最新头条
==============================================================

1. Supreme Court poised to expand Trump's power...
   来源: The Washington Post
   链接: https://...

✓ 共获取 10 条新闻
```

#### 2. `simple_news.py` - Python简易工具 ⭐
**用途**: 功能更丰富的新闻获取工具  
**特点**:
- 获取头条新闻
- 搜索特定主题(科技、股票等)
- 显示详细信息(来源、时间、链接)
- 代码简洁,易于修改

**使用场景**: 
- 需要搜索特定主题
- 需要二次开发
- Python开发环境

**命令**: `python3 tools/simple_news.py`

---

## 💡 常见使用场景

### 场景1: 首次部署验证
```bash
# 1. 运行完整测试
bash test/test_complete.sh

# 2. 如果DNS失败,运行修复脚本
bash test/test_with_dns_fix.sh

# 3. 验证Python环境
python3 test/test_python.py
```

### 场景2: 日常获取新闻
```bash
# 快速获取头条
bash tools/get_news.sh

# 或使用Python版本
python3 tools/simple_news.py
```

### 场景3: 搜索特定主题
```bash
# 修改 simple_news.py 中的关键词
# 或直接使用命令行
python3 << 'EOF'
from gnews import GNews
news = GNews().get_news('stock market')
for n in news[:5]:
    print(n['title'])
EOF
```

### 场景4: 定时任务
```bash
# 添加到crontab,每小时获取一次
crontab -e

# 添加这一行
0 * * * * cd /root/google_news_scripts && bash tools/get_news.sh >> /var/log/news.log 2>&1
```

---

## 🔧 常用命令速查

### 获取不同地区新闻
```bash
# 美国
python3 -c "from gnews import GNews; [print(n['title']) for n in GNews(language='en', country='US').get_top_news()[:5]]"

# 英国
python3 -c "from gnews import GNews; [print(n['title']) for n in GNews(language='en', country='GB').get_top_news()[:5]]"

# 香港
python3 -c "from gnews import GNews; [print(n['title']) for n in GNews(language='zh-Hans', country='HK').get_top_news()[:5]]"
```

### 搜索特定主题
```bash
# 股票
python3 -c "from gnews import GNews; [print(n['title']) for n in GNews().get_news('stock')[:5]]"

# 科技
python3 -c "from gnews import GNews; [print(n['title']) for n in GNews().get_news('technology')[:5]]"

# 加密货币
python3 -c "from gnews import GNews; [print(n['title']) for n in GNews().get_news('cryptocurrency')[:5]]"
```

### 使用RSS Feed(无需Python)
```bash
# 美国新闻
curl -sL "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en" | grep -o "<title>.*</title>" | sed 's/<[^>]*>//g' | head -n 10

# 香港新闻
curl -sL "https://news.google.com/rss?hl=zh-HK&gl=HK&ceid=HK:zh-Hant" | grep -o "<title>.*</title>" | sed 's/<[^>]*>//g' | head -n 10
```

---

## 📝 依赖要求

### 系统要求
- Linux系统(Ubuntu/Debian/CentOS等)
- Bash Shell
- Python 3.6+

### Python依赖
```bash
pip3 install gnews
```

### 系统工具
- curl
- nslookup
- ping
- grep, sed (通常已预装)

---

## ❓ 常见问题

### Q1: DNS解析失败怎么办?
**A**: 运行 `bash test/test_with_dns_fix.sh`,脚本会自动诊断并提供修复方案。

### Q2: Python提示gnews未安装?
**A**: 运行 `pip3 install gnews` 安装。

### Q3: 如何修改获取的新闻数量?
**A**: 编辑 `tools/simple_news.py`,修改 `max_results` 参数。

### Q4: 如何获取中文新闻?
**A**: 修改语言参数:
```python
GNews(language='zh-Hans', country='CN')  # 简体中文
GNews(language='zh-Hant', country='HK')  # 繁体中文
```

### Q5: 脚本执行权限问题?
**A**: 添加执行权限:
```bash
chmod +x test/*.sh tools/*.sh
```

---

## 📞 技术支持

如有问题,请检查:
1. 网络连接是否正常
2. DNS配置是否正确
3. Python环境是否安装
4. 依赖库是否安装

---

## 📄 许可证

这些脚本仅供学习和测试使用。

---

**最后更新**: 2025-12-09
