# 自选股功能联调验证指南

## 前置条件检查

### ✅ 已完成的工作

1. **数据迁移** - 4 只港股已成功迁移到 MongoDB
   - 09618.HK ✅
   - 01810.HK ✅
   - 02128.HK ✅
   - 02525.HK ✅

2. **前端重构** - `3_自选股管理.py` 已重写
   - ❌ 删除了所有 JSON 文件读写代码
   - ✅ 新增了 MongoDB 数据库操作函数
   - ✅ 添加了数据库连接状态检测
   - ✅ 添加了友好的错误提示

3. **数据库验证** - MongoDB 数据正常
   - 用户 ID: `default_user`
   - 自选股数量: 4 只
   - 数据完整性: ✅

---

## 第三步：联调验证

### 步骤 1: 重启前端服务

#### 方法一：使用 Streamlit 命令（推荐）

```bash
cd /trae/TradingAgents-arm32
streamlit run web/主页.py --server.port 8501
```

#### 方法二：如果服务已在运行

1. 找到现有进程：
```bash
ps aux | grep streamlit
```

2. 停止旧进程：
```bash
kill -9 <进程ID>
```

3. 启动新服务：
```bash
cd /trae/TradingAgents-arm32
streamlit run web/主页.py --server.port 8501 &
```

---

### 步骤 2: 验证现有数据显示

1. **打开浏览器**
   - 访问: `http://localhost:8501`
   - 或者: `http://<你的服务器IP>:8501`

2. **进入自选股管理页面**
   - 点击左侧导航栏的"自选股管理"

3. **检查点 ✓**
   - [ ] 页面右上角显示 "🟢 已连接"
   - [ ] 显示 "当前自选股 (4只)"
   - [ ] 港股列表中显示 4 只股票：
     - [ ] 09618.HK
     - [ ] 01810.HK
     - [ ] 02128.HK
     - [ ] 02525.HK

**如果出现问题**:
- 显示 "🔴 未连接" → 检查 MongoDB 服务是否运行
- 显示 "0只" → 运行验证脚本确认数据库中有数据

---

### 步骤 3: 添加新股票测试

1. **在"添加自选股"区域**
   - 选择市场: `港股`
   - 输入股票代码: `00700.HK`（腾讯控股）
   - 点击 "➕ 添加" 按钮

2. **检查点 ✓**
   - [ ] 显示成功消息: "✅ 添加成功: 00700.HK"
   - [ ] 页面自动刷新
   - [ ] 当前自选股数量变为 "(5只)"
   - [ ] 港股列表中出现 00700.HK

---

### 步骤 4: 验证数据库存储

**运行验证脚本**:
```bash
python3 verify_mongodb_watchlist.py
```

**预期输出**:
```
✅ 找到 1 个用户的自选股数据
自选股数量: 5

用户 default_user 的自选股列表:
  1. 09618.HK
  2. 01810.HK
  3. 02128.HK
  4. 02525.HK
  5. 00700.HK  ← 新添加的股票
```

**检查点 ✓**:
- [ ] 数据库中有 5 只股票
- [ ] 00700.HK 已存在于 MongoDB 中

---

### 步骤 5: 验证不生成 JSON 文件

**检查 JSON 文件**:
```bash
ls -la data/watchlist.json
stat data/watchlist.json
```

**预期结果**:
```
-rw-r--r-- 1 root root 446 Dec 12 11:14 data/watchlist.json
```

**检查点 ✓**:
- [ ] 文件修改时间是旧的（Dec 12 11:14）
- [ ] 文件大小没有变化（446 字节）
- [ ] 文件内容仍然是原来的 4 只股票

**验证命令**:
```bash
cat data/watchlist.json | jq length
# 应该输出: 4 (不是 5)
```

---

### 步骤 6: 删除股票测试

1. **在自选股列表中**
   - 找到 `00700.HK`
   - 点击右侧的 "🗑️" 按钮

2. **检查点 ✓**
   - [ ] 显示成功消息: "✅ 删除成功: 00700.HK"
   - [ ] 页面自动刷新
   - [ ] 当前自选股数量变回 "(4只)"
   - [ ] 港股列表中不再显示 00700.HK

---

### 步骤 7: 最终数据库验证

**运行验证脚本**:
```bash
python3 verify_mongodb_watchlist.py
```

**预期输出**:
```
✅ 找到 1 个用户的自选股数据
自选股数量: 4

用户 default_user 的自选股列表:
  1. 09618.HK
  2. 01810.HK
  3. 02128.HK
  4. 02525.HK
```

**检查点 ✓**:
- [ ] 数据库中恢复为 4 只股票
- [ ] 00700.HK 已被删除

---

## 验证总结

### 成功标准

所有以下条件都满足才算验证通过：

1. ✅ 前端能正常显示现有的 4 只港股
2. ✅ 数据库连接状态显示正常
3. ✅ 能成功添加新股票（00700.HK）
4. ✅ 新股票数据存入 MongoDB（不是 JSON）
5. ✅ JSON 文件没有被修改
6. ✅ 能成功删除股票
7. ✅ 删除操作反映在 MongoDB 中

### 如果验证失败

#### 问题 1: 数据库连接失败

**症状**: 页面显示 "🔴 未连接"

**解决方案**:
```bash
# 检查 MongoDB 服务
ps aux | grep mongod

# 如果没有运行，启动服务
sudo systemctl start mongod
# 或
docker start mongodb
```

#### 问题 2: 数据不显示

**症状**: 显示 "暂无自选股"

**解决方案**:
```bash
# 重新运行迁移脚本
python3 migrate_json_to_mongo.py
```

#### 问题 3: 添加股票失败

**症状**: 点击添加后没有反应或报错

**解决方案**:
1. 检查浏览器控制台错误
2. 检查 Streamlit 终端输出
3. 确认 MongoDB 有写入权限

---

## 快速验证命令

**一键验证脚本**:
```bash
#!/bin/bash
echo "=== 自选股功能验证 ==="
echo ""
echo "1. 检查 MongoDB 服务..."
ps aux | grep mongod | grep -v grep && echo "✅ MongoDB 运行中" || echo "❌ MongoDB 未运行"
echo ""
echo "2. 验证数据库数据..."
python3 verify_mongodb_watchlist.py | grep "自选股数量"
echo ""
echo "3. 检查 JSON 文件..."
echo "文件修改时间: $(stat -c %y data/watchlist.json 2>/dev/null || echo '文件不存在')"
echo "文件大小: $(stat -c %s data/watchlist.json 2>/dev/null || echo '0') 字节"
echo ""
echo "=== 验证完成 ==="
```

保存为 `quick_verify.sh` 并运行：
```bash
chmod +x quick_verify.sh
./quick_verify.sh
```

---

## 下一步

验证通过后，可以考虑：

1. **实现真实用户认证**
   - 替换 `default_user` 为真实用户 ID
   - 集成登录系统

2. **优化用户体验**
   - 添加股票名称自动获取
   - 添加实时行情显示
   - 添加价格预警功能

3. **性能优化**
   - 添加 Redis 缓存
   - 批量操作优化

4. **功能扩展**
   - 导入/导出功能
   - 标签管理
   - 分组功能
