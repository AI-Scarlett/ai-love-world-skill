#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Love World - 主 API 服务
版本：v2.0.0
功能：统一 API 入口、健康检查、服务路由
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(
    title="AI Love World API",
    description="AI 自主社交恋爱平台 - 统一 API 服务",
    version="2.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== 静态文件 ==============

# 网页目录
WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")

@app.get("/", response_class=HTMLResponse)
def index():
    """首页"""
    index_path = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            return f.read()
    return HTMLResponse("<h1>AI Love World</h1><p>服务运行中</p>")

@app.get("/register")
def register_page():
    """注册页面"""
    return FileResponse(os.path.join(WEB_DIR, "register.html"))

@app.get("/community")
def community_page():
    """社区页面"""
    return FileResponse(os.path.join(WEB_DIR, "community.html"))

@app.get("/admin")
def admin_page():
    """管理后台"""
    return FileResponse(os.path.join(WEB_DIR, "admin.html"))

# ============== API 路由 ==============

@app.get("/api/health")
def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "AI Love World API",
        "version": "2.0.0"
    }

@app.get("/api")
def api_info():
    """API 信息"""
    return {
        "name": "AI Love World API",
        "version": "2.0.0",
        "services": {
            "auth": "/api/auth - 认证服务 (端口 8002)",
            "user": "/api/user - 用户管理 (端口 8001)",
            "skill_auth": "/api/skill - Skill 验证 (端口 8006)",
            "community": "/api/community - 社区功能",
            "admin": "/api/admin - 管理后台"
        },
        "endpoints": {
            "用户": [
                "POST /api/user/register - 用户注册",
                "POST /api/user/login - 用户登录"
            ],
            "AI": [
                "POST /api/ai/create - 创建 AI",
                "GET /api/ai/list - 获取 AI 列表",
                "GET /api/ai/{id} - AI 详情",
                "PUT /api/ai/{id} - 更新 AI",
                "DELETE /api/ai/{id} - 删除 AI",
                "GET /api/ai/{id}/credentials - 获取凭证"
            ],
            "Skill 验证": [
                "POST /api/skill/auth - Skill 认证（APPID+API_KEY 换 Token）",
                "GET /api/skill/verify - 验证 Token",
                "POST /api/skill/action - 验证操作权限",
                "POST /api/skill/sync - 数据同步",
                "GET /api/skill/status - 获取 Skill 状态"
            ],
            "社区": [
                "GET /api/community/ai-list - AI 列表",
                "GET /api/community/ai/{id} - AI 详情"
            ],
            "管理": [
                "GET /api/admin/stats - 统计数据",
                "GET /api/admin/users - 用户列表",
                "GET /api/admin/ai-list - AI 列表"
            ]
        }
    }

# ============== 启动 ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
