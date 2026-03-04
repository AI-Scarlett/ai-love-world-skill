#!/bin/bash
# AI Love World 自动化部署脚本
# 使用方法：./auto_deploy.sh

set -e

echo "========================================"
echo "🚀 AI Love World 自动化部署"
echo "========================================"
echo ""

# 配置
PROJECT_DIR="/var/www/ailoveworld"
BACKUP_DIR="/var/www/ailoveworld_backup"
REPO_URL="https://codeup.aliyun.com/69a0572966d410a0f265834c/AILOVE1/AILOVE_V1.git"
CODEUP_USER="1129323634546582"
CODEUP_TOKEN="pt-fqXLkLFxt0FtsZOrjMY4f35z_3ad4bc37-b332-4160-ba47-11c0d69b248f"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_step() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 1. 检查是否在服务器上
if [ ! -d "$PROJECT_DIR" ]; then
    echo_warn "项目目录不存在，可能是首次部署"
    echo "创建目录..."
    sudo mkdir -p $PROJECT_DIR
    echo_step "目录创建完成"
fi

# 2. 备份现有代码
if [ -d "$PROJECT_DIR" ] && [ "$(ls -A $PROJECT_DIR)" ]; then
    echo "备份现有代码..."
    sudo cp -r $PROJECT_DIR $BACKUP_DIR/$(date +%Y%m%d_%H%M%S)
    echo_step "备份完成"
fi

# 3. 拉取最新代码
cd $PROJECT_DIR

if [ -d ".git" ]; then
    echo "拉取最新代码..."
    # 更新认证信息
    git remote set-url origin https://${CODEUP_USER}:${CODEUP_TOKEN}@codeup.aliyun.com/69a0572966d410a0f265834c/AILOVE1/AILOVE_V1.git
    sudo git pull origin master
    echo_step "代码更新完成"
else
    echo "克隆仓库..."
    sudo git clone https://${CODEUP_USER}:${CODEUP_TOKEN}@codeup.aliyun.com/69a0572966d410a0f265834c/AILOVE1/AILOVE_V1.git .
    echo_step "代码克隆完成"
fi

# 4. 安装依赖
echo "安装 Python 依赖..."
if [ -f "server/requirements.txt" ]; then
    sudo pip3 install -r server/requirements.txt
    echo_step "服务器依赖安装完成"
fi

if [ -f "skills/ai-love-world/requirements.txt" ]; then
    sudo pip3 install -r skills/ai-love-world/requirements.txt
    echo_step "Skill 依赖安装完成"
fi

# 5. 检查数据库
echo "检查数据库..."
DB_DIR="/var/www/ailoveworld/data"
if [ ! -d "$DB_DIR" ]; then
    sudo mkdir -p $DB_DIR
    echo_warn "数据库目录已创建"
else
    echo_step "数据库目录存在"
fi

# 6. 重启服务
echo "重启服务..."
# 查找进程
PID=$(ps aux | grep "uvicorn main:app" | grep -v grep | awk '{print $2}')

if [ ! -z "$PID" ]; then
    echo "停止旧进程 (PID: $PID)..."
    sudo kill $PID
    sleep 2
    echo_step "服务已停止"
fi

# 启动新进程
echo "启动新服务..."
cd $PROJECT_DIR/server
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > /var/www/ailoveworld/server.log 2>&1 &
NEW_PID=$!
echo_step "服务已启动 (PID: $NEW_PID)"

# 7. 验证服务
echo "验证服务..."
sleep 3
HEALTH=$(curl -s http://localhost:8000/api/health)

if echo $HEALTH | grep -q "healthy"; then
    echo_step "服务健康检查通过"
    echo "服务状态：$HEALTH"
else
    echo_error "服务健康检查失败"
    echo "查看日志：tail -f /var/www/ailoveworld/server.log"
    exit 1
fi

# 8. 清理旧备份
echo "清理旧备份..."
sudo find $BACKUP_DIR -type d -mtime +7 -exec rm -rf {} \; 2>/dev/null || true
echo_step "清理完成"

echo ""
echo "========================================"
echo "🎉 部署完成！"
echo "========================================"
echo ""
echo "服务地址：http://8.148.230.65:8000"
echo "健康检查：http://8.148.230.65:8000/api/health"
echo "日志文件：tail -f /var/www/ailoveworld/server.log"
echo ""
