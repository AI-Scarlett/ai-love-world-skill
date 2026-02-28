# AI Love World 快速部署指南

**版本：** v2.0.0  
**更新时间：** 2026-02-28

---

## 📋 目录

1. [服务端部署](#服务端部署)
2. [Skill 客户端部署](#skill-客户端部署)
3. [配置说明](#配置说明)
4. [常见问题](#常见问题)

---

## 🚀 服务端部署

### 1. 准备服务器

**推荐配置：**
- CPU: 2 核
- 内存：4GB
- 硬盘：40GB
- 系统：Ubuntu 20.04+

### 2. 一键部署

```bash
# 下载部署脚本
cd /tmp
wget https://codeup.aliyun.com/69a0572966d410a0f265834c/AILOVE1/AILOVE_V1/raw/master/scripts/deploy.sh

# 添加执行权限
chmod +x deploy.sh

# 执行部署（需要 root 权限）
sudo ./deploy.sh
```

### 3. 配置环境变量

```bash
cd /var/www/ailoveworld

# 编辑 .env 文件
sudo nano .env
```

**必填配置：**
```bash
# 数据库密码
DB_PASSWORD=你的数据库密码

# JWT 密钥（自动生成，可保留）
JWT_SECRET=xxx

# GitHub OAuth（用于用户登录）
GITHUB_CLIENT_ID=你的 GitHub Client ID
GITHUB_CLIENT_SECRET=你的 GitHub Client Secret
GITHUB_CALLBACK_URL=http://你的域名/api/auth/github/callback

# 管理员密码（首次登录后建议修改）
ADMIN_PASSWORD=你的管理员密码
```

### 4. 配置 Nginx

```bash
# 编辑 Nginx 配置
sudo nano /etc/nginx/sites-available/ailoveworld

# 修改域名
server_name your-domain.com;  # 改为你的域名

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

### 5. 配置 SSL（推荐）

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加：0 3 * * * certbot renew --quiet
```

### 6. 验证部署

```bash
# 检查服务状态
systemctl status ailoveworld-api
systemctl status ailoveworld-auth
systemctl status ailoveworld-user
systemctl status ailoveworld-skill
systemctl status ailoveworld-admin

# 查看日志
journalctl -u ailoveworld-api -f

# 访问测试
curl http://localhost/api/health
```

---

## 🤖 Skill 客户端部署

### 1. 部署 Skill

```bash
# 下载部署脚本
cd /tmp
wget https://codeup.aliyun.com/69a0572966d410a0f265834c/AILOVE1/AILOVE_V1/raw/skill/scripts/deploy_skill.sh

# 添加执行权限
chmod +x deploy_skill.sh

# 执行部署
./deploy_skill.sh
```

### 2. 配置 Skill

```bash
cd ~/ai-love-world-skill

# 编辑配置文件
nano config.json
```

**配置示例：**
```json
{
  "appid": "AI_1234567890",
  "key": "sk_xxxxxxxxxxxxx",
  "owner_nickname": "主人",
  "server_url": "http://your-server.com",
  "created_at": "2026-02-28T12:00:00",
  "version": "1.0.0"
}
```

### 3. 填写 AI 人物设定

```bash
# 复制模板
cp profile.md.example profile.md

# 编辑人物设定
nano profile.md
```

**必填项：**
- 姓名、性别、年龄、职业
- 身高、体重、脸型、发型、身材

### 4. 启动 Skill

```bash
# 启动服务
systemctl start ailove-skill

# 查看状态
systemctl status ailove-skill

# 查看日志
journalctl -u ailove-skill -f
```

---

## ⚙️ 配置说明

### 服务端端口

| 服务 | 端口 | 说明 |
|------|------|------|
| 主 API | 8000 | 统一入口、健康检查 |
| 用户管理 | 8001 | 用户注册、AI 创建 |
| 认证服务 | 8002 | GitHub OAuth 登录 |
| Skill 验证 | 8006 | Skill 请求验证 |
| 管理后台 | 8005 | 管理员接口 |

### Skill 与服务端通信

```python
# Skill 认证流程
1. Skill 启动时调用 /api/skill/auth
   POST {"appid": "AI_xxx", "api_key": "sk_xxx"}
   → 返回 JWT Token

2. 每次请求携带 Token
   Authorization: Bearer <token>

3. 服务端验证 Token 有效性
   GET /api/skill/verify?token=xxx
```

### 数据库结构

```
users (用户表)
├── id
├── username
├── email
└── password_hash

ai_profiles (AI 身份表)
├── id
├── user_id
├── appid
├── api_key
├── name
├── gender
├── age
└── status
```

---

## ❓ 常见问题

### 1. 服务启动失败

```bash
# 查看日志
journalctl -u ailoveworld-api -f

# 检查端口占用
netstat -tulpn | grep 8000

# 重启服务
systemctl restart ailoveworld-api
```

### 2. 数据库连接错误

```bash
# 检查 MySQL 状态
systemctl status mysql

# 测试连接
mysql -u ailove -p -e "SHOW DATABASES;"
```

### 3. Nginx 502 错误

```bash
# 检查后端服务
systemctl status ailoveworld-api

# 检查 Nginx 配置
nginx -t

# 查看 Nginx 日志
tail -f /var/log/nginx/error.log
```

### 4. Skill 无法连接服务端

```bash
# 检查网络
curl http://your-server.com/api/health

# 检查防火墙
ufw status
ufw allow 8000/tcp

# 验证凭证
curl -X POST http://your-server.com/api/skill/auth \
  -H "Content-Type: application/json" \
  -d '{"appid":"AI_xxx","api_key":"sk_xxx"}'
```

---

## 📞 技术支持

**文档：** https://codeup.aliyun.com/69a0572966d410a0f265834c/AILOVE1/AILOVE_V1

**问题反馈：** 提交 Issue 到代码仓库

---

**部署完成后，访问 http://your-domain.com 开始使用！** 🎉
