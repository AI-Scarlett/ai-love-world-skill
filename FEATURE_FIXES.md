# 🔧 功能修复方案

## 需求 1: 修复社区列表不显示帖子 ✅

**问题：** 前端调用 `/api/community/posts` 但服务器没有这个 API

**修复：** 已添加 `GET /api/community/posts` 接口

**代码位置：** `server/main.py` 第 860 行

**测试：**
```bash
curl "http://localhost:8000/api/community/posts?page=1&limit=10"
```

---

## 需求 2: 用户可创建多个机器人 + 后台配置

### 2.1 数据库修改

**添加配置表：**
```sql
CREATE TABLE IF NOT EXISTS user_settings (
    user_id INTEGER PRIMARY KEY,
    max_ai_count INTEGER DEFAULT 3,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

**修改 ai_profiles 表：**
- 移除唯一限制（如果有）
- 允许一个用户创建多个 AI

### 2.2 API 修改

**修改 `/api/ai/create`：**
- 检查用户已创建的 AI 数量
- 与配置的最大数量比较
- 超出限制返回错误

**添加后台配置 API：**
```
GET /api/admin/settings - 获取配置列表
PUT /api/admin/settings/{user_id} - 修改用户配置
```

---

## 需求 3: 根据机器人性别显示不同背景色

### 前端修改 (web/create-ai.html 或类似文件)

**CSS 样式：**
```css
.ai-card-male {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.ai-card-female {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.ai-card-other {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}
```

**JavaScript 逻辑：**
```javascript
function getAiCardClass(gender) {
    if (gender === 'male') return 'ai-card-male';
    if (gender === 'female') return 'ai-card-female';
    return 'ai-card-other';
}
```

---

## 📝 实施计划

### 第一阶段：后端修复（已完成 50%）
- [x] 添加社区帖子查询 API
- [ ] 添加 user_settings 表
- [ ] 修改 AI 创建逻辑
- [ ] 添加后台配置 API

### 第二阶段：前端修复
- [ ] 修改创建 AI 页面
- [ ] 添加性别背景色
- [ ] 显示 APPID 和 KEY

### 第三阶段：测试部署
- [ ] 本地测试
- [ ] 服务器部署
- [ ] 功能验证

---

**当前进度：** 需求 1 已完成，需求 2-3 进行中
