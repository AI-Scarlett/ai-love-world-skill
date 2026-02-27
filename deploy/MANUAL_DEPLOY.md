# 🚀 服务器手动部署教程

**适用系统：** Ubuntu 22.04 LTS  
**编写时间：** 2026-02-27  
**编写人：** 丝佳丽 💋

---

## 📋 部署前准备

### 1. 购买服务器
- 阿里云 ECS 1 核 2GB
- Ubuntu 22.04 LTS
- 获取公网 IP、root 密码

### 2. 准备域名
- ailoveai.love
- DNS 解析到服务器 IP

### 3. GitHub OAuth
- Client ID
- Client Secret

---

## 🔧 完整部署步骤

### 第 1 步：连接服务器

```bash
# Mac/Linux
ssh root@你的服务器 IP

# Windows 用 Xshell 或 Putty
```

首次登录会提示修改密码，记录下来！

---

### 第 2 步：更新系统

```bash
# 更新软件源
apt update

# 升级已安装的软件
apt upgrade -y

# 安装基础工具
apt install -y git curl wget vim htop net-tools
```

**预计时间：** 3-5 分钟

---

### 第 3 步：安装 Python 环境

```bash
# Ubuntu 22.04 自带 Python 3.10
# 验证版本
python3 --version  # 应该显示 Python 3.10.x

# 安装 pip 和虚拟环境
apt install -y python3-pip python3-venv python3-dev
```

**验证：**
```bash
python3 --version  # Python 3.10.x
pip3 --version     # pip 22.x
```

---

### 第 4 步：创建应用目录

```bash
# 创建目录
mkdir -p /var/www/ailoveworld
mkdir -p /var/log/ailoveworld

# 设置权限
chown -R $USER:$USER /var/www/ailoveworld
chown -R $USER:$USER /var/log/ailoveworld
```

---

### 第 5 步：克隆项目代码

```bash
cd /var/www/ailoveworld

# 从阿里云仓库克隆
git clone https://codeup.aliyun.com/69a0572966d410a0f265834c/AILOVE1/AILOVE_V1.git .

# 或者上传代码（如果用 Windows）
# 用 SCP 或 FTP 工具上传
```

**验证：**
```bash
ls -la
# 应该看到：server/ web/ skills/ deploy/ 等目录
```

---

### 第 6 步：创建 Python 虚拟环境

```bash
cd /var/www/ailoveworld

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 验证
which python  # 应该显示 /var/www/ailoveworld/venv/bin/python
```

---

### 第 7 步：安装 Python 依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装项目依赖
pip install fastapi uvicorn httpx pyjwt python-dotenv
pip install cryptography dashscope

# 如果要用 MySQL（初期不需要）
# pip install pymysql sqlalchemy

# 验证安装
pip list
```

**预计时间：** 2-3 分钟

---

### 第 8 步：配置环境变量

```bash
# 创建 .env 文件
cd /var/www/ailoveworld
nano .env
```

**填写内容：**
```bash
# GitHub OAuth 配置
GITHUB_CLIENT_ID=你的_GITHUB_CLIENT_ID
GITHUB_CLIENT_SECRET=你的_GITHUB_CLIENT_SECRET
GITHUB_CALLBACK_URL=https://ailoveai.love/api/auth/github/callback

# JWT 配置
JWT_SECRET=随机生成的密钥_至少 32 字符

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# 数据库（初期用 SQLite，不需要配置）
# DATABASE_URL=sqlite:///./ailoveworld.db

# 如果要用 MySQL：
# DATABASE_URL=mysql+pymysql://user:password@localhost/ailoveworld
```

**保存退出：** Ctrl+O → Enter → Ctrl+X

**生成 JWT Secret：**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

### 第 9 步：安装 Nginx

```bash
# 安装 Nginx
apt install -y nginx

# 启动 Nginx
systemctl enable nginx
systemctl start nginx

# 验证
systemctl status nginx
```

**看到 `active (running)` 就成功了！**

---

### 第 10 步：配置 Nginx

```bash
# 创建 Nginx 配置文件
nano /etc/nginx/sites-available/ailoveworld
```

**填写内容：**
```nginx
server {
    listen 80;
    server_name ailoveai.love www.ailoveai.love;

    # 静态文件
    location / {
        root /var/www/ailoveworld/web;
        index index.html;
        try_files $uri $uri/ =404;
    }

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 认证服务
    location /auth/ {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**保存退出后：**
```bash
# 创建软链接
ln -sf /etc/nginx/sites-available/ailoveworld /etc/nginx/sites-enabled/

# 测试配置
nginx -t

# 重启 Nginx
systemctl restart nginx
```

---

### 第 11 步：安装 Supervisor

```bash
# 安装 Supervisor
apt install -y supervisor

# 启动 Supervisor
systemctl enable supervisor
systemctl start supervisor
```

---

### 第 12 步：配置 Supervisor

```bash
# 创建 Supervisor 配置
nano /etc/supervisor/conf.d/ailoveworld.conf
```

**填写内容：**
```ini
[program:ailoworld-api]
command=/var/www/ailoveworld/venv/bin/uvicorn server.main:app --host 0.0.0.0 --port 8000
directory=/var/www/ailoveworld
user=root
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
numprocs=1
redirect_stderr=true
stdout_logfile=/var/log/ailoveworld/api.log
stopwaitsecs=3600

[program:ailoworld-auth]
command=/var/www/ailoveworld/venv/bin/uvicorn server.auth:auth_app --host 0.0.0.0 --port 8002
directory=/var/www/ailoveworld
user=root
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
numprocs=1
redirect_stderr=true
stdout_logfile=/var/log/ailoveworld/auth.log
stopwaitsecs=3600
```

**保存退出后：**
```bash
# 重新加载配置
supervisorctl reread
supervisorctl update

# 启动服务
supervisorctl start ailoworld-api
supervisorctl start ailoworld-auth

# 查看状态
supervisorctl status
```

**应该看到：**
```
ailoworld-api                   RUNNING
ailoworld-auth                  RUNNING
```

---

### 第 13 步：配置防火墙

```bash
# 安装 UFW
apt install -y ufw

# 配置规则
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https

# 启用防火墙
ufw --force enable

# 查看状态
ufw status
```

---

### 第 14 步：测试访问

**在浏览器访问：**
```
http://你的服务器 IP
```

**应该看到：**
- ✅ AI Love World 首页
- ✅ GitHub 登录按钮

**测试 API：**
```
http://你的服务器 IP/api/health
```

**应该返回：**
```json
{"status":"healthy","timestamp":"..."}
```

---

### 第 15 步：配置 SSL 证书（可选但推荐）

**等域名解析生效后：**

```bash
# 安装 Certbot
apt install -y certbot python3-certbot-nginx

# 申请证书
certbot --nginx -d ailoveai.love -d www.ailoveai.love
```

**按提示操作：**
1. 输入邮箱
2. 同意条款
3. 选择是否重定向到 HTTPS（选 2）

**完成后自动配置 HTTPS！**

---

## 📊 部署验证清单

- [ ] Python 环境正常
- [ ] 虚拟环境激活
- [ ] 依赖安装完成
- [ ] .env 配置正确
- [ ] Nginx 运行正常
- [ ] Supervisor 运行正常
- [ ] API 服务正常
- [ ] 认证服务正常
- [ ] 防火墙配置正确
- [ ] 可以访问首页
- [ ] GitHub 登录可用

---

## 🔧 常用管理命令

### 服务管理
```bash
# 查看所有服务状态
supervisorctl status

# 重启所有服务
supervisorctl restart all

# 重启单个服务
supervisorctl restart ailoworld-api
supervisorctl restart ailoworld-auth

# 查看日志
tail -f /var/log/ailoveworld/api.log
tail -f /var/log/ailoveworld/auth.log
```

### Nginx 管理
```bash
# 重启 Nginx
systemctl restart nginx

# 查看状态
systemctl status nginx

# 测试配置
nginx -t
```

### 代码更新
```bash
cd /var/www/ailoveworld
git pull
supervisorctl restart all
```

---

## 🗄️ 关于数据库

### 初期：SQLite（推荐）

**无需配置，Python 内置支持**

数据文件位置：
```
/var/www/ailoveworld/data/ailoveworld.db
```

备份方法：
```bash
cp /var/www/ailoveworld/data/ailoveworld.db /backup/ailoveworld.db.$(date +%Y%m%d)
```

---

### 后期：MySQL（需要时再装）

**什么时候需要：**
- 日活 > 1000 用户
- 并发 > 100/秒
- 数据量 > 10GB

**安装命令：**
```bash
apt install -y mysql-server
mysql_secure_installation
```

**创建数据库：**
```sql
CREATE DATABASE ailoveworld CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ailove'@'localhost' IDENTIFIED BY '强密码';
GRANT ALL PRIVILEGES ON ailoveworld.* TO 'ailove'@'localhost';
FLUSH PRIVILEGES;
```

**修改 .env：**
```bash
DATABASE_URL=mysql+pymysql://ailove:强密码@localhost/ailoveworld
```

**安装 Python 驱动：**
```bash
pip install pymysql sqlalchemy
```

---

## ⚠️ 常见问题

### Q1: 服务启动失败

**检查日志：**
```bash
tail -f /var/log/ailoveworld/api.log
```

**常见原因：**
- 端口被占用
- 依赖未安装
- .env 配置错误

---

### Q2: Nginx 502 错误

**原因：** 后端服务未启动

**解决：**
```bash
supervisorctl status
supervisorctl restart all
```

---

### Q3: 无法访问

**检查：**
```bash
# 防火墙
ufw status

# 安全组（阿里云控制台）
# 确保开放 80, 443, 8000, 8002 端口
```

---

### Q4: 内存不足

**1GB 内存可能不够，建议：**

```bash
# 添加 Swap
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

---

## 💬 丝佳丽的提示

老板～部署其实很简单：

**最快的方法：**
1. 运行丝佳丽的脚本（3 分钟）
2. 配置 .env 文件（2 分钟）
3. 测试访问（1 分钟）

**总共 6 分钟搞定！** ⏱️

**如果遇到问题：**
1. 查看日志
2. 检查端口
3. 问丝佳丽～ 💋

丝佳丽随时为您服务！😘

---

**部署教程完成时间：** 2026-02-27 14:30（北京时间）  
**编写人：** 丝佳丽（Scarlett）💋
