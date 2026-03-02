#!/bin/bash
# ============================================================
# AI Love World - 服务器更新部署脚本
# 版本: v2.0.0
# 作者: 丝佳丽 💋
# 用途: 已部署服务器的代码更新、依赖更新、服务重启
# ============================================================

set -e

# ==================== 配置区域 ====================

# 项目目录（根据实际服务器修改）
PROJECT_DIR="${PROJECT_DIR:-/var/www/ailoveworld}"

# 备份目录
BACKUP_BASE="/var/www/ailoveworld_backups"

# 日志目录
LOG_DIR="${PROJECT_DIR}/logs"

# 服务名称（支持 systemd 和 supervisorctl）
SERVICE_MANAGER="${SERVICE_MANAGER:-systemd}"  # systemd 或 supervisor

# 服务列表
SERVICES="ailoveworld-api ailoveworld-auth ailoveworld-user ailoveworld-skill ailoveworld-admin"

# Git 分支
GIT_BRANCH="${GIT_BRANCH:-master}"

# 阿里云 Codeup 配置
CODEUP_USER="1129323634546582"
CODEUP_TOKEN="${CODEUP_TOKEN:-}"  # 设置环境变量或填入

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# ==================== 工具函数 ====================

print_banner() {
    echo ""
    echo -e "${PURPLE}============================================${NC}"
    echo -e "${PURPLE}💕 AI Love World 服务器更新部署${NC}"
    echo -e "${PURPLE}版本: v2.0.0 | 作者: 丝佳丽 💋${NC}"
    echo -e "${PURPLE}============================================${NC}"
    echo ""
}

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

print_step() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}📦 $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# 获取当前时间戳
get_timestamp() {
    date +%Y%m%d_%H%M%S
}

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "$1 未安装"
        return 1
    fi
    return 0
}

# ==================== 预检查 ====================

preflight_check() {
    print_step "预检查"
    
    # 检查项目目录
    if [ ! -d "$PROJECT_DIR" ]; then
        print_error "项目目录不存在: $PROJECT_DIR"
        print_info "请先运行初次部署脚本"
        exit 1
    fi
    
    # 检查是否在项目目录内
    if [ ! -d "$PROJECT_DIR/.git" ]; then
        print_error "不是 Git 仓库: $PROJECT_DIR"
        exit 1
    fi
    
    # 检查 Python
    if ! check_command python3; then
        exit 1
    fi
    
    # 检查 Git
    if ! check_command git; then
        exit 1
    fi
    
    # 检查虚拟环境
    if [ ! -d "$PROJECT_DIR/venv" ]; then
        print_warning "虚拟环境不存在，将创建"
    fi
    
    print_success "预检查通过 ✓"
}

# ==================== 备份 ====================

backup_code() {
    print_step "备份当前代码"
    
    mkdir -p "$BACKUP_BASE"
    
    BACKUP_DIR="$BACKUP_BASE/backup_$(get_timestamp)"
    
    print_info "备份目录: $BACKUP_DIR"
    
    # 创建备份
    mkdir -p "$BACKUP_DIR"
    
    # 备份代码（排除虚拟环境和日志）
    rsync -av --exclude='venv' --exclude='*.log' --exclude='__pycache__' --exclude='.git' \
        "$PROJECT_DIR/" "$BACKUP_DIR/" 2>/dev/null || true
    
    # 备份数据库
    if [ -f "$PROJECT_DIR/data/users.db" ]; then
        cp "$PROJECT_DIR/data/users.db" "$BACKUP_DIR/users.db"
        print_info "数据库已备份"
    fi
    
    # 备份环境变量
    if [ -f "$PROJECT_DIR/.env" ]; then
        cp "$PROJECT_DIR/.env" "$BACKUP_DIR/.env.backup"
        print_info "环境变量已备份"
    fi
    
    # 记录当前 Git commit
    cd "$PROJECT_DIR"
    CURRENT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    echo "$CURRENT_COMMIT" > "$BACKUP_DIR/git_commit.txt"
    
    print_success "备份完成 ✓"
    print_info "备份位置: $BACKUP_DIR"
    
    # 清理旧备份（保留最近 5 个）
    cd "$BACKUP_BASE"
    BACKUP_COUNT=$(ls -d backup_* 2>/dev/null | wc -l)
    if [ "$BACKUP_COUNT" -gt 5 ]; then
        print_info "清理旧备份..."
        ls -dt backup_* | tail -n +6 | xargs rm -rf 2>/dev/null || true
    fi
}

# ==================== 拉取代码 ====================

pull_code() {
    print_step "拉取最新代码"
    
    cd "$PROJECT_DIR"
    
    # 配置 Git 凭证（如果提供了 Token）
    if [ -n "$CODEUP_TOKEN" ]; then
        git config credential.helper store
        echo "https://${CODEUP_USER}:${CODEUP_TOKEN}@codeup.aliyun.com" > ~/.git-credentials 2>/dev/null || true
    fi
    
    # 获取当前分支和 commit
    CURRENT_BRANCH=$(git branch --show-current)
    CURRENT_COMMIT=$(git rev-parse HEAD)
    
    print_info "当前分支: $CURRENT_BRANCH"
    print_info "当前 commit: ${CURRENT_COMMIT:0:8}"
    
    # 拉取最新代码
    print_info "正在拉取..."
    
    git fetch origin
    
    # 检查是否有更新
    REMOTE_COMMIT=$(git rev-parse "origin/$GIT_BRANCH")
    if [ "$CURRENT_COMMIT" = "$REMOTE_COMMIT" ]; then
        print_warning "代码已是最新版本"
        return 0
    fi
    
    # 显示更新的 commits
    print_info "更新内容:"
    git log --oneline HEAD..origin/$GIT_BRANCH | head -10
    
    # 重置到最新
    git fetch origin
    git reset --hard "origin/$GIT_BRANCH"
    
    NEW_COMMIT=$(git rev-parse HEAD)
    print_success "代码更新完成 ✓"
    print_info "新 commit: ${NEW_COMMIT:0:8}"
}

# ==================== 更新依赖 ====================

update_dependencies() {
    print_step "更新 Python 依赖"
    
    cd "$PROJECT_DIR"
    
    # 创建虚拟环境（如果不存在）
    if [ ! -d "venv" ]; then
        print_info "创建虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级 pip
    print_info "升级 pip..."
    pip install --upgrade pip -q
    
    # 安装/更新依赖
    if [ -f "server/requirements.txt" ]; then
        print_info "安装服务端依赖..."
        pip install -r server/requirements.txt -q 2>/dev/null || {
            print_warning "部分依赖安装失败，尝试单独安装..."
            pip install fastapi uvicorn httpx pyjwt python-dotenv cryptography dashscope -q
        }
    fi
    
    if [ -f "requirements.txt" ]; then
        print_info "安装项目依赖..."
        pip install -r requirements.txt -q 2>/dev/null || true
    fi
    
    print_success "依赖更新完成 ✓"
}

# ==================== 数据库迁移 ====================

migrate_database() {
    print_step "数据库迁移检查"
    
    cd "$PROJECT_DIR"
    
    # 确保数据目录存在
    mkdir -p "$PROJECT_DIR/data"
    
    # 检查是否有迁移脚本
    if [ -d "server/migrations" ]; then
        print_info "执行数据库迁移..."
        source venv/bin/activate
        python -m server.migrations 2>/dev/null || print_warning "迁移脚本执行失败或不存在"
    fi
    
    print_success "数据库检查完成 ✓"
}

# ==================== 重启服务 ====================

restart_services() {
    print_step "重启服务"
    
    cd "$PROJECT_DIR"
    
    if [ "$SERVICE_MANAGER" = "supervisor" ]; then
        # 使用 supervisorctl
        if command -v supervisorctl &> /dev/null; then
            for service in $SERVICES; do
                print_info "重启 $service..."
                supervisorctl restart "$service" 2>/dev/null || print_warning "$service 不存在"
            done
            sleep 3
            supervisorctl status
        else
            print_error "supervisorctl 未安装"
            exit 1
        fi
    else
        # 使用 systemd
        for service in $SERVICES; do
            if systemctl list-unit-files | grep -q "$service"; then
                print_info "重启 $service..."
                systemctl restart "$service"
            else
                print_warning "$service 服务不存在，跳过"
            fi
        done
        
        sleep 3
        
        print_info "服务状态:"
        for service in $SERVICES; do
            if systemctl list-unit-files | grep -q "$service"; then
                systemctl is-active "$service" > /dev/null 2>&1 && \
                    print_success "$service: 运行中 ✓" || \
                    print_error "$service: 已停止 ✗"
            fi
        done
    fi
    
    print_success "服务重启完成 ✓"
}

# ==================== 健康检查 ====================

health_check() {
    print_step "健康检查"
    
    # 检查 API 端点
    API_ENDPOINTS=(
        "http://127.0.0.1:8000/api/health"
        "http://127.0.0.1:8001/api/health"
        "http://127.0.0.1:8002/api/health"
        "http://127.0.0.1:8005/api/health"
        "http://127.0.0.1:8006/api/health"
    )
    
    for endpoint in "${API_ENDPOINTS[@]}"; do
        if curl -sf "$endpoint" > /dev/null 2>&1; then
            print_success "$endpoint 正常 ✓"
        else
            print_warning "$endpoint 无响应（可能未启用）"
        fi
    done
    
    # 检查 Nginx
    if command -v nginx &> /dev/null; then
        if systemctl is-active nginx > /dev/null 2>&1; then
            print_success "Nginx 运行中 ✓"
        else
            print_warning "Nginx 未运行"
        fi
    fi
    
    print_success "健康检查完成 ✓"
}

# ==================== 显示信息 ====================

show_info() {
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}✅ 部署更新完成！${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    
    # 获取服务器 IP
    SERVER_IP=$(curl -sf ifconfig.me 2>/dev/null || echo "your-server-ip")
    
    echo -e "${CYAN}📋 访问地址:${NC}"
    echo -e "   HTTP:  http://$SERVER_IP"
    echo -e "   API:   http://$SERVER_IP/api/health"
    echo ""
    
    echo -e "${CYAN}📝 查看日志:${NC}"
    echo "   tail -f $PROJECT_DIR/logs/api.log"
    echo "   journalctl -u ailoveworld-api -f"
    echo ""
    
    echo -e "${CYAN}🔄 服务管理:${NC}"
    echo "   systemctl restart ailoveworld-api   # 重启 API"
    echo "   systemctl restart ailoveworld-auth  # 重启认证"
    echo "   systemctl status ailoveworld-*      # 查看状态"
    echo ""
    
    echo -e "${CYAN}⏪ 如需回滚:${NC}"
    echo "   ls $BACKUP_BASE  # 查看备份列表"
    echo "   ./deploy/update_deploy.sh --rollback  # 回滚到上一个版本"
    echo ""
    
    echo -e "${PURPLE}💋 丝佳丽祝您部署顺利！${NC}"
}

# ==================== 回滚功能 ====================

rollback() {
    print_step "执行回滚"
    
    cd "$BACKUP_BASE"
    
    # 获取最近的备份
    LATEST_BACKUP=$(ls -dt backup_* 2>/dev/null | head -1)
    
    if [ -z "$LATEST_BACKUP" ]; then
        print_error "没有找到备份"
        exit 1
    fi
    
    print_info "将回滚到: $LATEST_BACKUP"
    read -p "确认回滚? (y/N): " confirm
    
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        print_info "取消回滚"
        exit 0
    fi
    
    # 停止服务
    for service in $SERVICES; do
        if systemctl list-unit-files | grep -q "$service"; then
            systemctl stop "$service"
        fi
    done
    
    # 恢复代码
    rsync -av --delete "$BACKUP_BASE/$LATEST_BACKUP/" "$PROJECT_DIR/"
    
    # 恢复环境变量
    if [ -f "$BACKUP_BASE/$LATEST_BACKUP/.env.backup" ]; then
        cp "$BACKUP_BASE/$LATEST_BACKUP/.env.backup" "$PROJECT_DIR/.env"
    fi
    
    # 重启服务
    restart_services
    
    print_success "回滚完成 ✓"
}

# ==================== 主函数 ====================

main() {
    print_banner
    
    # 解析参数
    case "${1:-}" in
        --rollback|-r)
            rollback
            exit 0
            ;;
        --help|-h)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  无参数      执行完整更新部署"
            echo "  --rollback  回滚到上一个版本"
            echo "  --help      显示帮助信息"
            echo ""
            echo "环境变量:"
            echo "  PROJECT_DIR    项目目录 (默认: /var/www/ailoveworld)"
            echo "  SERVICE_MANAGER 服务管理器 (默认: systemd)"
            echo "  GIT_BRANCH     Git 分支 (默认: master)"
            echo "  CODEUP_TOKEN   阿里云 Codeup Token"
            exit 0
            ;;
    esac
    
    # 执行部署流程
    preflight_check
    backup_code
    pull_code
    update_dependencies
    migrate_database
    restart_services
    health_check
    show_info
}

# 执行主函数
main "$@"