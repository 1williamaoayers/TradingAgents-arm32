#!/bin/bash
# Docker配置同步和重载完整测试脚本
# 用于验证容器写入→宿主机同步和重启配置加载

set -e

echo "🔬 Docker配置同步和重载完整测试"
echo "=================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 测试计数
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 测试函数
test_pass() {
    echo -e "${GREEN}✅ $1${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
}

test_fail() {
    echo -e "${RED}❌ $1${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
}

run_test() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo ""
    echo -e "${YELLOW}🧪 测试 $TOTAL_TESTS: $1${NC}"
}

# 测试1: inode验证
run_test "验证容器和宿主机.env文件inode相同"
host_inode=$(ls -i .env 2>/dev/null | awk '{print $1}')
container_inode=$(docker exec tradingagents ls -i /app/.env 2>/dev/null | awk '{print $1}')

if [ -z "$host_inode" ] || [ -z "$container_inode" ]; then
    test_fail "无法获取inode (容器可能未启动)"
elif [ "$host_inode" = "$container_inode" ]; then
    test_pass "inode相同: $host_inode (证明是同一个文件)"
else
    test_fail "inode不同: host=$host_inode, container=$container_inode"
fi

# 测试2: 容器写入→宿主机同步
run_test "验证容器写入立即同步到宿主机"
TEST_KEY="SYNC_TEST_$(date +%s)"
TEST_VALUE="container_write_$(date +%N)"

docker exec tradingagents sh -c "echo '${TEST_KEY}=${TEST_VALUE}' >> /app/.env"

if grep -q "${TEST_KEY}=${TEST_VALUE}" .env; then
    test_pass "容器写入立即同步到宿主机"
else
    test_fail "容器写入未同步到宿主机"
fi

# 测试3: 宿主机写入→容器同步
run_test "验证宿主机写入立即同步到容器"
TEST_KEY2="SYNC_TEST_HOST_$(date +%s)"
TEST_VALUE2="host_write_$(date +%N)"

echo "${TEST_KEY2}=${TEST_VALUE2}" >> .env

if docker exec tradingagents cat /app/.env | grep -q "${TEST_KEY2}=${TEST_VALUE2}"; then
    test_pass "宿主机写入立即同步到容器"
else
    test_fail "宿主机写入未同步到容器"
fi

# 测试4: 文件修改时间同步
run_test "验证文件修改时间同步"
docker exec tradingagents sh -c 'echo "TIME_TEST=ok" >> /app/.env'
sleep 1

host_mtime=$(stat -c %Y .env 2>/dev/null || stat -f %m .env 2>/dev/null)
container_mtime=$(docker exec tradingagents stat -c %Y /app/.env 2>/dev/null || docker exec tradingagents stat -f %m /app/.env 2>/dev/null)

if [ "$host_mtime" = "$container_mtime" ]; then
    test_pass "文件修改时间完全一致"
else
    # 允许1秒误差
    diff=$((host_mtime - container_mtime))
    if [ $diff -lt 2 ] && [ $diff -gt -2 ]; then
        test_pass "文件修改时间基本一致 (误差${diff}秒)"
    else
        test_fail "文件修改时间不一致: host=$host_mtime, container=$container_mtime"
    fi
fi

# 测试5: 前端配置保存
run_test "验证前端config_manager保存配置"
TEST_API_KEY="sk-test-frontend-$(date +%s)"

docker exec tradingagents python3 << EOF
import sys
sys.path.insert(0, '/app')
from web.utils.config_manager import config_manager

result = config_manager.update_config("DEEPSEEK_API_KEY", "${TEST_API_KEY}")
print(f"保存结果: {result['success']}")
EOF

if grep -q "DEEPSEEK_API_KEY=${TEST_API_KEY}" .env; then
    test_pass "前端配置成功保存到宿主机"
else
    test_fail "前端配置未保存到宿主机"
fi

# 测试6: 重启前准备
run_test "准备重启测试 - 写入测试标记"
RESTART_TEST_KEY="RESTART_TEST_$(date +%s)"
RESTART_TEST_VALUE="before_restart_$(date +%N)"

docker exec tradingagents sh -c "echo '${RESTART_TEST_KEY}=${RESTART_TEST_VALUE}' >> /app/.env"

if grep -q "${RESTART_TEST_KEY}=${RESTART_TEST_VALUE}" .env; then
    test_pass "重启测试标记已写入宿主机"
else
    test_fail "重启测试标记写入失败"
fi

# 测试7: 容器重启
run_test "重启容器"
echo "正在重启容器..."
docker-compose restart > /dev/null 2>&1

echo "等待容器启动..."
sleep 5

# 检查容器是否运行
if docker ps | grep -q tradingagents; then
    test_pass "容器重启成功"
else
    test_fail "容器重启失败"
    exit 1
fi

# 测试8: 重启后配置文件存在
run_test "验证重启后配置文件仍然存在"
if docker exec tradingagents test -f /app/.env; then
    test_pass "重启后.env文件存在"
else
    test_fail "重启后.env文件不存在"
fi

# 测试9: 重启后配置内容保留
run_test "验证重启后配置内容完整保留"
if docker exec tradingagents cat /app/.env | grep -q "${RESTART_TEST_KEY}=${RESTART_TEST_VALUE}"; then
    test_pass "重启后配置内容完整保留"
else
    test_fail "重启后配置内容丢失"
fi

# 测试10: 重启后应用能读取配置
run_test "验证重启后应用能正确读取配置"
loaded_value=$(docker exec tradingagents python3 -c "import os; from dotenv import load_dotenv; load_dotenv('/app/.env'); print(os.getenv('${RESTART_TEST_KEY}', 'NOT_FOUND'))")

if [ "$loaded_value" = "$RESTART_TEST_VALUE" ]; then
    test_pass "重启后应用正确读取配置: $loaded_value"
else
    test_fail "重启后应用读取配置失败: expected=$RESTART_TEST_VALUE, got=$loaded_value"
fi

# 总结
echo ""
echo "=================================="
echo "📊 测试总结"
echo "=================================="
echo "总测试数: $TOTAL_TESTS"
echo -e "通过: ${GREEN}$PASSED_TESTS${NC}"
echo -e "失败: ${RED}$FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ 所有测试通过! Docker配置同步和重载机制100%可靠!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}❌ 有 $FAILED_TESTS 个测试失败${NC}"
    exit 1
fi
