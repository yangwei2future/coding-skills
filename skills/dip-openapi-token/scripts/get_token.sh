#!/bin/bash
# get_token.sh - 获取 DIP OpenAPI 的 IDaaS Access Token
# 用法: ./get_token.sh [test|ontest|prod]
#
# 流程:
#   1. 自动打开浏览器登录页（macOS 用 open，Linux 用 xdg-open）
#   2. 用户登录后复制页面显示的 Refresh Token
#   3. 脚本自动调用 IDaaS API 换取 Access Token

ENV=${1:-ontest}

case "$ENV" in
  test)
    LOGIN_URL="https://account-ontest.lixiang.com/login?client_id=4wqmIzTQraqJn8QgC4NonY&redirect_uri=https%3A%2F%2Fdmp-api.ontest.k8s.chj.cloud%2F"
    TOKEN_BASE_URL="https://id-ontest.lixiang.com"
    CLIENT_ID="4wqmIzTQraqJn8QgC4NonY"
    ;;
  ontest|prod)
    LOGIN_URL="https://dmp-api.prod.k8s.chj.cloud/"
    TOKEN_BASE_URL="https://id.lixiang.com"
    CLIENT_ID="4wqmIzTQraqJn8QgC4NonY"
    ;;
  *)
    echo "用法: $0 [test|ontest|prod]"
    echo "  test   - 测试环境"
    echo "  ontest - ontest 环境（默认）"
    echo "  prod   - 生产环境"
    exit 1
    ;;
esac

TOKEN_URL="${TOKEN_BASE_URL}/api/token"

echo ""
echo "========================================="
echo "  DIP OpenAPI - IDaaS Token 获取工具"
echo "  环境: $ENV"
echo "========================================="
echo ""
echo "【步骤 1/3】正在打开浏览器登录页..."
echo "  登录地址: $LOGIN_URL"
echo ""

# 自动打开浏览器
if [[ "$OSTYPE" == "darwin"* ]]; then
  open "$LOGIN_URL"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
  xdg-open "$LOGIN_URL" 2>/dev/null || {
    echo "  ⚠️  无法自动打开浏览器，请手动访问上面的链接"
  }
else
  echo "  ⚠️  请手动在浏览器中打开上面的链接"
fi

echo "【步骤 2/3】完成浏览器登录后："
echo "  - 页面右下角会显示您的 Refresh Token"
echo "  - 点击「复制」按钮，然后粘贴到下方"
echo ""
printf "请粘贴 Refresh Token: "
read -r REFRESH_TOKEN

if [ -z "$REFRESH_TOKEN" ]; then
  echo "错误: Refresh Token 不能为空"
  exit 1
fi

echo ""
echo "【步骤 3/3】正在调用 IDaaS API 获取 Access Token..."

RESPONSE=$(curl -s -X POST "$TOKEN_URL" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "client_id=$CLIENT_ID" \
  --data-urlencode "grant_type=refresh_token" \
  --data-urlencode "refresh_token=$REFRESH_TOKEN" 2>&1)

# 解析响应
ACCESS_TOKEN=$(echo "$RESPONSE" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('access_token', ''))
except Exception:
    pass
" 2>/dev/null)

EXPIRES_IN=$(echo "$RESPONSE" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('expires_in', ''))
except Exception:
    pass
" 2>/dev/null)

ERROR_DESC=$(echo "$RESPONSE" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('error_description', d.get('error', '')))
except Exception:
    pass
" 2>/dev/null)

if [ -z "$ACCESS_TOKEN" ]; then
  echo ""
  echo "❌ 获取 Access Token 失败"
  if [ -n "$ERROR_DESC" ]; then
    echo "   错误信息: $ERROR_DESC"
  else
    echo "   原始响应: $RESPONSE"
  fi
  echo ""
  echo "常见原因:"
  echo "  - Refresh Token 已过期（重新执行脚本登录）"
  echo "  - Refresh Token 粘贴不完整（注意前后无空格）"
  echo "  - 需要连接公司 VPN"
  exit 1
fi

echo ""
echo "========================================="
echo "  ✅ Access Token 获取成功！"
echo "========================================="
echo ""
echo "Access Token (Bearer):"
echo "Bearer $ACCESS_TOKEN"
echo ""
if [ -n "$EXPIRES_IN" ]; then
  echo "有效期: ${EXPIRES_IN} 秒（约 $((EXPIRES_IN / 60)) 分钟）"
  echo ""
fi
echo "HTTP Header 用法:"
echo "  Authorization: Bearer $ACCESS_TOKEN"
echo ""
echo "注意事项:"
echo "  - 请在 expires_in 时间内复用此 Token，勿频繁刷新"
echo "  - 若接口返回 Token 过期，重新执行此脚本即可"
