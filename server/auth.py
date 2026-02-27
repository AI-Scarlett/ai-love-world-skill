#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Love World - 用户认证模块
版本：v1.0.0
功能：GitHub OAuth 登录、JWT Token 管理
"""

from fastapi import FastAPI, HTTPException, Depends, Request, Query
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
import os
import jwt
import secrets
from datetime import datetime, timedelta
from pathlib import Path
import json

# 认证应用
auth_app = FastAPI(title="AI Love World Auth")

# 配置（从环境变量读取）
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_CALLBACK_URL = os.getenv("GITHUB_CALLBACK_URL", "http://localhost:8000/api/auth/github/callback")
JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 30

# 用户数据存储
USERS_DB_PATH = Path(__file__).parent / "auth_data" / "users.json"
USERS_DB_PATH.parent.mkdir(exist_ok=True)

def load_users():
    """加载用户数据"""
    if USERS_DB_PATH.exists():
        with open(USERS_DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users: dict):
    """保存用户数据"""
    with open(USERS_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def create_jwt_token(user_id: str, username: str) -> str:
    """创建 JWT Token"""
    expire = datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS)
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """验证 JWT Token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@auth_app.get("/")
async def auth_root():
    """认证服务根路径"""
    return {
        "service": "AI Love World Auth",
        "version": "1.0.0",
        "providers": ["github"],
        "status": "running"
    }

@auth_app.get("/api/auth/github/login")
async def github_login():
    """
    GitHub 登录入口
    重定向用户到 GitHub 授权页面
    """
    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GitHub Client ID 未配置")
    
    # 生成 state 参数防止 CSRF
    state = secrets.token_urlsafe(16)
    
    # 构建 GitHub 授权 URL
    github_auth_url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={GITHUB_CLIENT_ID}&"
        f"redirect_uri={GITHUB_CALLBACK_URL}&"
        f"scope=user:email&"
        f"state={state}"
    )
    
    # 重定向到 GitHub
    return RedirectResponse(url=github_auth_url)

@auth_app.get("/api/auth/github/callback")
async def github_callback(code: str, state: str):
    """
    GitHub 回调处理
    接收授权码，换取用户信息
    """
    # 验证 state（简化版，生产环境应存储并验证）
    
    try:
        # 用授权码换取 access_token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": GITHUB_CLIENT_ID,
                    "client_secret": GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": GITHUB_CALLBACK_URL
                }
            )
            
            token_data = token_response.json()
            
            if "error" in token_data:
                raise HTTPException(status_code=400, detail=f"GitHub API 错误：{token_data['error']}")
            
            access_token = token_data.get("access_token")
            
            # 用 access_token 获取用户信息
            user_response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"token {access_token}",
                    "Accept": "application/json"
                }
            )
            
            github_user = user_response.json()
            
            # 获取用户邮箱
            email_response = await client.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"token {access_token}",
                    "Accept": "application/json"
                }
            )
            
            emails = email_response.json()
            primary_email = next(
                (e["email"] for e in emails if e["primary"]),
                github_user.get("email", "")
            )
            
            # 创建或更新用户
            users = load_users()
            github_id = str(github_user["id"])
            
            if github_id not in users:
                # 新用户
                users[github_id] = {
                    "github_id": github_id,
                    "username": github_user["login"],
                    "email": primary_email,
                    "name": github_user.get("name", ""),
                    "avatar_url": github_user.get("avatar_url", ""),
                    "profile_url": github_user.get("html_url", ""),
                    "created_at": datetime.utcnow().isoformat(),
                    "last_login": datetime.utcnow().isoformat(),
                    "role": "user"
                }
                save_users(users)
            else:
                # 更新最后登录时间
                users[github_id]["last_login"] = datetime.utcnow().isoformat()
                save_users(users)
            
            # 创建 JWT Token
            jwt_token = create_jwt_token(github_id, github_user["login"])
            
            # 重定向到前端页面，带上 token
            frontend_url = f"/auth/success?token={jwt_token}&username={github_user['login']}"
            return RedirectResponse(url=frontend_url)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"登录失败：{str(e)}")

@auth_app.get("/api/auth/github/info")
async def github_auth_info():
    """获取 GitHub 登录配置信息"""
    return {
        "enabled": bool(GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET),
        "callback_url": GITHUB_CALLBACK_URL,
        "instructions": {
            "step1": "访问 https://github.com/settings/developers",
            "step2": "点击 'New OAuth App'",
            "step3": "填写 Application name: AI Love World",
            "step4": "填写 Homepage URL: https://ailoveai.love",
            "step5": "填写 Callback URL: " + GITHUB_CALLBACK_URL,
            "step6": "获取 Client ID 和 Client Secret",
            "step7": "设置环境变量：GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET"
        }
    }

@auth_app.post("/api/auth/verify")
async def verify_token(request: Request):
    """验证 Token"""
    try:
        data = await request.json()
        token = data.get("token")
        
        if not token:
            raise HTTPException(status_code=400, detail="Token 缺失")
        
        payload = verify_jwt_token(token)
        
        if not payload:
            raise HTTPException(status_code=401, detail="Token 无效或已过期")
        
        return {
            "valid": True,
            "user_id": payload["user_id"],
            "username": payload["username"],
            "expires_at": datetime.fromtimestamp(payload["exp"]).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证失败：{str(e)}")

@auth_app.get("/api/auth/me")
async def get_current_user(token: str = Query(...)):
    """获取当前用户信息"""
    payload = verify_jwt_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Token 无效")
    
    users = load_users()
    user = users.get(payload["user_id"])
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 不返回敏感信息
    return {
        "id": user["github_id"],
        "username": user["username"],
        "email": user["email"],
        "name": user["name"],
        "avatar_url": user["avatar_url"],
        "profile_url": user["profile_url"],
        "created_at": user["created_at"],
        "last_login": user["last_login"]
    }

@auth_app.post("/api/auth/logout")
async def logout(request: Request):
    """登出（前端清除 token 即可）"""
    return {"success": True, "message": "已登出"}

# 启动服务器
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(auth_app, host="0.0.0.0", port=8002)
