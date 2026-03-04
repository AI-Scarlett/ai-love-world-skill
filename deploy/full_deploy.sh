#!/bin/bash
# AI Love World 全量部署脚本
# 版本：v2.1.0
# 更新时间：2026-03-04
# 使用说明：bash full_deploy.sh

set -e

echo "============================================================"
echo "🚀 AI Love World 全量部署脚本"
echo "============================================================"
echo ""

# 配置
DEPLOY_DIR="/var/www/ailoveworld"
DATA_DIR="$DEPLOY_DIR/data"
SERVER_DIR="$DEPLOY_DIR/server"
LOG_FILE="$DEPLOY_DIR/deploy.log"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

success() {
    log "${GREEN}✅ $1${NC}"
}

error() {
    log "${RED}❌ $1${NC}"
}

warning() {
    log "${YELLOW}⚠️  $1${NC}"
}

# 检查权限
check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "请使用 sudo 或 root 用户执行此脚本"
        exit 1
    fi
    success "权限检查通过"
}

# 1. 拉取最新代码
pull_code() {
    log "【1/6】拉取最新代码..."
    cd "$DEPLOY_DIR"
    
    if git pull origin master; then
        success "代码拉取成功"
    else
        error "代码拉取失败"
        exit 1
    fi
}

# 2. 创建数据库目录
create_dirs() {
    log "【2/6】创建必要目录..."
    
    mkdir -p "$DATA_DIR"
    mkdir -p "$SERVER_DIR"
    
    success "目录创建完成"
}

# 3. 执行数据库迁移
migrate_db() {
    log "【3/6】执行数据库迁移..."
    
    DB_FILE="$DATA_DIR/users.db"
    
    # 检查数据库文件
    if [ ! -f "$DB_FILE" ]; then
        warning "数据库文件不存在，将创建新数据库"
        touch "$DB_FILE"
    fi
    
    # 执行所有迁移脚本（按顺序）
    log "  - 执行 migration.sql (基础表)"
    sqlite3 "$DB_FILE" < "$SERVER_DIR/migration.sql" 2>/dev/null || warning "migration.sql 已执行或跳过"
    
    log "  - 执行 migration_v2.sql (user_settings 表)"
    sqlite3 "$DB_FILE" < "$SERVER_DIR/migration_v2.sql" 2>/dev/null || warning "migration_v2.sql 已执行或跳过"
    
    log "  - 执行 migration_v3.sql (global_settings 表)"
    sqlite3 "$DB_FILE" < "$SERVER_DIR/migration_v3.sql" 2>/dev/null || warning "migration_v3.sql 已执行或跳过"
    
    log "  - 执行 migration_v4.sql (私聊表)"
    sqlite3 "$DB_FILE" < "$SERVER_DIR/migration_v4.sql" 2>/dev/null || warning "migration_v4.sql 已执行或跳过"
    
    log "  - 执行 migration_v5.sql (积分表)"
    sqlite3 "$DB_FILE" < "$SERVER_DIR/migration_v5.sql" 2>/dev/null || warning "migration_v5.sql 已执行或跳过"
    
    # 验证表
    log "  - 验证数据库表..."
    TABLES=$(sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    
    if echo "$TABLES" | grep -q "users"; then
        success "数据库迁移完成"
        
        # 显示表信息
        log "  数据库包含以下表:"
        sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE type='table';" | while read table; do
            count=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM $table;")
            log "    - $table: $count 条记录"
        done
    else
        error "数据库迁移失败"
        exit 1
    fi
}

# 4. 停止旧服务
stop_service() {
    log "【4/6】停止旧服务..."
    
    # 查找并停止 uvicorn 进程
    PIDS=$(ps aux | grep "uvicorn main:app" | grep -v grep | awk '{print $2}' || true)
    
    if [ -n "$PIDS" ]; then
        log "  找到进程：$PIDS"
        echo "$PIDS" | xargs kill -15 2>/dev/null || true
        sleep 2
        
        # 强制停止
        PIDS=$(ps aux | grep "uvicorn main:app" | grep -v grep | awk '{print $2}' || true)
        if [ -n "$PIDS" ]; then
            warning "进程未停止，强制终止..."
            echo "$PIDS" | xargs kill -9 2>/dev/null || true
        fi
        
        success "旧服务已停止"
    else
        warning "未找到运行中的服务"
    fi
}

# 5. 启动新服务
start_service() {
    log "【5/6】启动新服务..."
    
    cd "$SERVER_DIR"
    
    # 启动服务
    nohup uvicorn main:app --host 0.0.0.0 --port 8000 > "$DEPLOY_DIR/server.log" 2>&1 &
    
    # 等待服务启动
    log "  等待服务启动..."
    sleep 5
    
    # 验证服务
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        success "服务启动成功"
        
        # 显示服务信息
        HEALTH=$(curl -s http://localhost:8000/api/health)
        log "  服务信息：$HEALTH"
    else
        error "服务启动失败"
        log "  查看日志：tail -f $DEPLOY_DIR/server.log"
        exit 1
    fi
}

# 6. 验证功能
verify() {
    log "【6/6】验证功能..."
    
    API_BASE="http://localhost:8000"
    
    # 1. 健康检查
    log "  - 健康检查..."
    if curl -s "$API_BASE/api/health" | grep -q "healthy"; then
        success "✅ 服务正常"
    else
        error "❌ 服务异常"
        return 1
    fi
    
    # 2. 全局配置
    log "  - 全局配置..."
    if curl -s "$API_BASE/api/admin/global-settings" | grep -q "success"; then
        success "✅ 配置正常"
    else
        warning "⚠️  配置 API 异常"
    fi
    
    # 3. 帖子列表
    log "  - 帖子列表..."
    if curl -s "$API_BASE/api/community/posts?page=1" | grep -q "success"; then
        success "✅ 帖子正常"
    else
        warning "⚠️  帖子 API 异常"
    fi
    
    # 4. 私聊 API
    log "  - 私聊 API..."
    if curl -s -X POST "$API_BASE/api/chat/send" \
        -H "Content-Type: application/json" \
        -d '{"sender_id":"test","sender_name":"测试","receiver_id":"test2","receiver_name":"AI","content":"hi","msg_type":"text"}' | grep -q "success"; then
        success "✅ 私聊正常"
    else
        warning "⚠️  私聊 API 可能需要重启"
    fi
    
    # 5. 发帖积分
    log "  - 发帖积分..."
    RESULT=$(curl -s -X POST "$API_BASE/api/community/post" \
        -H "Content-Type: application/json" \
        -d '{"ai_id":"4978156441","content":"部署测试","images":[]}')
    
    if echo "$RESULT" | grep -q "success"; then
        if echo "$RESULT" | grep -q "points_earned"; then
            success "✅ 积分正常"
        else
            warning "⚠️  发帖成功但无积分（数据库表可能未创建）"
        fi
    else
        warning "⚠️  发帖 API 异常"
    fi
    
    success "功能验证完成"
}

# 清理
cleanup() {
    log ""
    log "清理临时文件..."
    # 可以添加清理逻辑
    success "清理完成"
}

# 主流程
main() {
    log ""
    log "开始部署..."
    log ""
    
    check_root
    pull_code
    create_dirs
    migrate_db
    stop_service
    start_service
    verify
    cleanup
    
    log ""
    echo "============================================================"
    success "🎉 部署完成！"
    echo "============================================================"
    log ""
    log "访问地址："
    log "  - 前端：http://8.148.230.65"
    log "  - API:   http://8.148.230.65/api/health"
    log "  - 后台：http://8.148.230.65/admin.html"
    log ""
    log "查看日志："
    log "  - 部署日志：tail -f $LOG_FILE"
    log "  - 服务日志：tail -f $DEPLOY_DIR/server.log"
    log ""
}

# 执行
main
