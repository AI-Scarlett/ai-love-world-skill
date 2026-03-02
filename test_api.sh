#!/bin/bash
# AI Love World - 完整测试脚本
# 测试所有 API 是否正常工作

API_BASE="http://8.148.230.65/api"

echo "=========================================="
echo "AI Love World API 测试"
echo "=========================================="

# 1. 测试健康检查
echo ""
echo "1. 测试健康检查..."
curl -s "$API_BASE/health" | head -1

# 2. 测试国家列表
echo ""
echo "2. 测试国家列表..."
curl -s "$API_BASE/locations/countries" | head -1

# 3. 测试用户注册
echo ""
echo "3. 测试用户注册..."
REGISTER_RESULT=$(curl -s -X POST "$API_BASE/user/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"test_user_'$(date +%s)'","email":"test@test.com","password":"test123"}')
echo "$REGISTER_RESULT" | head -1

# 提取 token
TOKEN=$(echo "$REGISTER_RESULT" | grep -o '"token":"[^"]*"' | sed 's/"token":"//;s/"//')
echo "Token: $TOKEN"

# 4. 测试 AI 创建
echo ""
echo "4. 测试 AI 创建..."
if [ -n "$TOKEN" ]; then
  AI_RESULT=$(curl -s -X POST "$API_BASE/ai/create" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{
      "name": "测试AI",
      "gender": "female",
      "birth_date": "2000-01-01",
      "nationality": "CN",
      "city": "北京",
      "education": "大学",
      "height": 165,
      "personality": "温柔",
      "occupation": "助手",
      "hobbies": "阅读",
      "appearance": "美丽",
      "background": "测试",
      "love_preference": "测试"
    }')
  echo "$AI_RESULT" | head -3
else
  echo "跳过：没有获取到 token"
fi

# 5. 测试 AI 列表
echo ""
echo "5. 测试 AI 列表..."
if [ -n "$TOKEN" ]; then
  curl -s "$API_BASE/ai/list" \
    -H "Authorization: Bearer $TOKEN" | head -1
else
  echo "跳过：没有获取到 token"
fi

# 6. 测试管理后台 API
echo ""
echo "6. 测试管理后台登录..."
ADMIN_LOGIN=$(curl -s -X POST "$API_BASE/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"admin_id":"1000000000","password":"admin123456"}')
echo "$ADMIN_LOGIN" | head -1

ADMIN_TOKEN=$(echo "$ADMIN_LOGIN" | grep -o '"token":"[^"]*"' | sed 's/"token":"//;s/"//')
echo "Admin Token: $ADMIN_TOKEN"

# 7. 测试管理后台用户列表
echo ""
echo "7. 测试管理后台用户列表..."
if [ -n "$ADMIN_TOKEN" ]; then
  curl -s "$API_BASE/admin/users?page=1&limit=50" \
    -H "Authorization: Bearer $ADMIN_TOKEN" | head -1
else
  echo "跳过：没有获取到管理后台 token"
fi

# 8. 测试管理后台 AI 列表
echo ""
echo "8. 测试管理后台 AI 列表..."
if [ -n "$ADMIN_TOKEN" ]; then
  curl -s "$API_BASE/admin/ai-list?page=1&limit=50" \
    -H "Authorization: Bearer $ADMIN_TOKEN" | head -1
else
  echo "跳过：没有获取到管理后台 token"
fi

echo ""
echo "=========================================="
echo "测试完成！"
echo "=========================================="