#!/bin/bash
# 端到端实测: 前端配置 → Docker容器 → 宿主机一致性
# 完整模拟用户在前端配置向导中保存配置的流程

set -e

echo "🔬 端到端实测: 前端→容器→宿主机一致性"
echo "=========================================="
echo ""

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 测试结果
PASSED=0
FAILED=0

test_step() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}📍 $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

test_pass() {
    echo -e "${GREEN}✅ $1${NC}"
    PASSED=$((PASSED + 1))
}

test_fail() {
    echo -e "${RED}❌ $1${NC}"
    FAILED=$((FAILED + 1))
}

# ============================================
# 阶段1: 环境准备
# ============================================
test_step "阶段1: 环境准备"

echo "检查Docker容器状态..."
if ! docker ps | grep -q tradingagents; then
    echo -e "${RED}❌ 容器未运行,请先启动: docker-compose up -d${NC}"
    exit 1
fi
test_pass "Docker容器正在运行"

echo "检查.env文件..."
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env文件不存在${NC}"
    exit 1
fi
test_pass ".env文件存在"

# 备份原始.env
echo "备份原始.env文件..."
cp .env .env.backup.test
test_pass "原始配置已备份到 .env.backup.test"

# ============================================
# 阶段2: 前端配置保存模拟
# ============================================
test_step "阶段2: 模拟前端配置向导保存"

# 生成唯一测试值
TIMESTAMP=$(date +%s%N)
TEST_DEEPSEEK_KEY="sk-test-deepseek-${TIMESTAMP}"
TEST_DASHSCOPE_KEY="sk-test-dashscope-${TIMESTAMP}"
TEST_FINNHUB_KEY="test-finnhub-${TIMESTAMP}"

echo "测试配置:"
echo "  DEEPSEEK_API_KEY: ${TEST_DEEPSEEK_KEY}"
echo "  DASHSCOPE_API_KEY: ${TEST_DASHSCOPE_KEY}"
echo "  FINNHUB_API_KEY: ${TEST_FINNHUB_KEY}"
echo ""

echo "执行前端config_manager.update_config()..."
docker exec tradingagents python3 << EOF
import sys
sys.path.insert(0, '/app')
from web.utils.config_manager import config_manager

print("📝 保存DeepSeek API密钥...")
result1 = config_manager.update_config("DEEPSEEK_API_KEY", "${TEST_DEEPSEEK_KEY}")
print(f"   结果: {result1}")

print("📝 保存DashScope API密钥...")
result2 = config_manager.update_config("DASHSCOPE_API_KEY", "${TEST_DASHSCOPE_KEY}")
print(f"   结果: {result2}")

print("📝 保存FinnHub API密钥...")
result3 = config_manager.update_config("FINNHUB_API_KEY", "${TEST_FINNHUB_KEY}")
print(f"   结果: {result3}")

if result1['success'] and result2['success'] and result3['success']:
    print("✅ 所有配置保存成功")
else:
    print("❌ 配置保存失败")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    test_pass "前端config_manager保存成功"
else
    test_fail "前端config_manager保存失败"
    exit 1
fi

# ============================================
# 阶段3: 验证容器内文件
# ============================================
test_step "阶段3: 验证容器内.env文件"

echo "读取容器内/app/.env文件..."
CONTAINER_DEEPSEEK=$(docker exec tradingagents grep "^DEEPSEEK_API_KEY=" /app/.env | cut -d'=' -f2)
CONTAINER_DASHSCOPE=$(docker exec tradingagents grep "^DASHSCOPE_API_KEY=" /app/.env | cut -d'=' -f2)
CONTAINER_FINNHUB=$(docker exec tradingagents grep "^FINNHUB_API_KEY=" /app/.env | cut -d'=' -f2)

echo "容器内配置:"
echo "  DEEPSEEK_API_KEY: ${CONTAINER_DEEPSEEK}"
echo "  DASHSCOPE_API_KEY: ${CONTAINER_DASHSCOPE}"
echo "  FINNHUB_API_KEY: ${CONTAINER_FINNHUB}"
echo ""

if [ "$CONTAINER_DEEPSEEK" = "$TEST_DEEPSEEK_KEY" ]; then
    test_pass "容器内DEEPSEEK_API_KEY正确"
else
    test_fail "容器内DEEPSEEK_API_KEY错误: expected=${TEST_DEEPSEEK_KEY}, got=${CONTAINER_DEEPSEEK}"
fi

if [ "$CONTAINER_DASHSCOPE" = "$TEST_DASHSCOPE_KEY" ]; then
    test_pass "容器内DASHSCOPE_API_KEY正确"
else
    test_fail "容器内DASHSCOPE_API_KEY错误"
fi

if [ "$CONTAINER_FINNHUB" = "$TEST_FINNHUB_KEY" ]; then
    test_pass "容器内FINNHUB_API_KEY正确"
else
    test_fail "容器内FINNHUB_API_KEY错误"
fi

# ============================================
# 阶段4: 验证宿主机文件同步
# ============================================
test_step "阶段4: 验证宿主机.env文件同步"

echo "读取宿主机.env文件..."
HOST_DEEPSEEK=$(grep "^DEEPSEEK_API_KEY=" .env | cut -d'=' -f2)
HOST_DASHSCOPE=$(grep "^DASHSCOPE_API_KEY=" .env | cut -d'=' -f2)
HOST_FINNHUB=$(grep "^FINNHUB_API_KEY=" .env | cut -d'=' -f2)

echo "宿主机配置:"
echo "  DEEPSEEK_API_KEY: ${HOST_DEEPSEEK}"
echo "  DASHSCOPE_API_KEY: ${HOST_DASHSCOPE}"
echo "  FINNHUB_API_KEY: ${HOST_FINNHUB}"
echo ""

if [ "$HOST_DEEPSEEK" = "$TEST_DEEPSEEK_KEY" ]; then
    test_pass "宿主机DEEPSEEK_API_KEY已同步"
else
    test_fail "宿主机DEEPSEEK_API_KEY未同步: expected=${TEST_DEEPSEEK_KEY}, got=${HOST_DEEPSEEK}"
fi

if [ "$HOST_DASHSCOPE" = "$TEST_DASHSCOPE_KEY" ]; then
    test_pass "宿主机DASHSCOPE_API_KEY已同步"
else
    test_fail "宿主机DASHSCOPE_API_KEY未同步"
fi

if [ "$HOST_FINNHUB" = "$TEST_FINNHUB_KEY" ]; then
    test_pass "宿主机FINNHUB_API_KEY已同步"
else
    test_fail "宿主机FINNHUB_API_KEY未同步"
fi

# ============================================
# 阶段5: 验证容器和宿主机完全一致
# ============================================
test_step "阶段5: 验证容器和宿主机文件完全一致"

if [ "$CONTAINER_DEEPSEEK" = "$HOST_DEEPSEEK" ] && \
   [ "$CONTAINER_DASHSCOPE" = "$HOST_DASHSCOPE" ] && \
   [ "$CONTAINER_FINNHUB" = "$HOST_FINNHUB" ]; then
    test_pass "容器和宿主机配置完全一致"
else
    test_fail "容器和宿主机配置不一致"
fi

# ============================================
# 阶段6: 验证应用能读取配置
# ============================================
test_step "阶段6: 验证应用能读取配置"

echo "测试应用读取配置..."
docker exec tradingagents python3 << EOF
import os
from dotenv import load_dotenv

# 重新加载.env
load_dotenv('/app/.env', override=True)

deepseek = os.getenv('DEEPSEEK_API_KEY')
dashscope = os.getenv('DASHSCOPE_API_KEY')
finnhub = os.getenv('FINNHUB_API_KEY')

print(f"应用读取到的配置:")
print(f"  DEEPSEEK_API_KEY: {deepseek}")
print(f"  DASHSCOPE_API_KEY: {dashscope}")
print(f"  FINNHUB_API_KEY: {finnhub}")

if deepseek == "${TEST_DEEPSEEK_KEY}" and \
   dashscope == "${TEST_DASHSCOPE_KEY}" and \
   finnhub == "${TEST_FINNHUB_KEY}":
    print("✅ 应用正确读取所有配置")
else:
    print("❌ 应用读取配置错误")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    test_pass "应用正确读取配置"
else
    test_fail "应用读取配置失败"
fi

# ============================================
# 阶段7: 容器重启测试
# ============================================
test_step "阶段7: 容器重启测试"

echo "重启Docker容器..."
docker-compose restart > /dev/null 2>&1

echo "等待容器启动..."
sleep 5

# 检查容器状态
if docker ps | grep -q tradingagents; then
    test_pass "容器重启成功"
else
    test_fail "容器重启失败"
    exit 1
fi

# ============================================
# 阶段8: 验证重启后配置保留
# ============================================
test_step "阶段8: 验证重启后配置保留"

echo "读取重启后容器内配置..."
RESTART_DEEPSEEK=$(docker exec tradingagents grep "^DEEPSEEK_API_KEY=" /app/.env | cut -d'=' -f2)
RESTART_DASHSCOPE=$(docker exec tradingagents grep "^DASHSCOPE_API_KEY=" /app/.env | cut -d'=' -f2)
RESTART_FINNHUB=$(docker exec tradingagents grep "^FINNHUB_API_KEY=" /app/.env | cut -d'=' -f2)

echo "重启后容器配置:"
echo "  DEEPSEEK_API_KEY: ${RESTART_DEEPSEEK}"
echo "  DASHSCOPE_API_KEY: ${RESTART_DASHSCOPE}"
echo "  FINNHUB_API_KEY: ${RESTART_FINNHUB}"
echo ""

if [ "$RESTART_DEEPSEEK" = "$TEST_DEEPSEEK_KEY" ]; then
    test_pass "重启后DEEPSEEK_API_KEY保留"
else
    test_fail "重启后DEEPSEEK_API_KEY丢失"
fi

if [ "$RESTART_DASHSCOPE" = "$TEST_DASHSCOPE_KEY" ]; then
    test_pass "重启后DASHSCOPE_API_KEY保留"
else
    test_fail "重启后DASHSCOPE_API_KEY丢失"
fi

if [ "$RESTART_FINNHUB" = "$TEST_FINNHUB_KEY" ]; then
    test_pass "重启后FINNHUB_API_KEY保留"
else
    test_fail "重启后FINNHUB_API_KEY丢失"
fi

# ============================================
# 阶段9: 验证重启后应用能读取
# ============================================
test_step "阶段9: 验证重启后应用能读取配置"

echo "测试重启后应用读取配置..."
docker exec tradingagents python3 << EOF
import os
from dotenv import load_dotenv

load_dotenv('/app/.env', override=True)

deepseek = os.getenv('DEEPSEEK_API_KEY')
dashscope = os.getenv('DASHSCOPE_API_KEY')
finnhub = os.getenv('FINNHUB_API_KEY')

print(f"重启后应用读取:")
print(f"  DEEPSEEK_API_KEY: {deepseek}")
print(f"  DASHSCOPE_API_KEY: {dashscope}")
print(f"  FINNHUB_API_KEY: {finnhub}")

if deepseek == "${TEST_DEEPSEEK_KEY}" and \
   dashscope == "${TEST_DASHSCOPE_KEY}" and \
   finnhub == "${TEST_FINNHUB_KEY}":
    print("✅ 重启后应用正确读取所有配置")
else:
    print("❌ 重启后应用读取配置错误")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    test_pass "重启后应用正确读取配置"
else
    test_fail "重启后应用读取配置失败"
fi

# ============================================
# 阶段10: 清理和恢复
# ============================================
test_step "阶段10: 清理测试环境"

echo "恢复原始.env文件..."
mv .env.backup.test .env
test_pass "原始配置已恢复"

echo "重启容器以加载原始配置..."
docker-compose restart > /dev/null 2>&1
sleep 3
test_pass "容器已重启"

# ============================================
# 测试总结
# ============================================
echo ""
echo "=========================================="
echo "📊 测试总结"
echo "=========================================="
echo ""
echo -e "通过: ${GREEN}${PASSED}${NC}"
echo -e "失败: ${RED}${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ 所有测试通过!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "验证结论:"
    echo "  ✅ 前端配置保存 → 容器内写入 → 宿主机同步: 100%可靠"
    echo "  ✅ 容器重启后配置保留: 100%可靠"
    echo "  ✅ 应用能正确读取配置: 100%可靠"
    echo ""
    exit 0
else
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ 有 ${FAILED} 个测试失败${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    exit 1
fi
