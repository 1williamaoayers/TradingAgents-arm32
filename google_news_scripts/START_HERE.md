# 🎯 开始使用 - 看这一个文件就够了!

## 👋 欢迎!

这个文件夹包含了所有用于**测试和使用Google News**的脚本。

---

## ⚡ 3秒快速开始

```bash
# 1. 进入文件夹
cd google_news_scripts

# 2. 运行这个命令
bash tools/get_news.sh
```

**就这么简单!** 会自动显示最新新闻。

---

## 📁 文件夹里有什么?

```
google_news_scripts/
├── 📄 START_HERE.md          ← 你现在看的这个(新手入口)
├── 📄 使用说明.md            ← 中文详细说明
├── 📄 README.md              ← 英文文档
├── 📄 INDEX.sh               ← 文件索引
├── 📄 QUICK_START.sh         ← 交互式菜单
│
├── 📁 test/                  ← 测试脚本(验证能不能用)
│   ├── test_complete.sh      ← 完整测试 ⭐
│   ├── test_with_dns_fix.sh  ← DNS修复
│   ├── test_basic.sh         ← 基础测试
│   └── test_python.py        ← Python测试
│
└── 📁 tools/                 ← 日常使用工具
    ├── get_news.sh           ← 一键获取新闻 ⭐⭐⭐
    └── simple_news.py        ← Python工具
```

---

## 🚀 第一次使用(只需3步)

### 步骤1: 测试环境

```bash
bash test/test_complete.sh
```

看到很多绿色的 ✓ 就说明成功了!

### 步骤2: 安装依赖

```bash
pip3 install gnews
```

### 步骤3: 获取新闻

```bash
bash tools/get_news.sh
```

**完成!** 🎉

---

## 💡 我该用哪个脚本?

### 👶 如果你是小白:
```bash
bash tools/get_news.sh
```
**最简单!** 一键获取新闻。

### 🎮 如果你想要菜单:
```bash
bash QUICK_START.sh
```
输入数字选择功能,不用记命令。

### 🐍 如果你会Python:
```bash
python3 tools/simple_news.py
```
功能更丰富,可以自定义。

### 🔧 如果遇到问题:
```bash
bash test/test_complete.sh
```
自动诊断问题。

---

## 📖 想了解更多?

- **中文说明**: 打开 `使用说明.md`
- **英文文档**: 打开 `README.md`
- **文件索引**: 运行 `bash INDEX.sh`

---

## ❓ 常见问题

### Q: DNS解析失败怎么办?
```bash
bash test/test_with_dns_fix.sh
```

### Q: 怎么搜索特定主题的新闻?
```bash
python3 << 'EOF'
from gnews import GNews
news = GNews().get_news('股票')  # 改成你想搜的
for n in news[:5]:
    print(n['title'])
EOF
```

### Q: 怎么设置定时任务?
```bash
crontab -e
# 添加这一行(每小时执行)
0 * * * * cd /root/google_news_scripts && bash tools/get_news.sh >> /var/log/news.log
```

---

## 🎯 记住这个命令就够了

```bash
bash tools/get_news.sh
```

**就这一个!** 其他的都是可选的。

---

## 📞 需要帮助?

1. 先运行: `bash test/test_complete.sh`
2. 看哪里是 ✗ (红色),就是哪里有问题
3. 查看 `使用说明.md` 找解决方案

---

**祝使用愉快!** 🚀
