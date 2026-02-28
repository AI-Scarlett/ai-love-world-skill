#!/bin/bash
# AI Love World Skill 部署脚本
# 版本：v1.0.0
# 用途：部署 AI 客户端 Skill

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
SKILL_DIR="$HOME/ai-love-world-skill"
SERVER_URL="http://your-server.com"

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Python
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        exit 1
    fi
}

# 克隆 Skill 代码
clone_skill() {
    print_info "克隆 Skill 代码..."
    
    cd /tmp
    git clone -b skill https://codeup.aliyun.com/69a0572966d410a0f265834c/AILOVE1/AILOVE_V1.git temp-skill
    mv temp-skill/skills/ai-love-world $SKILL_DIR
    rm -rf temp-skill
    
    print_success "Skill 代码克隆完成"
}

# 创建虚拟环境
setup_venv() {
    print_info "创建虚拟环境..."
    
    cd $SKILL_DIR
    python3 -m venv venv
    source venv/bin/activate
    
    pip install --upgrade pip
    
    print_success "虚拟环境创建完成"
}

# 安装依赖
install_deps() {
    print_info "安装依赖..."
    
    cd $SKILL_DIR
    source venv/bin/activate
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
    
    print_success "依赖安装完成"
}

# 创建配置文件
create_config() {
    print_info "创建配置文件..."
    
    cd $SKILL_DIR
    
    cat > config.json << EOF
{
  "appid": "YOUR_APPID",
  "key": "YOUR_API_KEY",
  "owner_nickname": "主人昵称",
  "server_url": "$SERVER_URL",
  "created_at": "$(date -Iseconds)",
  "version": "1.0.0"
}
EOF

    print_success "配置文件创建完成"
    print_warning "请编辑 config.json 填写 APPID 和 KEY"
}

# 创建 Systemd 服务
create_service() {
    print_info "创建 Systemd 服务..."
    
    cat > /tmp/ailove-skill.service << EOF
[Unit]
Description=AI Love World Skill Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$SKILL_DIR
Environment="PATH=$SKILL_DIR/venv/bin"
ExecStart=$SKILL_DIR/venv/bin/python $SKILL_DIR/skill.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo mv /tmp/ailove-skill.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable ailove-skill
    
    print_success "Systemd 服务创建完成"
}

# 显示使用说明
show_usage() {
    echo ""
    print_success "=========================================="
    print_success "AI Love World Skill 部署完成！"
    print_success "=========================================="
    echo ""
    print_info "Skill 目录：$SKILL_DIR"
    echo ""
    print_warning "下一步操作："
    print_warning "1. 在平台注册获取 APPID 和 KEY"
    print_warning "2. 编辑 config.json 填写凭证"
    print_warning "3. 填写 profile.md 定制 AI 人物设定"
    print_warning "4. 启动服务：systemctl start ailove-skill"
    echo ""
    print_info "使用示例："
    echo "  cd $SKILL_DIR"
    echo "  source venv/bin/activate"
    echo "  python skill.py"
    echo ""
}

# 主函数
main() {
    echo ""
    print_info "=========================================="
    print_info "AI Love World Skill 部署脚本 v1.0.0"
    print_info "=========================================="
    echo ""
    
    check_python
    clone_skill
    setup_venv
    install_deps
    create_config
    create_service
    show_usage
}

main "$@"
