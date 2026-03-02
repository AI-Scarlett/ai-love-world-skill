#!/bin/bash
# ============================================================
# AI Love World - 全量更新部署脚本
# 版本: v3.0.0
# 作者: 丝佳丽 💋
# 用途: 完整更新服务器代码、显示更新结果
# ============================================================

set -e

# ==================== 配置 ====================

PROJECT_DIR="${PROJECT_DIR:-/var/www/ailoveworld}"
BACKUP_DIR="/var/www/ailoveworld_backups"
LOG_FILE="/var/log/ailoveworld/update_$(date +%Y%m%d_%H%M%S).log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ==================== 工具函数 ====================

log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

print_banner() {
    clear
    echo ""
    log "${PURPLE}╔══════════════════════════════════════════════════════════╗${NC}"
    log "${PURPLE}║${NC}                                                          ${PURPLE}║${NC}"
    log "${PURPLE}║${NC}  ${BOLD}${CYAN}💕 AI Love World 全量更新部署 v3.0.0${NC}                      ${PURPLE}║${NC}"
    log "${PURPLE}║${NC}  ${YELLOW}作者: 丝佳丽 💋${NC}                                        ${PURPLE}║${NC}"
    log "${PURPLE}║${NC}                                                          ${PURPLE}║${NC}"
    log "${PURPLE}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_section() {
    echo ""
    log "${CYAN}┌──────────────────────────────────────────────────────────┐${NC}"
    log "${CYAN}│${NC} ${BOLD}$1${NC}"
    log "${CYAN}└──────────────────────────────────────────────────────────┘${NC}"
    echo ""
}

print_success() {
    log "${GREEN}✅ $1${NC}"
}

print_error() {
    log "${RED}❌ $1${NC}"
}

print_warning() {
    log "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    log "${BLUE}ℹ️  $1${NC}"
}

# ==================== 检查函数 ====================

check_requirements() {
    print_section "🔍 检查环境"
    
    local errors=0
    
    # 检查项目目录
    if [ ! -d "$PROJECT_DIR" ]; then
        print_error "项目目录不存在: $PROJECT_DIR"
        print_info "请先运行初次部署脚本"
        exit 1
    fi
    print_success "项目目录存在"
    
    # 检查 Git
    if ! command -v git &> /dev/null; then
        print_error "Git 未安装"
        ((errors++))
    else
        print_success "Git 已安装: $(git --version)"
    fi
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        ((errors++))
    else
        print_success "Python 已安装: $(python3 --version)"
    fi
    
    # 检查虚拟环境
    if [ ! -d "$PROJECT_DIR/venv" ]; then
        print_warning "虚拟环境不存在，将创建"
    else
        print_success "虚拟环境存在"
    fi
    
    if [ $errors -gt 0 ]; then
        print_error "环境检查失败，请先安装缺失的依赖"
        exit 1
    fi
}

# ==================== 备份 ====================

backup_current() {
    print_section "📦 备份当前代码"
    
    mkdir -p "$BACKUP_DIR"
    
    local backup_name="backup_$(date +%Y%m%d_%H%M%S)"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    mkdir -p "$backup_path"
    
    # 备份关键文件
    print_info "备份关键文件..."
    cp -r "$PROJECT_DIR/server" "$backup_path/" 2>/dev/null || true
    cp -r "$PROJECT_DIR/web" "$backup_path/" 2>/dev/null || true
    cp -r "$PROJECT_DIR/skills" "$backup_path/" 2>/dev/null || true
    cp "$PROJECT_DIR/.env" "$backup_path/" 2>/dev/null || true
    cp "$PROJECT_DIR/data/users.db" "$backup_path/" 2>/dev/null || true
    
    # 记录当前版本
    cd "$PROJECT_DIR"
    git rev-parse HEAD > "$backup_path/git_commit.txt" 2>/dev/null || echo "unknown" > "$backup_path/git_commit.txt"
    
    print_success "备份完成: $backup_path"
    
    # 清理旧备份（保留最近 10 个）
    cd "$BACKUP_DIR"
    local backup_count=$(ls -d backup_* 2>/dev/null | wc -l)
    if [ "$backup_count" -gt 10 ]; then
        print_info "清理旧备份..."
        ls -dt backup_* | tail -n +11 | xargs rm -rf 2>/dev/null || true
    fi
}

# ==================== Git 更新 ====================

update_from_git() {
    print_section "📥 从 Git 仓库更新代码"
    
    cd "$PROJECT_DIR"
    
    # 获取当前版本信息
    local old_commit=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    local old_branch=$(git branch --show-current 2>/dev/null || echo "unknown")
    
    print_info "当前分支: $old_branch"
    print_info "当前提交: ${old_commit:0:8}"
    
    # 拉取最新代码
    print_info "正在拉取最新代码..."
    
    git fetch origin 2>&1 | tee -a "$LOG_FILE"
    
    # 检查是否有更新
    local remote_commit=$(git rev-parse "origin/$old_branch" 2>/dev/null || echo "unknown")
    
    if [ "$old_commit" = "$remote_commit" ]; then
        print_warning "代码已是最新版本"
        return 0
    fi
    
    # 显示更新的内容
    print_info "更新内容:"
    git log --oneline HEAD..origin/$old_branch 2>/dev/null | head -10 | while read line; do
        log "   $line"
    done
    
    # 执行更新
    git reset --hard "origin/$old_branch" 2>&1 | tee -a "$LOG_FILE"
    
    local new_commit=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    
    print_success "代码更新完成"
    print_info "新提交: ${new_commit:0:8}"
    
    # 显示变更统计
    echo ""
    print_info "变更统计:"
    git diff --stat "$old_commit" "$new_commit" 2>/dev/null | tail -5 | while read line; do
        log "   $line"
    done
}

# ==================== 依赖更新 ====================

update_dependencies() {
    print_section "🐍 更新 Python 依赖"
    
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
    pip install --upgrade pip -q 2>&1 | tee -a "$LOG_FILE"
    
    # 安装依赖
    if [ -f "server/requirements.txt" ]; then
        print_info "安装服务端依赖..."
        pip install -r server/requirements.txt -q 2>&1 | tee -a "$LOG_FILE"
    fi
    
    if [ -f "requirements.txt" ]; then
        print_info "安装项目依赖..."
        pip install -r requirements.txt -q 2>&1 | tee -a "$LOG_FILE"
    fi
    
    # 确保关键依赖存在
    print_info "检查关键依赖..."
    pip install fastapi uvicorn httpx pyjwt python-dotenv cryptography -q 2>&1 | tee -a "$LOG_FILE"
    
    print_success "依赖更新完成"
    
    # 显示已安装的关键包版本
    print_info "关键包版本:"
    pip show fastapi uvicorn pyjwt 2>/dev/null | grep -E "^(Name|Version)" | while read line; do
        log "   $line"
    done
}

# ==================== 服务重启 ====================

restart_services() {
    print_section "🔄 重启服务"
    
    cd "$PROJECT_DIR"
    
    # 检测服务管理器
    if command -v supervisorctl &> /dev/null && supervisorctl status &> /dev/null; then
        print_info "使用 supervisorctl 管理服务"
        
        # 重启所有 ailoveworld 相关服务
        for service in $(supervisorctl status | grep ailoveworld | awk '{print $1}'); do
            print_info "重启 $service..."
            supervisorctl restart "$service" 2>&1 | tee -a "$LOG_FILE"
        done
        
        sleep 3
        
        # 显示服务状态
        echo ""
        print_info "服务状态:"
        supervisorctl status | grep ailoveworld | while read line; do
            if echo "$line" | grep -q "RUNNING"; then
                log "   ${GREEN}✓ $line${NC}"
            else
                log "   ${RED}✗ $line${NC}"
            fi
        done
        
    elif command -v systemctl &> /dev/null; then
        print_info "使用 systemctl 管理服务"
        
        for service in ailoveworld-api ailoveworld-auth ailoveworld-user ailoveworld-skill ailoveworld-admin; do
            if systemctl list-unit-files | grep -q "$service"; then
                print_info "重启 $service..."
                systemctl restart "$service" 2>&1 | tee -a "$LOG_FILE"
            fi
        done
        
        sleep 3
        
        echo ""
        print_info "服务状态:"
        for service in ailoveworld-api ailoveworld-auth ailoveworld-user ailoveworld-skill ailoveworld-admin; do
            if systemctl list-unit-files | grep -q "$service"; then
                if systemctl is-active "$service" > /dev/null 2>&1; then
                    log "   ${GREEN}✓ $service: 运行中${NC}"
                else
                    log "   ${RED}✗ $service: 已停止${NC}"
                fi
            fi
        done
    else
        print_warning "未检测到服务管理器，请手动重启服务"
    fi
    
    print_success "服务重启完成"
}

# ==================== 健康检查 ====================

health_check() {
    print_section "🏥 健康检查"
    
    local api_endpoints=(
        "http://127.0.0.1:8000/api/health"
    )
    
    local all_healthy=true
    
    for endpoint in "${api_endpoints[@]}"; do
        local response=$(curl -sf "$endpoint" 2>/dev/null)
        if [ $? -eq 0 ]; then
            log "   ${GREEN}✓ $endpoint${NC}"
            log "      响应: $response"
        else
            log "   ${RED}✗ $endpoint 无响应${NC}"
            all_healthy=false
        fi
    done
    
    # 检查 Nginx
    if command -v nginx &> /dev/null; then
        if systemctl is-active nginx > /dev/null 2>&1 || service nginx status > /dev/null 2>&1; then
            log "   ${GREEN}✓ Nginx 运行中${NC}"
        else
            log "   ${RED}✗ Nginx 未运行${NC}"
            all_healthy=false
        fi
    fi
    
    echo ""
    
    if [ "$all_healthy" = true ]; then
        print_success "所有服务健康"
    else
        print_warning "部分服务异常，请检查日志"
    fi
}

# ==================== 显示更新报告 ====================

show_report() {
    print_section "📊 更新报告"
    
    cd "$PROJECT_DIR"
    
    local current_commit=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    local current_branch=$(git branch --show-current 2>/dev/null || echo "unknown")
    local last_update=$(git log -1 --format="%ci" 2>/dev/null || echo "unknown")
    
    log "${BOLD}项目信息:${NC}"
    log "   分支: $current_branch"
    log "   提交: ${current_commit:0:8}"
    log "   时间: $last_update"
    echo ""
    
    # 获取服务器 IP
    local server_ip=$(curl -sf ifconfig.me 2>/dev/null || echo "your-server-ip")
    
    log "${BOLD}访问地址:${NC}"
    log "   首页:    http://$server_ip"
    log "   登录:    http://$server_ip/login.html"
    log "   创建AI:  http://$server_ip/register.html"
    log "   管理后台: http://$server_ip/admin.html"
    echo ""
    
    log "${BOLD}常用命令:${NC}"
    log "   查看日志:     tail -f $PROJECT_DIR/logs/api.log"
    log "   重启服务:     supervisorctl restart ailoworld-api"
    log "   查看状态:     supervisorctl status"
    echo ""
    
    log "${BOLD}备份位置:${NC}"
    log "   $BACKUP_DIR"
    echo ""
}

# ==================== 主函数 ====================

main() {
    # 创建日志目录
    mkdir -p /var/log/ailoveworld
    
    print_banner
    
    local start_time=$(date +%s)
    
    check_requirements
    backup_current
    update_from_git
    update_dependencies
    restart_services
    health_check
    show_report
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo ""
    log "${PURPLE}╔══════════════════════════════════════════════════════════╗${NC}"
    log "${PURPLE}║${NC}                                                          ${PURPLE}║${NC}"
    log "${PURPLE}║${NC}  ${GREEN}${BOLD}✅ 更新完成！耗时 ${duration} 秒${NC}                                ${PURPLE}║${NC}"
    log "${PURPLE}║${NC}  ${YELLOW}日志文件: $LOG_FILE${NC}"
    log "${PURPLE}║${NC}                                                          ${PURPLE}║${NC}"
    log "${PURPLE}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    log "${CYAN}💋 丝佳丽祝您使用愉快！${NC}"
    echo ""
}

# 运行
main "$@"