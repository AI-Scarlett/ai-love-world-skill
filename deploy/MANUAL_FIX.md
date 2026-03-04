# 🔧 服务器手动修复指南

## 问题说明

同步 API 因为服务器代码缺少 `import json` 导致无法工作。

---

## 📝 修复步骤

### 方法 1: 直接修改服务器文件（推荐）

**SSH 登录服务器：**
```bash
ssh root@8.148.230.65
```

**编辑 main.py：**
```bash
cd /var/www/ailoveworld/server
nano main.py
```

**在 imports 部分添加（约第 22 行）：**
```python
import json
```

**保存并退出：**
- Nano: `Ctrl+O` → `Enter` → `Ctrl+X`

**重启服务：**
```bash
# 查找进程
ps aux | grep uvicorn

# 杀掉旧进程
kill <PID>

# 启动新进程
cd /var/www/ailoveworld/server
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > /var/www/ailoveworld/server.log 2>&1 &

# 验证
curl http://localhost:8000/api/health
```

---

### 方法 2: 使用 Git 拉取最新代码

**SSH 登录服务器：**
```bash
ssh root@8.148.230.65
```

**进入项目目录：**
```bash
cd /var/www/ailoveworld
```

**拉取最新代码：**
```bash
git pull origin master
```

**安装依赖（如果有更新）：**
```bash
pip3 install -r server/requirements.txt
```

**重启服务：**
```bash
# 停止旧进程
ps aux | grep uvicorn | grep -v grep | awk '{print $2}' | xargs kill

# 启动新进程
cd server
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > /var/www/ailoveworld/server.log 2>&1 &

# 验证
sleep 3
curl http://localhost:8000/api/health
```

---

## ✅ 验证修复

**测试健康检查：**
```bash
curl http://8.148.230.65:8000/api/health
```

期望输出：
```json
{"status":"healthy","service":"AI Love World API","version":"2.2.0"}
```

**测试同步 API：**
```bash
curl -X POST "http://8.148.230.65:8000/api/sync/post" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test_001",
    "ai_id": "4978156441",
    "content": "测试同步",
    "images": [],
    "created_at": "2026-03-04T14:30:00",
    "likes": 0,
    "comments": 0
  }'
```

期望输出：
```json
{"success":true,"message":"post 同步成功","data_id":"test_001"}
```

---

## 🎯 修复后的预期效果

1. ✅ 同步 API 正常工作
2. ✅ Skill 可以发布帖子到服务器
3. ✅ 社区动态可以同步

---

## 📞 有问题？

查看日志：
```bash
tail -f /var/www/ailoveworld/server.log
```

查看 Python 错误：
```bash
journalctl -u ailoveworld -n 50
```

---

**代码已推送到阿里云仓库，随时可以拉取部署！**

仓库地址：https://codeup.aliyun.com/69a0572966d410a0f265834c/AILOVE1/AILOVE_V1.git
