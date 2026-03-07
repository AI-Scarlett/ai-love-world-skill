#!/bin/bash
# AI Love World - 一键部署脚本
# 版本：v2.3.0
# 功能：数据库迁移 + 服务重启 + 健康检查

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
APP_DIR="/var/www/ailoveworld"
SERVER_DIR="$APP_DIR/server"
DATA_DIR="$APP_DIR/data"
LOG_DIR="$APP_DIR/logs"
SERVER_LOG="$LOG_DIR/server.log"
PID_FILE="$APP_DIR/server.pid"
PORT=8000

# 打印函数
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否以 root 运行
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "请使用 sudo 运行此脚本"
        exit 1
    fi
}

# 检查目录是否存在
check_dirs() {
    print_info "检查目录结构..."
    
    if [ ! -d "$APP_DIR" ]; then
        print_error "应用目录不存在：$APP_DIR"
        exit 1
    fi
    
    if [ ! -d "$SERVER_DIR" ]; then
        print_error "服务器目录不存在：$SERVER_DIR"
        exit 1
    fi
    
    # 创建必要目录
    mkdir -p "$DATA_DIR" "$LOG_DIR"
    
    print_success "目录检查完成"
}

# 停止旧服务
stop_service() {
    print_info "停止旧服务..."
    
    # 方法 1: 通过 PID 文件
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if kill -0 "$OLD_PID" 2>/dev/null; then
            kill "$OLD_PID"
            print_info "已停止进程 (PID: $OLD_PID)"
            sleep 2
        fi
        rm -f "$PID_FILE"
    fi
    
    # 方法 2: 通过进程名
    if pgrep -f "uvicorn.*main:app" > /dev/null; then
        pkill -f "uvicorn.*main:app"
        print_info "已停止 uvicorn 进程"
        sleep 2
    fi
    
    print_success "旧服务已停止"
}

# 执行数据库迁移
run_migrations() {
    print_info "执行数据库迁移..."
    
    DB_FILE="$DATA_DIR/users.db"
    
    # 检查数据库文件
    if [ ! -f "$DB_FILE" ]; then
        print_warning "数据库文件不存在，将创建新数据库"
        touch "$DB_FILE"
    fi
    
    # 执行所有迁移脚本
    MIGRATION_COUNT=0
    
    for migration in $(ls -1 "$SERVER_DIR"/migration_v*.sql 2>/dev/null | sort); do
        migration_name=$(basename "$migration")
        print_info "执行迁移：$migration_name"
        
        if sqlite3 "$DB_FILE" < "$migration"; then
            print_success "✓ $migration_name 完成"
            ((MIGRATION_COUNT++))
        else
            print_warning "✗ $migration_name 失败（可能已执行过）"
        fi
    done
    
    if [ $MIGRATION_COUNT -eq 0 ]; then
        print_warning "没有发现迁移脚本或所有迁移已执行"
    else
        print_success "完成 $MIGRATION_COUNT 个数据库迁移"
    fi
}

# 检查 Python 依赖
check_dependencies() {
    print_info "检查 Python 依赖..."
    
    cd "$SERVER_DIR"
    
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt -q
        print_success "依赖安装完成"
    else
        print_warning "未找到 requirements.txt"
    fi
}

# 启动新服务
start_service() {
    print_info "启动新服务..."
    
    cd "$SERVER_DIR"
    
    # 检查端口是否被占用
    if netstat -tuln 2>/dev/null | grep -q ":$PORT "; then
        print_error "端口 $PORT 已被占用"
        exit 1
    fi
    
    # 启动服务
    nohup python3 -m uvicorn main:app \
        --host 0.0.0.0 \
        --port $PORT \
        --reload \
        > "$SERVER_LOG" 2>&1 &
    
    NEW_PID=$!
    echo $NEW_PID > "$PID_FILE"
    
    print_info "服务已启动 (PID: $NEW_PID)"
    print_info "日志文件：$SERVER_LOG"
    
    # 等待服务启动
    sleep 3
    
    # 检查服务是否正常运行
    if kill -0 $NEW_PID 2>/dev/null; then
        print_success "服务启动成功"
    else
        print_error "服务启动失败，请检查日志：$SERVER_LOG"
        exit 1
    fi
}

# 健康检查
health_check() {
    print_info "执行健康检查..."
    
    sleep 2
    
    # 检查 API 响应
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/api/health" | grep -q "200"; then
        print_success "API 健康检查通过"
    else
        print_error "API 健康检查失败"
        exit 1
    fi
    
    # 显示服务信息
    echo ""
    echo "================================"
    echo -e "${GREEN}✅ AI Love World 部署完成！${NC}"
    echo "================================"
    echo "服务地址：http://localhost:$PORT"
    echo "API 地址：http://localhost:$PORT/api/health"
    echo "进程 PID: $(cat $PID_FILE)"
    echo "日志文件：$SERVER_LOG"
    echo "================================"
    echo ""
}

# 显示服务状态
show_status() {
    print_info "服务状态："
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 $PID 2>/dev/null; then
            print_success "服务运行中 (PID: $PID)"
        else
            print_error "服务未运行 (PID 文件存在但进程不存在)"
        fi
    else
        print_warning "服务未启动"
    fi
}

# 清理旧日志
cleanup_logs() {
    print_info "清理旧日志..."
    
    # 保留最近 7 天的日志
    if [ -f "$SERVER_LOG" ]; then
        find "$LOG_DIR" -name "*.log" -mtime +7 -delete 2>/dev/null || true
        print_success "日志清理完成"
    fi
}

# 主函数
main() {
    echo ""
    echo "================================"
    echo -e "${BLUE}🚀 AI Love World 一键部署${NC}"
    echo "版本：v2.3.0"
    echo "================================"
    echo ""
    
    check_root
    check_dirs
    stop_service
    run_migrations
    check_dependencies
    start_service
    health_check
    cleanup_logs
    
    print_success "🎉 部署完成！"
    echo ""
}

# 显示帮助
show_help() {
    echo "AI Love World 部署脚本"
    echo ""
    echo "用法：$0 [命令]"
    echo ""
    echo "命令:"
    echo "  deploy    完整部署（默认）"
    echo "  start     仅启动服务"
    echo "  stop      停止服务"
    echo "  restart   重启服务"
    echo "  status    查看状态"
    echo "  migrate   仅执行数据库迁移"
    echo "  logs      查看日志"
    echo "  help      显示帮助"
    echo ""
}

# 命令处理
case "${1:-deploy}" in
    deploy)
        main
        ;;
    start)
        check_root
        check_dirs
        start_service
        health_check
        ;;
    stop)
        check_root
        stop_service
        print_success "服务已停止"
        ;;
    restart)
        check_root
        stop_service
        start_service
        health_check
        ;;
    status)
        show_status
        ;;
    migrate)
        check_root
        check_dirs
        run_migrations
        ;;
    logs)
        tail -f "$SERVER_LOG"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "未知命令：$1"
        show_help
        exit 1
        ;;
esac
