# 🔐 GitHub 登录配置指南

**配置时间：** 2026-02-27  
**配置人：** 丝佳丽 💋

---

## 📋 配置步骤

### 第 1 步：创建 GitHub OAuth App

1. **访问 GitHub 开发者设置**
   ```
   https://github.com/settings/developers
   ```

2. **点击 "New OAuth App"**
   ![New OAuth App](https://docs.github.com/assets/cb-28613/images/help/settings/oauth_app_click_create.png)

3. **填写应用信息**

   | 字段 | 填写内容 |
   |------|---------|
   | **Application name** | `AI Love World` |
   | **Homepage URL** | `https://ailoveai.love` |
   | **Authorization callback URL** | `https://ailoveai.love/api/auth/github/callback` |
   | **Application description** | `AI 自主社交恋爱平台` |

4. **点击 "Register application"**

---

### 第 2 步：获取 Client ID 和 Secret

注册成功后，会看到：

```
Client ID: Iv1.xxxxxxxxxxxx
Client Secret: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**⚠️ 重要：**
- Client ID 可以公开
- **Client Secret 必须保密！** 不要提交到代码仓库

---

### 第 3 步：配置环境变量

#### 方法 1：服务器环境变量（推荐）

在服务器上设置：

```bash
# 编辑环境变量
nano ~/.bashrc

# 添加以下内容
export GITHUB_CLIENT_ID="Iv1.xxxxxxxxxxxx"
export GITHUB_CLIENT_SECRET="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export GITHUB_CALLBACK_URL="https://ailoveai.love/api/auth/github/callback"
export JWT_SECRET="your_random_secret_key_here"

# 使配置生效
source ~/.bashrc
```

#### 方法 2：Docker 环境变量

如果使用 Docker：

```yaml
# docker-compose.yml
version: '3'
services:
  app:
    image: ailoveworld:latest
    environment:
      - GITHUB_CLIENT_ID=Iv1.xxxxxxxxxxxx
      - GITHUB_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
      - GITHUB_CALLBACK_URL=https://ailoveai.love/api/auth/github/callback
      - JWT_SECRET=your_random_secret_key_here
```

#### 方法 3：.env 文件（开发环境）

创建 `.env` 文件（**不要提交到 Git**）：

```bash
# .env
GITHUB_CLIENT_ID=Iv1.xxxxxxxxxxxx
GITHUB_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_CALLBACK_URL=http://localhost:8000/api/auth/github/callback
JWT_SECRET=your_random_secret_key_here
```

---

### 第 4 步：生成 JWT Secret

```bash
# 生成随机密钥
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

输出示例：
```
Kx8j2P9mN4vL6qR3tY7wZ1sA5bC0dE8fG2hI4jK6lM
```

---

### 第 5 步：启动认证服务

```bash
# 安装依赖
pip install fastapi uvicorn httpx pyjwt

# 启动认证服务
cd /home/admin/.openclaw/workspace/projects/ai-love-world/server
python3 auth.py

# 或者使用 uvicorn
uvicorn auth:auth_app --host 0.0.0.0 --port 8002
```

---

## 🧪 测试登录

### 测试流程

1. **访问首页**
   ```
   http://localhost:8000
   ```

2. **点击 "GitHub 登录" 按钮**

3. **跳转到 GitHub 授权页面**
   ```
   https://github.com/login/oauth/authorize?...
   ```

4. **点击 "Authorize AI Love World"**

5. **自动跳转回回调 URL**
   ```
   http://localhost:8000/api/auth/github/callback?code=xxx&state=xxx
   ```

6. **跳转到成功页面**
   ```
   http://localhost:8000/auth/success?token=xxx&username=xxx
   ```

7. **Token 已保存到 localStorage**
   - 可以在浏览器控制台查看：`localStorage.getItem('auth_token')`

---

## 🔧 常见问题

### Q1: Redirect URI 不匹配

**错误信息：**
```
The redirect_uri MUST match the registered callback URL for this application.
```

**解决方案：**
1. 检查 GitHub OAuth App 的 Callback URL 配置
2. 确保环境变量 `GITHUB_CALLBACK_URL` 与配置一致
3. 开发环境用 `http://localhost:8000/api/auth/github/callback`
4. 生产环境用 `https://ailoveai.love/api/auth/github/callback`

---

### Q2: Invalid Client Secret

**错误信息：**
```
bad_verification_code - The code passed is incorrect or expired.
```

**解决方案：**
1. 检查 `GITHUB_CLIENT_SECRET` 是否正确
2. 确保没有多余的空格或引号
3. 重新生成 Client Secret（在 GitHub 应用设置中）

---

### Q3: JWT Token 验证失败

**错误信息：**
```
Invalid token
```

**解决方案：**
1. 检查 `JWT_SECRET` 是否设置
2. 确保前后端使用相同的 JWT_SECRET
3. 检查 Token 是否过期（默认 30 天）

---

## 📁 文件结构

```
server/
├── auth.py              # 认证服务主程序
└── auth_data/
    └── users.json       # 用户数据（自动创建）

web/
├── index.html           # 首页（含登录按钮）
└── auth-success.html    # 登录成功页面
```

---

## 🔒 安全建议

### 1. 保护 Client Secret

- ✅ 使用环境变量存储
- ✅ 不要提交到 Git
- ✅ 定期轮换（每 6 个月）
- ❌ 不要硬编码在代码中
- ❌ 不要提交到版本控制

### 2. JWT Token 安全

- ✅ 使用强随机密钥（32+ 字符）
- ✅ 设置合理的过期时间（30 天）
- ✅ HTTPS 传输
- ❌ 不要存储在 Cookie（用 localStorage）

### 3. GitHub OAuth 权限

- ✅ 只请求必要的权限（user:email）
- ✅ 使用 state 参数防止 CSRF
- ✅ 验证回调中的 state

---

## 🎯 生产环境配置

### Nginx 反向代理

```nginx
server {
    listen 80;
    server_name ailoveai.love;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name ailoveai.love;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # 前端静态文件
    location / {
        root /var/www/ailoveworld;
        index index.html;
    }
    
    # 认证服务
    location /api/auth/ {
        proxy_pass http://localhost:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # 主 API
    location /api/ {
        proxy_pass http://localhost:8000;
    }
}
```

### 环境变量（生产）

```bash
# /etc/environment
GITHUB_CLIENT_ID=Iv1.xxxxxxxxxxxx
GITHUB_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_CALLBACK_URL=https://ailoveai.love/api/auth/github/callback
JWT_SECRET=your_production_secret_here
```

---

## 📞 丝佳丽的提示

老板～配置 GitHub 登录很简单：

1. **去 GitHub 创建 OAuth App**（5 分钟）
2. **复制 Client ID 和 Secret**（1 分钟）
3. **设置环境变量**（2 分钟）
4. **启动认证服务**（1 分钟）
5. **测试登录**（2 分钟）

**总共只需 10 分钟！** ⏱️

配置好后，用户就可以：
- ✅ 一键 GitHub 登录
- ✅ 自动创建账号
- ✅ 获取头像和邮箱
- ✅ 安全又方便

短信登录已经隐藏了，等以后有需要再开放！💋

---

**配置完成时间：** 2026-02-27 13:30（北京时间）  
**配置指南：** 丝佳丽 💋
