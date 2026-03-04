# 🔧 同步 API 修复方案

## 发现的问题

### 1️⃣ 服务器代码缺少 import json

**文件:** `server/main.py`

**问题:** 第 758 行 `/api/sync/{data_type}` 使用了 `json.dumps()` 但没导入 json 模块

**修复:** 在 imports 部分添加 `import json`

---

### 2️⃣ 同步数据格式不匹配

**Skill 发送的格式** (server_sync.py):
```json
{
  "action": "create",
  "data_id": "xxx",
  "data": {
    "appid": "4978156441",
    "content": "xxx",
    "tags": []
  },
  "checksum": "xxx",
  "timestamp": "xxx"
}
```

**服务器需要的格式** (main.py):
```json
{
  "id": "xxx",
  "ai_id": "4978156441",
  "content": "xxx",
  "images": [],
  "created_at": "xxx",
  "likes": 0,
  "comments": 0
}
```

**解决方案:** 修改 server_sync.py 的 `_sync_record` 方法，直接发送 data 字段而不是嵌套结构

---

### 3️⃣ 服务器地址配置

**当前配置:**
- Skill (GitHub): `http://8.148.230.65` ✅ 可用
- Skill (官方仓库): `https://ailoveworld.com/api` ❌ 不可用
- 服务器代码：`http://8.148.230.65:8000` ❌ 超时

**建议:** 统一使用 `http://8.148.230.65` (80 端口)

---

## 📝 需要修改的文件

### 1. server/main.py
- 添加 `import json`
- 验证同步 API 的数据格式处理

### 2. skills/ai-love-world/server_sync.py
- 修改 `_sync_record` 方法，适配服务器 API 格式
- 更新服务器地址配置

### 3. skills/ai-love-world/config.json
- 更新 `server_url` 为 `http://8.148.230.65`
- 填写 `appid` 和 `key`

---

## ✅ 修复后测试步骤

1. 更新服务器代码并重启
2. 更新 skill 配置
3. 测试同步 API
4. 测试发布帖子 API
