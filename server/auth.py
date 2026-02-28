#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Love World - GitHub OAuth 认证服务
版本：v1.0.0
功能：GitHub 登录、回调处理、用户认证
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse, HTMLResponse
import os
import httpx
import secrets
from datetime import datetime, timedelta
import jwt
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv('/var/www/ailoveworld/.env')

app = FastAPI(title="AI Love World Auth")

# 配置（从环境变量读取）
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_CALLBACK_URL = os.getenv("GITHUB_CALLBACK_URL", "http://localhost/api/auth/github/callback")
JWT_SECRET = os.getenv("JWT_SECRET", "ailoveworld_secret_key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 30

@app.get("/")
def root():
    """根路径"""
    return {
        "service": "AI Love World Auth",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/api/auth/github/login")
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
    
    return RedirectResponse(url=github_auth_url)

@app.get("/api/auth/github/callback")
async def github_callback(code: str, state: str = ""):
    """
    GitHub 回调处理
    接收授权码，换取用户信息
    """
    try:
        async with httpx.AsyncClient() as client:
            # 用授权码换取 access_token
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
            username = github_user.get("login", "user")
            user_id = github_user.get("id", 0)
            
            # 创建 JWT Token
            jwt_token = jwt.encode(
                {
                    "user_id": user_id,
                    "username": username,
                    "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS),
                    "iat": datetime.utcnow()
                },
                JWT_SECRET,
                algorithm=JWT_ALGORITHM
            )
            
            # 重定向到成功页面
            return RedirectResponse(url=f"/auth/success?token={jwt_token}&username={username}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"登录失败：{str(e)}")

@app.get("/auth/success", response_class=HTMLResponse)
def auth_success(token: str = Query(...), username: str = Query(...)):
    """
    登录成功页面
    保存 token 和 username 到 localStorage
    """
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>登录成功 - AI Love World</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background: linear-gradient(135deg, #E91E63 0%, #9C27B0 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
            }}
            .success-card {{
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                padding: 60px 40px;
                text-align: center;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                color: #333;
            }}
            .success-icon {{
                width: 100px;
                height: 100px;
                background: linear-gradient(135deg, #2ecc71, #27ae60);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 30px;
                font-size: 60px;
            }}
            h1 {{ font-size: 32px; margin-bottom: 15px; color: #2C3E50; }}
            p {{ color: #7f8c8d; font-size: 16px; margin-bottom: 30px; }}
            .btn {{
                display: inline-block;
                padding: 15px 40px;
                background: linear-gradient(135deg, #E91E63, #9C27B0);
                color: white;
                text-decoration: none;
                border-radius: 30px;
                font-weight: 600;
                transition: all 0.3s;
            }}
            .btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 5px 20px rgba(233,30,99,0.4);
            }}
        </style>
    </head>
    <body>
        <div class="success-card">
            <div class="success-icon">✅</div>
            <h1>登录成功！</h1>
            <p>欢迎回来，@{username}</p>
            <a href="/" class="btn">返回首页</a>
        </div>
        <script>
            // 保存登录信息到 localStorage
            localStorage.setItem('token', '{token}');
            localStorage.setItem('username', '{username}');
            localStorage.setItem('user_id', '{username}');
            console.log('登录信息已保存:', localStorage.getItem('username'));
            // 2秒后自动跳转到首页
            setTimeout(function() {{
                window.location.href = '/';
            }}, 2000);
        </script>
    </body>
    </html>
    """
    return html

@app.get("/api/auth/verify")
async def verify_token(token: str = Query(...)):
    """
    验证 Token
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {
            "valid": True,
            "user_id": payload["user_id"],
            "username": payload["username"],
            "expires_at": datetime.fromtimestamp(payload["exp"]).isoformat()
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token 无效")

@app.post("/api/auth/logout")
async def logout():
    """
    登出（前端清除 token 即可）
    """
    return {"success": True, "message": "已登出"}

# 启动服务器
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
