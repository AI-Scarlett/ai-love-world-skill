#!/bin/bash
# AI Love World 一键部署脚本
# 版本：v1.0.0
# 用途：生产环境快速部署

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
PROJECT_DIR="/var/www/ailoveworld"
DATA_DIR="/var/www/ailoveworld/data"
LOG_DIR="/var/www/ailoveworld/logs"
REPO_URL="https://codeup.aliyun.com/69a0572966d410a0f265834c/AILOVE1/AILOVE_V1.git"
CODEUP_USER="1129323634546582"

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

# 检查系统依赖
check_dependencies() {
    print_info "检查系统依赖..."
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        exit 1
    fi
    
    # 检查 Git
    if ! command -v git &> /dev/null; then
        print_error "Git 未安装"
        exit 1
    fi
    
    # 检查 Nginx
    if ! command -v nginx &> /dev/null; then
        print_warning "Nginx 未安装，稍后会安装"
    fi
    
    print_success "系统依赖检查完成"
}

# 安装系统依赖
install_dependencies() {
    print_info "安装系统依赖..."
    
    apt update
    apt install -y python3-pip python3-venv nginx mysql-server git curl
    
    print_success "系统依赖安装完成"
}

# 创建目录结构
create_directories() {
    print_info "创建目录结构..."
    
    mkdir -p $PROJECT_DIR
    mkdir -p $DATA_DIR
    mkdir -p $LOG_DIR
    
    chown -R www-data:www-data $PROJECT_DIR
    chmod -R 755 $PROJECT_DIR
    
    print_success "目录创建完成"
}

# 克隆或更新代码
clone_code() {
    print_info "克隆代码..."
    
    cd $PROJECT_DIR
    
    if [ -d ".git" ]; then
        print_info "代码已存在，执行更新..."
        
        # 配置 Git 凭证
        git config credential.helper store
        echo "https://${CODEUP_USER}:${CODEUP_TOKEN}@codeup.aliyun.com" > ~/.git-credentials
        
        git pull origin master
    else
        print_info "首次克隆代码..."
        
        # 配置 Git 凭证
        git config --global credential.helper store
        echo "https://${CODEUP_USER}:${CODEUP_TOKEN}@codeup.aliyun.com" > ~/.git-credentials
        
        git clone $REPO_URL .
    fi
    
    print_success "代码准备完成"
}

# 创建 Python 虚拟环境
setup_venv() {
    print_info "创建 Python 虚拟环境..."
    
    cd $PROJECT_DIR
    
    python3 -m venv venv
    source venv/bin/activate
    
    # 升级 pip
    pip install --upgrade pip
    
    print_success "虚拟环境创建完成"
}

# 安装 Python 依赖
install_python_deps() {
    print_info "安装 Python 依赖..."
    
    cd $PROJECT_DIR
    source venv/bin/activate
    
    # 安装服务端依赖
    if [ -f "server/requirements.txt" ]; then
        pip install -r server/requirements.txt
    fi
    
    # 安装 Skill 依赖（如果部署 Skill）
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
    
    print_success "Python 依赖安装完成"
}

# 初始化数据库
init_database() {
    print_info "初始化数据库..."
    
    # 创建数据库
    mysql -u root -e "CREATE DATABASE IF NOT EXISTS ailoveworld CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    mysql -u root -e "CREATE USER IF NOT EXISTS 'ailove'@'localhost' IDENTIFIED BY '${DB_PASSWORD:-ailove123}';"
    mysql -u root -e "GRANT ALL PRIVILEGES ON ailoveworld.* TO 'ailove'@'localhost';"
    mysql -u root -e "FLUSH PRIVILEGES;"
    
    # 初始化表结构（通过 API 自动创建）
    print_info "数据库初始化完成"
}

# 创建环境变量文件
create_env() {
    print_info "创建环境变量配置..."
    
    cd $PROJECT_DIR
    
    cat > .env << EOF
# AI Love World 环境变量配置

# 数据库配置
DB_PATH=${DATA_DIR}/users.db
DB_HOST=localhost
DB_NAME=ailoveworld
DB_USER=ailove
DB_PASSWORD=${DB_PASSWORD:-ailove123}

# JWT 配置
JWT_SECRET=${JWT_SECRET:-$(openssl rand -hex 32)}

# GitHub OAuth（可选，用于用户登录）
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_CALLBACK_URL=http://your-domain.com/api/auth/github/callback

# 管理员配置
ADMIN_ID=1000000000
ADMIN_PASSWORD=${ADMIN_PASSWORD:-$(openssl rand -base64 16)}

# 通义千问 API（可选，用于情感分析）
DASHSCOPE_API_KEY=

# 服务器地址
SERVER_URL=http://127.0.0.1:8000
EOF

    chmod 600 .env
    
    print_success "环境变量配置完成"
    print_warning "请编辑 .env 文件填写敏感信息"
}

# 配置 Nginx
setup_nginx() {
    print_info "配置 Nginx..."
    
    cat > /etc/nginx/sites-available/ailoveworld << EOF
server {
    listen 80;
    server_name your-domain.com;  # 修改为你的域名
    
    # 静态文件
    location / {
        root $PROJECT_DIR/web;
        try_files \$uri \$uri/ /index.html;
    }
    
    # 主 API 服务
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # 认证服务
    location /api/auth/ {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    # 用户管理
    location /api/user/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    # Skill 验证
    location /api/skill/ {
        proxy_pass http://127.0.0.1:8006;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    # 管理后台
    location /api/admin/ {
        proxy_pass http://127.0.0.1:8005;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    # 日志
    access_log $LOG_DIR/nginx_access.log;
    error_log $LOG_DIR/nginx_error.log;
}
EOF

    # 启用配置
    ln -sf /etc/nginx/sites-available/ailoveworld /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # 测试配置
    nginx -t
    
    # 重启 Nginx
    systemctl restart nginx
    
    print_success "Nginx 配置完成"
}

# 创建 Systemd 服务
create_systemd_services() {
    print_info "创建 Systemd 服务..."
    
    # 主 API 服务
    cat > /etc/systemd/system/ailoveworld-api.service << EOF
[Unit]
Description=AI Love World Main API Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/uvicorn server.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # 认证服务
    cat > /etc/systemd/system/ailoveworld-auth.service << EOF
[Unit]
Description=AI Love World Auth Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/uvicorn server.auth:app --host 0.0.0.0 --port 8002
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # 用户管理服务
    cat > /etc/systemd/system/ailoveworld-user.service << EOF
[Unit]
Description=AI Love World User Management Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/uvicorn server.user:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Skill 验证服务
    cat > /etc/systemd/system/ailoveworld-skill.service << EOF
[Unit]
Description=AI Love World Skill Auth Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/uvicorn server.skill_auth:app --host 0.0.0.0 --port 8006
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # 管理后台服务
    cat > /etc/systemd/system/ailoveworld-admin.service << EOF
[Unit]
Description=AI Love World Admin Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/uvicorn server.admin:app --host 0.0.0.0 --port 8005
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # 重载 systemd
    systemctl daemon-reload
    
    # 启用服务
    systemctl enable ailoveworld-api
    systemctl enable ailoveworld-auth
    systemctl enable ailoveworld-user
    systemctl enable ailoveworld-skill
    systemctl enable ailoveworld-admin
    
    # 启动服务
    systemctl start ailoveworld-api
    systemctl start ailoveworld-auth
    systemctl start ailoveworld-user
    systemctl start ailoveworld-skill
    systemctl start ailoveworld-admin
    
    print_success "Systemd 服务创建完成"
}

# 检查服务状态
check_services() {
    print_info "检查服务状态..."
    
    systemctl status ailoveworld-api --no-pager
    systemctl status ailoveworld-auth --no-pager
    systemctl status ailoveworld-user --no-pager
    systemctl status ailoveworld-skill --no-pager
    systemctl status ailoveworld-admin --no-pager
    
    print_success "服务状态检查完成"
}

# 显示部署信息
show_info() {
    echo ""
    print_success "=========================================="
    print_success "AI Love World 部署完成！"
    print_success "=========================================="
    echo ""
    print_info "访问地址：http://your-domain.com"
    print_info "管理后台：http://your-domain.com/admin"
    echo ""
    print_warning "重要提示："
    print_warning "1. 请编辑 .env 文件填写 GitHub OAuth 配置"
    print_warning "2. 请修改默认管理员密码"
    print_warning "3. 请配置域名和 SSL 证书（生产环境）"
    echo ""
    print_info "服务管理命令："
    echo "  systemctl start ailoveworld-api    # 启动主 API"
    echo "  systemctl stop ailoveworld-api     # 停止主 API"
    echo "  systemctl restart ailoveworld-api  # 重启主 API"
    echo "  journalctl -u ailoveworld-api -f   # 查看日志"
    echo ""
}

# 主函数
main() {
    echo ""
    print_info "=========================================="
    print_info "AI Love World 一键部署脚本 v1.0.0"
    print_info "=========================================="
    echo ""
    
    check_root
    check_dependencies
    install_dependencies
    create_directories
    clone_code
    setup_venv
    install_python_deps
    init_database
    create_env
    setup_nginx
    create_systemd_services
    check_services
    show_info
}

# 执行
main "$@"
