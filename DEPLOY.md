# AI Love World - 部署指南

## 🚀 一键部署（推荐）

### 快速部署
```bash
cd /var/www/ailoveworld
sudo ./deploy.sh
```

### 部署命令

| 命令 | 说明 |
|------|------|
| `sudo ./deploy.sh` | 完整部署（默认） |
| `sudo ./deploy.sh start` | 仅启动服务 |
| `sudo ./deploy.sh stop` | 停止服务 |
| `sudo ./deploy.sh restart` | 重启服务 |
| `sudo ./deploy.sh status` | 查看服务状态 |
| `sudo ./deploy.sh migrate` | 仅执行数据库迁移 |
| `sudo ./deploy.sh logs` | 查看实时日志 |
| `sudo ./deploy.sh help` | 显示帮助信息 |

---

## 📋 手动部署

### 1. 拉取最新代码
```bash
cd /var/www/ailoveworld
git pull origin master
```

### 2. 执行数据库迁移
```bash
cd /var/www/ailoveworld/server
sqlite3 ../data/users.db < migration_v8.sql
sqlite3 ../data/users.db < migration_v9.sql
```

### 3. 安装依赖
```bash
cd /var/www/ailoveworld/server
pip3 install -r requirements.txt
```

### 4. 启动服务
```bash
cd /var/www/ailoveworld/server
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../logs/server.log 2>&1 &
```

### 5. 验证部署
```bash
curl http://localhost:8000/api/health
```

---

## 🔧 服务管理

### 查看服务状态
```bash
# 查看进程
ps aux | grep uvicorn

# 查看端口
netstat -tuln | grep 8000

# 查看 PID
cat /var/www/ailoveworld/server.pid
```

### 停止服务
```bash
# 方法 1: 使用部署脚本
sudo ./deploy.sh stop

# 方法 2: 手动停止
pkill -f "uvicorn.*main:app"
```

### 查看日志
```bash
# 实时日志
tail -f /var/www/ailoveworld/logs/server.log

# 最近 100 行
tail -n 100 /var/www/ailoveworld/logs/server.log

# 搜索错误
grep -i error /var/www/ailoveworld/logs/server.log
```

---

## 📊 数据库迁移历史

| 版本 | 迁移文件 | 说明 |
|------|---------|------|
| v6 | migration_v6.sql | user_settings 表 |
| v7 | migration_v7.sql | community_posts 表 |
| v8 | migration_v8.sql | last_active_at 字段 |
| v9 | migration_v9.sql | gifts 表（礼物配置） |

### 检查迁移状态
```bash
cd /var/www/ailoveworld/server
sqlite3 ../data/users.db ".tables"
sqlite3 ../data/users.db "SELECT * FROM gifts;"
```

---

## 🎯 验证清单

部署完成后，请检查以下项目：

- [ ] 服务运行中 (`sudo ./deploy.sh status`)
- [ ] API 健康检查通过 (`curl http://localhost:8000/api/health`)
- [ ] 数据库迁移完成 (`sqlite3 data/users.db ".tables"`)
- [ ] 礼物表有数据 (`SELECT COUNT(*) FROM gifts;`)
- [ ] 日志正常无错误 (`tail logs/server.log`)

---

## 🔍 故障排查

### 服务无法启动
```bash
# 检查端口占用
sudo netstat -tuln | grep 8000

# 检查日志
tail -f /var/www/ailoveworld/logs/server.log

# 检查 Python 版本
python3 --version

# 检查依赖
pip3 list | grep -i fastapi
```

### 数据库迁移失败
```bash
# 手动执行迁移
cd /var/www/ailoveworld/server
sqlite3 ../data/users.db < migration_v9.sql

# 检查表结构
sqlite3 ../data/users.db ".schema gifts"
```

### API 无法访问
```bash
# 检查防火墙
sudo ufw status

# 检查服务
curl -v http://localhost:8000/api/health

# 重启服务
sudo ./deploy.sh restart
```

---

## 📝 更新日志

**v2.3.0 (2026-02-28)**
- ✅ 添加一键部署脚本
- ✅ 自动化数据库迁移
- ✅ 服务管理功能
- ✅ 健康检查
- ✅ 日志管理

---

**文档版本:** v1.0  
**最后更新:** 2026-02-28
