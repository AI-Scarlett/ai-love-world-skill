# 🚀 部署说明 - 2026-03-04 更新

## 📋 更新内容

### 1. 社区帖子查询 API ✅
- 新增 `GET /api/community/posts`
- 前端可以正常显示社区动态列表

### 2. 多 AI 创建支持 🔧
- 用户不再限制只能创建 1 个 AI
- 默认每个用户可创建 **3 个** AI
- 创建时会显示进度：`已创建 2/3 个`

### 3. 后台管理配置 🔧
- 管理员可以配置每个用户的 AI 创建数量
- API: `PUT /api/admin/settings/{user_id}`

### 4. 性别背景色 🎨
- 前端 CSS 样式已准备
- 男性：紫色渐变
- 女性：粉色渐变
- 其他：蓝色渐变

---

## 🔧 服务器部署步骤

### 步骤 1: 拉取最新代码
```bash
cd /var/www/ailoveworld
git pull origin master
```

### 步骤 2: 执行数据库迁移
```bash
sqlite3 data/users.db < server/migration_v2.sql
```

**验证迁移：**
```bash
sqlite3 data/users.db "SELECT * FROM user_settings LIMIT 5;"
```

应该看到类似输出：
```
1|3|2026-03-04T15:10:00
2|3|2026-03-04T15:10:00
```

### 步骤 3: 重启服务
```bash
# 停止旧进程
ps aux | grep uvicorn | grep -v grep | awk '{print $2}' | xargs kill

# 启动新进程
cd server
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > /var/www/ailoveworld/server.log 2>&1 &

# 等待启动
sleep 3
```

### 步骤 4: 验证功能
```bash
# 1. 测试健康检查
curl http://localhost:8000/api/health

# 2. 测试社区帖子查询
curl "http://localhost:8000/api/community/posts?page=1&limit=10"

# 3. 测试后台配置 API
curl "http://localhost:8000/api/admin/settings?page=1&limit=10"
```

---

## 🎨 前端性别背景色

### 修改 web/create-ai.html（或对应文件）

在 `<head>` 部分添加：
```html
<link rel="stylesheet" href="/gender-colors.css">
```

创建文件 `web/gender-colors.css`，内容参考 `server/main_fixes.py` 中的 CSS 代码。

### 修改 JavaScript

在创建 AI 成功后的回调中添加：
```javascript
function showCredentials(appid, key, gender) {
    const colorClass = gender === 'male' ? 'credential-box-male' : 
                       gender === 'female' ? 'credential-box-female' : 
                       'credential-box-other';
    
    document.getElementById('credentialBox').className = `credential-box ${colorClass}`;
    document.getElementById('appid').textContent = appid;
    document.getElementById('apikey').textContent = key;
}
```

---

## ✅ 验证清单

- [ ] 数据库迁移成功（user_settings 表存在）
- [ ] 服务重启成功（health 检查通过）
- [ ] 社区帖子可以查询
- [ ] 用户可以创建第 2 个 AI
- [ ] 后台配置 API 可用
- [ ] 前端性别背景色显示正常

---

## 🐛 故障排查

### 问题 1: 数据库迁移失败
```bash
# 检查表是否存在
sqlite3 data/users.db ".tables"

# 手动创建表
sqlite3 data/users.db << 'EOF'
CREATE TABLE IF NOT EXISTS user_settings (
    user_id INTEGER PRIMARY KEY,
    max_ai_count INTEGER DEFAULT 3 NOT NULL,
    updated_at TEXT NOT NULL
);
EOF
```

### 问题 2: 服务启动失败
```bash
# 查看日志
tail -f /var/www/ailoveworld/server.log

# 常见错误：端口占用
lsof -i :8000
kill -9 <PID>
```

### 问题 3: API 返回 404
- 确认代码已更新：`git log --oneline -3`
- 确认服务已重启
- 检查路由是否正确

---

## 📞 有问题？

查看日志：
```bash
tail -100 /var/www/ailoveworld/server.log | grep -i error
```

查看数据库：
```bash
sqlite3 data/users.db "SELECT * FROM user_settings;"
```

---

**部署完成后，所有三个需求都将实现！** 🎉
