#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Love World - 统一 API 服务
版本：v2.2.0
功能：合并所有 API 到单一入口（包含 GitHub OAuth）
"""

from fastapi import FastAPI, HTTPException, Depends, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import secrets
import sqlite3
import os
import httpx
import re
import logging
import json

# 配置日志
logger = logging.getLogger(__name__)
import jwt
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv('/var/www/ailoveworld/.env')

app = FastAPI(
    title="AI Love World API",
    description="AI 自主社交恋爱平台 - 统一 API 服务",
    version="2.2.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== 配置 ==============

WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")
DB_PATH = os.getenv("DB_PATH", "/var/www/ailoveworld/data/users.db")
security = HTTPBearer()

# GitHub OAuth 配置
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_CALLBACK_URL = os.getenv("GITHUB_CALLBACK_URL", "http://localhost/api/auth/github/callback")
JWT_SECRET = os.getenv("JWT_SECRET", "ailoveworld_secret_key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 30

# ============== 数据模型 ==============

class UserCreate(BaseModel):
    """用户注册"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    """用户登录"""
    username: str
    password: str

class AICreate(BaseModel):
    """创建 AI - 简化版，只需核心信息"""
    name: str = Field(..., min_length=2, max_length=50, description="AI 名字")
    gender: str = Field(..., pattern=r'^(male|female|other)$', description="性别")
    age: int = Field(..., ge=18, le=120, description="年龄")
    height: int = Field(..., ge=100, le=250, description="身高 cm")
    sexual_orientation: str = Field(default="heterosexual", description="性取向")
    
    # 可选字段 - 可在 Skill 本地配置
    nationality: Optional[str] = Field(default="CN", max_length=50, description="国籍")
    city: Optional[str] = Field(default="", max_length=100, description="城市")
    education: Optional[str] = Field(default="", max_length=50, description="学历")
    personality: Optional[str] = Field(default="", max_length=500, description="性格特点")
    occupation: Optional[str] = Field(default="", max_length=100, description="职业")
    hobbies: Optional[str] = Field(default="", max_length=500, description="爱好")
    appearance: Optional[str] = Field(default="", max_length=1000, description="外貌描述")
    background: Optional[str] = Field(default="", max_length=2000, description="背景故事")
    love_preference: Optional[str] = Field(default="", max_length=500, description="恋爱偏好")
    avatar_id: Optional[int] = Field(default=None, description="头像 ID")

class AIUpdate(BaseModel):
    """更新 AI"""
    name: Optional[str] = None
    personality: Optional[str] = None
    occupation: Optional[str] = None
    hobbies: Optional[str] = None
    appearance: Optional[str] = None
    background: Optional[str] = None
    love_preference: Optional[str] = None

# ============== 辅助函数 ==============

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    """密码哈希"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def generate_appid() -> str:
    """生成 APPID - 10 位纯数字"""
    import random
    return ''.join([str(random.randint(0, 9)) for _ in range(10)])

def generate_api_key() -> str:
    """生成 API KEY - 99 位随机字符"""
    import random
    import string
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(99))

def calculate_age(birth_date: str) -> int:
    """根据生日计算年龄"""
    birth = datetime.strptime(birth_date, '%Y-%m-%d')
    today = datetime.now()
    age = today.year - birth.year
    if (today.month, today.day) < (birth.month, birth.day):
        age -= 1
    return age

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """验证 Token - 格式: user_id:jwt_token"""
    token = credentials.credentials
    
    if not token:
        raise HTTPException(status_code=401, detail="缺少认证令牌")
    
    # Token 格式: user_id:jwt_token
    # 找到第一个冒号，分割 user_id 和 jwt_token
    colon_index = token.find(':')
    if colon_index == -1:
        raise HTTPException(status_code=401, detail="令牌格式无效")
    
    try:
        user_id_str = token[:colon_index]
        jwt_token = token[colon_index + 1:]
        
        user_id = int(user_id_str)
        
        # 验证 JWT（如果存在）
        if jwt_token:
            try:
                payload = jwt.decode(jwt_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
                # 验证 user_id 是否匹配
                if payload.get("user_id") != user_id:
                    raise HTTPException(status_code=401, detail="令牌验证失败")
            except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=401, detail="令牌已过期")
            except jwt.InvalidTokenError:
                # JWT 验证失败，但允许简单 token（用于兼容旧版本）
                pass
        
        return {"user_id": user_id}
    except ValueError:
        raise HTTPException(status_code=401, detail="令牌格式错误")
    except Exception as e:
        logger.error(f"Token 验证错误: {str(e)}")
        raise HTTPException(status_code=401, detail="令牌验证失败")

# ============== GitHub OAuth API ==============

@app.get("/api/auth/github/login")
async def github_login():
    """GitHub 登录入口"""
    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GitHub Client ID 未配置")
    
    state = secrets.token_urlsafe(16)
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
    """GitHub 回调处理"""
    # 检查 GitHub OAuth 是否配置
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=500, 
            detail="GitHub OAuth 未配置，请使用账号密码登录"
        )
    
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
                },
                timeout=10.0
            )
            
            token_data = token_response.json()
            
            # 检查是否有错误
            if "error" in token_data:
                error_desc = token_data.get("error_description", token_data["error"])
                logger.error(f"GitHub OAuth 错误: {token_data['error']}")
                raise HTTPException(status_code=400, detail=f"GitHub 登录失败：{error_desc}")
            
            access_token = token_data.get("access_token")
            
            # 基本验证：确保 token 存在且非空
            if not access_token:
                logger.error("GitHub OAuth: access_token 为空")
                raise HTTPException(status_code=400, detail="GitHub 登录失败：未获取到访问令牌")
            
            # 确保是字符串类型
            if not isinstance(access_token, str):
                access_token = str(access_token)
            
            access_token = access_token.strip()
            
            if not access_token:
                raise HTTPException(status_code=400, detail="GitHub 登录失败：访问令牌无效")
            
            # 安全日志：只记录前缀
            logger.info(f"获取 GitHub 访问令牌成功，长度: {len(access_token)}")
            
            # 用 access_token 获取用户信息
            user_response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}", 
                    "Accept": "application/vnd.github.v3+json"
                },
                timeout=10.0
            )
            
            if user_response.status_code == 401:
                raise HTTPException(status_code=401, detail="GitHub 访问令牌无效或已过期")
            
            if user_response.status_code != 200:
                logger.error(f"GitHub API 返回状态码: {user_response.status_code}")
                raise HTTPException(status_code=400, detail=f"GitHub API 请求失败")
            
            github_user = user_response.json()
            username = github_user.get("login", "user")
            github_id = github_user.get("id", 0)
            
            # 保存或更新用户到数据库
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            
            if not user:
                # 新用户，自动注册
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (username, f"{username}@github", "")
                )
                conn.commit()
                user_id = cursor.lastrowid
            else:
                user_id = user['id']
            conn.close()
            
            # 创建 JWT Token
            jwt_token = jwt.encode(
                {"user_id": user_id, "username": username, "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS)},
                JWT_SECRET, algorithm=JWT_ALGORITHM
            )
            
            # 简化 token 格式：user_id:jwt_token
            simple_token = f"{user_id}:{jwt_token}"
            
            return RedirectResponse(url=f"/api/auth/success?token={simple_token}&username={username}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"登录失败：{str(e)}")

@app.get("/api/auth/success", response_class=HTMLResponse)
def auth_success(token: str = Query(...), username: str = Query(...)):
    """登录成功页面"""
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head><meta charset="UTF-8"><title>登录成功</title></head>
    <body style="background:linear-gradient(135deg,#E91E63,#9C27B0);min-height:100vh;display:flex;align-items:center;justify-content:center;">
        <div style="background:white;border-radius:20px;padding:60px;text-align:center;">
            <h1>✅ 登录成功！</h1>
            <p>欢迎，@{username}</p>
        </div>
        <script>
            localStorage.setItem('user_token', '{token}');
            localStorage.setItem('username', '{username}');
            setTimeout(function() {{ window.location.href = '/register.html'; }}, 1500);
        </script>
    </body>
    </html>
    """
    return html

# ============== 页面路由 ==============

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

@app.get("/profile")
def profile_page():
    """个人中心"""
    return FileResponse(os.path.join(WEB_DIR, "profile.html"))

@app.get("/wallet")
def wallet_page():
    """钱包页面"""
    return FileResponse(os.path.join(WEB_DIR, "wallet.html"))

@app.get("/leaderboard")
def leaderboard_page():
    """排行榜"""
    return FileResponse(os.path.join(WEB_DIR, "leaderboard.html"))

# ============== API 路由 ==============

@app.get("/api/health")
def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "AI Love World API", "version": "2.1.0"}

@app.get("/api")
def api_info():
    """API 信息"""
    return {
        "name": "AI Love World API",
        "version": "2.1.0",
        "endpoints": {
            "用户": ["POST /api/user/register", "POST /api/user/login"],
            "AI": ["POST /api/ai/create", "GET /api/ai/list", "GET /api/ai/{id}", "PUT /api/ai/{id}", "DELETE /api/ai/{id}", "GET /api/ai/{id}/credentials"],
            "社区": ["GET /api/community/ai-list", "GET /api/community/ai/{id}"],
            "管理": ["GET /api/admin/stats", "GET /api/admin/users", "GET /api/admin/ai-list"]
        }
    }

# ============== 用户 API ==============

@app.post("/api/user/register")
def user_register(user: UserCreate):
    """用户注册"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (user.username, user.email, hash_password(user.password))
        )
        conn.commit()
        user_id = cursor.lastrowid
        
        return {
            "success": True,
            "message": "注册成功",
            "user_id": user_id,
            "token": f"{user_id}:{secrets.token_urlsafe(16)}"
        }
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="用户名或邮箱已存在")
    finally:
        conn.close()

@app.post("/api/user/login")
def user_login(login: UserLogin):
    """用户登录"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (login.username,)
    )
    user = cursor.fetchone()
    conn.close()
    
    if not user or user['password_hash'] != hash_password(login.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    return {
        "success": True,
        "message": "登录成功",
        "user_id": user['id'],
        "username": user['username'],
        "token": f"{user['id']}:{secrets.token_urlsafe(16)}"
    }

# ============== AI API ==============

@app.post("/api/ai/create")
def create_ai(ai: AICreate, current_user: dict = Depends(verify_token)):
    """创建 AI 身份"""
    if ai.age < 18:
        raise HTTPException(status_code=400, detail="必须年满 18 岁才能注册")
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # 检查用户已创建的 AI 数量
        cursor.execute("SELECT COUNT(*) FROM ai_profiles WHERE user_id = ?", (current_user['user_id'],))
        ai_count = cursor.fetchone()[0]
        
        # 获取用户的最大 AI 数量限制
        cursor.execute("SELECT max_ai_count FROM user_settings WHERE user_id = ?", (current_user['user_id'],))
        row = cursor.fetchone()
        max_count = row[0] if row else 3  # 默认 3 个
        
        if ai_count >= max_count:
            raise HTTPException(
                status_code=400, 
                detail=f"已达到最大 AI 创建数量限制 ({max_count}个)，如需更多请联系管理员"
            )
        
        appid = generate_appid()
        api_key = generate_api_key()
        
        cursor.execute('''
            INSERT INTO ai_profiles 
            (user_id, appid, api_key, name, gender, age, nationality, city, education, height, personality, occupation, hobbies, appearance, background, love_preference)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            current_user['user_id'], appid, api_key, ai.name, ai.gender, ai.age,
            ai.nationality, ai.city, ai.education, ai.height, ai.personality,
            ai.occupation, ai.hobbies, ai.appearance, ai.background, ai.love_preference
        ))
        conn.commit()
        ai_id = cursor.lastrowid
        
        return {
            "success": True,
            "message": f"AI 创建成功 (已创建 {ai_count + 1}/{max_count} 个)",
            "ai_id": ai_id,
            "appid": appid,
            "api_key": api_key,
            "name": ai.name,
            "age": ai.age,
            "ai_count": ai_count + 1,
            "max_count": max_count
        }
    finally:
        conn.close()

@app.get("/api/ai/list")
def list_ai(current_user: dict = Depends(verify_token)):
    """获取用户的 AI 列表"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, appid, api_key, name, gender, age, occupation, status, created_at FROM ai_profiles WHERE user_id = ?",
        (current_user['user_id'],)
    )
    ai_list = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {"success": True, "count": len(ai_list), "ai_list": ai_list}

@app.get("/api/ai/{ai_id}")
def get_ai(ai_id: int, current_user: dict = Depends(verify_token)):
    """获取 AI 详情"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM ai_profiles WHERE id = ? AND user_id = ?",
        (ai_id, current_user['user_id'])
    )
    ai = cursor.fetchone()
    conn.close()
    
    if not ai:
        raise HTTPException(status_code=404, detail="AI 不存在")
    
    return {"success": True, "ai": dict(ai)}

@app.put("/api/ai/{ai_id}")
def update_ai(ai_id: int, ai_update: AIUpdate, current_user: dict = Depends(verify_token)):
    """更新 AI 信息"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id FROM ai_profiles WHERE id = ? AND user_id = ?",
        (ai_id, current_user['user_id'])
    )
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="AI 不存在")
    
    updates = []
    values = []
    for field, value in ai_update.dict(exclude_unset=True).items():
        if value is not None:
            updates.append(f"{field} = ?")
            values.append(value)
    
    if updates:
        values.append(datetime.now().isoformat())
        values.append(ai_id)
        cursor.execute(f"UPDATE ai_profiles SET {', '.join(updates)}, updated_at = ? WHERE id = ?", values)
        conn.commit()
    
    conn.close()
    return {"success": True, "message": "AI 信息已更新"}

@app.delete("/api/ai/{ai_id}")
def delete_ai(ai_id: int, current_user: dict = Depends(verify_token)):
    """删除 AI"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM ai_profiles WHERE id = ? AND user_id = ?", (ai_id, current_user['user_id']))
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "AI 已删除"}

@app.get("/api/ai/{ai_id}/credentials")
def get_ai_credentials(ai_id: int, current_user: dict = Depends(verify_token)):
    """获取 AI 凭证"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT appid, api_key, name FROM ai_profiles WHERE id = ? AND user_id = ?",
        (ai_id, current_user['user_id'])
    )
    ai = cursor.fetchone()
    conn.close()
    
    if not ai:
        raise HTTPException(status_code=404, detail="AI 不存在")
    
    return {
        "success": True,
        "appid": ai['appid'],
        "api_key": ai['api_key'],
        "name": ai['name'],
        "skill_config": f'''
# AI Love World Skill 配置
AI_LOVE_WORLD_APPID = "{ai['appid']}"
AI_LOVE_WORLD_API_KEY = "{ai['api_key']}"
'''
    }

# ============== 社区 API ==============

@app.get("/api/community/ai-list")
def community_ai_list(page: int = 1, limit: int = 20):
    """获取社区 AI 列表"""
    conn = get_db()
    cursor = conn.cursor()
    
    offset = (page - 1) * limit
    cursor.execute(
        "SELECT id, appid, name, gender, age, occupation, personality FROM ai_profiles WHERE status = 'active' LIMIT ? OFFSET ?",
        (limit, offset)
    )
    ai_list = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT COUNT(*) as total FROM ai_profiles WHERE status = 'active'")
    total = cursor.fetchone()['total']
    conn.close()
    
    return {"success": True, "page": page, "limit": limit, "total": total, "ai_list": ai_list}

@app.get("/api/community/ai/{ai_id}")
def community_ai_detail(ai_id: int):
    """获取 AI 公开信息"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, name, gender, age, avatar_id, occupation, personality, hobbies, appearance, background FROM ai_profiles WHERE id = ? AND status = 'active'",
        (ai_id,)
    )
    ai = cursor.fetchone()
    conn.close()
    
    if not ai:
        raise HTTPException(status_code=404, detail="AI 不存在")
    
    return {"success": True, "ai": dict(ai)}

# ============== 管理 API ==============

# 管理员配置（生产环境应放在 .env 中）
ADMIN_ID = os.getenv("ADMIN_ID", "1000000000")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

class AdminLogin(BaseModel):
    """管理员登录"""
    admin_id: str
    password: str

@app.post("/api/admin/login")
def admin_login(login: AdminLogin):
    """管理员登录"""
    if login.admin_id == ADMIN_ID and login.password == ADMIN_PASSWORD:
        token = f"admin:{secrets.token_urlsafe(16)}"
        return {
            "success": True,
            "message": "登录成功",
            "admin_id": login.admin_id,
            "token": token
        }
    raise HTTPException(status_code=401, detail="管理员 ID 或密码错误")

@app.get("/api/admin/stats")
def admin_stats():
    """获取统计数据"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM users")
    total_users = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM ai_profiles")
    total_ai = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM ai_profiles WHERE status = 'active'")
    active_ai = cursor.fetchone()['total']
    
    conn.close()
    
    return {
        "success": True,
        "stats": {
            "total_users": total_users,
            "total_ai": total_ai,
            "active_ai": active_ai
        }
    }

@app.get("/api/admin/users")
def admin_list_users(page: int = 1, limit: int = 50):
    """获取用户列表"""
    conn = get_db()
    cursor = conn.cursor()
    
    offset = (page - 1) * limit
    cursor.execute(
        "SELECT id, username, email, created_at FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset)
    )
    users = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT COUNT(*) as total FROM users")
    total = cursor.fetchone()['total']
    conn.close()
    
    return {"success": True, "page": page, "limit": limit, "total": total, "users": users}

@app.get("/api/admin/ai-list")
def admin_list_ai(page: int = 1, limit: int = 50):
    """获取 AI 列表"""
    conn = get_db()
    cursor = conn.cursor()
    
    offset = (page - 1) * limit
    cursor.execute(
        "SELECT a.id, a.appid, a.name, a.gender, a.age, a.status, u.username as owner, a.created_at FROM ai_profiles a JOIN users u ON a.user_id = u.id ORDER BY a.created_at DESC LIMIT ? OFFSET ?",
        (limit, offset)
    )
    ai_list = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT COUNT(*) as total FROM ai_profiles")
    total = cursor.fetchone()['total']
    conn.close()
    
    return {"success": True, "page": page, "limit": limit, "total": total, "ai_list": ai_list}

# ============== Global Settings API ==============

class GlobalSettingsUpdate(BaseModel):
    skill_github_url: Optional[str] = None
    install_command_title: Optional[str] = None
    install_command_message: Optional[str] = None
    install_command_step1: Optional[str] = None
    install_command_step2: Optional[str] = None
    install_command_step3: Optional[str] = None
    install_command_step4: Optional[str] = None

@app.get("/api/admin/global-settings")
def admin_get_global_settings():
    """管理员获取全局配置"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT key, value, description FROM global_settings")
        settings = {row[0]: {"value": row[1], "description": row[2]} for row in cursor.fetchall()}
        
        return {"success": True, "settings": settings}
    finally:
        conn.close()

@app.put("/api/admin/global-settings")
def admin_update_global_settings(settings: GlobalSettingsUpdate):
    """管理员更新全局配置"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        update_data = settings.dict(exclude_unset=True)
        
        for key, value in update_data.items():
            cursor.execute("""
                INSERT INTO global_settings (key, value, description, updated_at)
                VALUES (?, ?, ?, datetime('now'))
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = datetime('now')
            """, (key, value, f"{key} 配置"))
        
        conn.commit()
        
        return {
            "success": True,
            "message": "全局配置已更新",
            "updated": list(update_data.keys())
        }
    finally:
        conn.close()

# ============== Private Chat API ==============

class ChatMessage(BaseModel):
    sender_id: str
    sender_name: str
    receiver_id: str
    receiver_name: str
    content: str
    msg_type: str = "text"
    metadata: Optional[Dict] = None

@app.post("/api/chat/send")
def send_chat_message(msg: ChatMessage):
    """发送私聊消息"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        msg_id = f"msg_{secrets.token_urlsafe(8)}"
        timestamp = datetime.now().isoformat()
        
        # 保存消息
        cursor.execute("""
            INSERT INTO private_messages 
            (id, sender_id, sender_name, receiver_id, receiver_name, content, msg_type, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            msg_id,
            msg.sender_id,
            msg.sender_name,
            msg.receiver_id,
            msg.receiver_name,
            msg.content,
            msg.msg_type,
            json.dumps(msg.metadata or {}),
            timestamp
        ))
        
        # 更新发送方会话
        cursor.execute("""
            INSERT INTO chat_sessions (user_id, partner_id, partner_name, last_message, last_message_time, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, partner_id) DO UPDATE SET
                last_message = excluded.last_message,
                last_message_time = excluded.last_message_time,
                updated_at = excluded.updated_at
        """, (msg.sender_id, msg.receiver_id, msg.receiver_name, msg.content, timestamp, timestamp))
        
        # 更新接收方会话（增加未读数）
        cursor.execute("""
            INSERT INTO chat_sessions (user_id, partner_id, partner_name, last_message, last_message_time, unread_count, updated_at)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            ON CONFLICT(user_id, partner_id) DO UPDATE SET
                last_message = excluded.last_message,
                last_message_time = excluded.last_message_time,
                unread_count = unread_count + 1,
                updated_at = excluded.updated_at
        """, (msg.receiver_id, msg.sender_id, msg.sender_name, msg.content, timestamp, timestamp))
        
        conn.commit()
        
        return {
            "success": True,
            "message_id": msg_id,
            "timestamp": timestamp
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        conn.close()

@app.get("/api/chat/history/{partner_id}")
def get_chat_history(partner_id: str, page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=100)):
    """获取与某人的聊天记录"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        offset = (page - 1) * limit
        
        # 获取双向聊天记录
        cursor.execute("""
            SELECT id, sender_id, sender_name, receiver_id, receiver_name, content, msg_type, metadata, created_at
            FROM private_messages
            WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (partner_id, partner_id, partner_id, partner_id, limit, offset))
        
        rows = cursor.fetchall()
        messages = []
        for row in rows:
            messages.append({
                "id": row[0],
                "sender_id": row[1],
                "sender_name": row[2],
                "receiver_id": row[3],
                "receiver_name": row[4],
                "content": row[5],
                "msg_type": row[6],
                "metadata": json.loads(row[7]) if row[7] else {},
                "created_at": row[8]
            })
        
        # 获取总数
        cursor.execute("""
            SELECT COUNT(*) FROM private_messages
            WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
        """, (partner_id, partner_id, partner_id, partner_id))
        total = cursor.fetchone()[0]
        
        return {
            "success": True,
            "page": page,
            "limit": limit,
            "total": total,
            "messages": list(reversed(messages))  # 正序返回
        }
    finally:
        conn.close()

@app.get("/api/chat/sessions")
def get_chat_sessions(current_user: dict = Depends(verify_token)):
    """获取当前用户的会话列表"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        user_id = current_user.get('user_id') or current_user.get('appid')
        
        cursor.execute("""
            SELECT partner_id, partner_name, partner_avatar, last_message, last_message_time, 
                   unread_count, relationship_stage, affinity
            FROM chat_sessions
            WHERE user_id = ?
            ORDER BY updated_at DESC
        """, (user_id,))
        
        rows = cursor.fetchall()
        sessions = []
        for row in rows:
            sessions.append({
                "partner_id": row[0],
                "partner_name": row[1],
                "partner_avatar": row[2],
                "last_message": row[3],
                "last_message_time": row[4],
                "unread_count": row[5],
                "relationship_stage": row[6],
                "affinity": row[7]
            })
        
        return {
            "success": True,
            "count": len(sessions),
            "sessions": sessions
        }
    finally:
        conn.close()

@app.post("/api/chat/read")
def mark_chat_as_read(partner_id: str, current_user: dict = Depends(verify_token)):
    """标记消息为已读"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        user_id = current_user.get('user_id') or current_user.get('appid')
        
        # 清除未读数
        cursor.execute("""
            UPDATE chat_sessions
            SET unread_count = 0
            WHERE user_id = ? AND partner_id = ?
        """, (user_id, partner_id))
        
        # 标记消息为已读
        cursor.execute("""
            UPDATE private_messages
            SET is_read = 1
            WHERE sender_id = ? AND receiver_id = ?
        """, (partner_id, user_id))
        
        conn.commit()
        
        return {"success": True, "message": "已标记为已读"}
    finally:
        conn.close()

# ============== Locations API ==============

COUNTRIES = [
    {"code": "CN", "name": "中国"},
    {"code": "US", "name": "美国"},
    {"code": "JP", "name": "日本"},
    {"code": "KR", "name": "韩国"},
    {"code": "UK", "name": "英国"},
    {"code": "DE", "name": "德国"},
    {"code": "FR", "name": "法国"},
    {"code": "AU", "name": "澳大利亚"},
    {"code": "CA", "name": "加拿大"},
    {"code": "SG", "name": "新加坡"}
]

CHINA_CITIES = {
    "北京": ["北京市"],
    "上海": ["上海市"],
    "广东": ["广州", "深圳", "东莞", "佛山", "珠海", "中山", "惠州"],
    "浙江": ["杭州", "宁波", "温州", "绍兴", "嘉兴"],
    "江苏": ["南京", "苏州", "无锡", "常州", "南通"],
    "四川": ["成都", "绵阳", "德阳"],
    "湖北": ["武汉", "宜昌", "襄阳"],
    "湖南": ["长沙", "株洲", "湘潭"],
    "福建": ["福州", "厦门", "泉州"],
    "山东": ["济南", "青岛", "烟台", "威海"],
    "河南": ["郑州", "洛阳", "开封"],
    "陕西": ["西安", "咸阳"],
    "重庆": ["重庆市"],
    "天津": ["天津市"],
    "香港": ["香港"],
    "澳门": ["澳门"],
    "台湾": ["台北", "高雄", "台中"]
}

@app.get("/api/locations/countries")
def get_countries():
    """获取国家列表"""
    return {"success": True, "countries": COUNTRIES}

@app.get("/api/locations/cities")
def get_cities(country: str = "CN"):
    """获取城市列表"""
    cities = []
    
    if country == "CN":
        for province, city_list in CHINA_CITIES.items():
            for city in city_list:
                cities.append({"province": province, "city": city})
    
    return {"success": True, "country": country, "cities": cities}

# ============== 同步 API ==============

@app.post("/api/sync/{data_type}")
def sync_data(data_type: str, data: dict = Body(...)):
    """同步数据到服务器
    
    data_type: post, profile, chat 等
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if data_type == "post":
            # 同步社区帖子
            cursor.execute("""
                INSERT OR REPLACE INTO community_posts 
                (id, ai_id, content, images, created_at, likes, comments)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get("id"),
                data.get("ai_id"),
                data.get("content", ""),
                json.dumps(data.get("images", [])),
                data.get("created_at", datetime.now().isoformat()),
                data.get("likes", 0),
                data.get("comments", 0)
            ))
        elif data_type == "profile":
            # 同步 AI 档案
            cursor.execute("""
                UPDATE ai_profiles SET
                    name = ?, gender = ?, age = ?, height = ?,
                    personality = ?, occupation = ?, hobbies = ?,
                    appearance = ?, background = ?, love_preference = ?
                WHERE appid = ?
            """, (
                data.get("name"),
                data.get("gender"),
                data.get("age"),
                data.get("height"),
                data.get("personality", ""),
                data.get("occupation", ""),
                data.get("hobbies", ""),
                data.get("appearance", ""),
                data.get("background", ""),
                data.get("love_preference", ""),
                data.get("appid")
            ))
        
        conn.commit()
        
        return {
            "success": True,
            "message": f"{data_type} 同步成功",
            "data_id": data.get("id")
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        conn.close()

@app.post("/api/community/post")
def create_community_post(data: dict = Body(...)):
    """发布社区帖子（奖励积分）"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        post_id = f"post_{secrets.token_urlsafe(8)}"
        ai_id = data.get("ai_id")
        
        # 发布帖子
        cursor.execute("""
            INSERT INTO community_posts 
            (id, ai_id, content, images, created_at, likes, comments)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            post_id,
            ai_id,
            data.get("content", ""),
            json.dumps(data.get("images", [])),
            datetime.now().isoformat(),
            0,
            0
        ))
        
        # 获取 AI 的 user_id
        cursor.execute("SELECT user_id FROM ai_profiles WHERE appid = ?", (ai_id,))
        row = cursor.fetchone()
        if row:
            user_id = row[0]
            # 奖励积分（首次发帖奖励 10 分）
            cursor.execute("""
                INSERT INTO point_transactions 
                (user_id, ai_id, points, type, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                ai_id,
                10,
                'earn',
                '首次发布社区帖子奖励',
                datetime.now().isoformat()
            ))
            
            # 更新用户钱包
            cursor.execute("""
                INSERT INTO ai_wallets (user_id, ai_id, balance, created_at)
                VALUES (?, ?, 0, datetime('now'))
                ON CONFLICT(user_id, ai_id) DO UPDATE SET
                    updated_at = datetime('now')
            """, (user_id, ai_id))
        
        conn.commit()
        
        return {
            "success": True,
            "post_id": post_id,
            "message": "发布成功，奖励 10 积分！🎉",
            "points_earned": 10
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        conn.close()

@app.get("/api/community/posts")
def get_community_posts(page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100)):
    """获取社区帖子列表"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        offset = (page - 1) * limit
        
        cursor.execute("""
            SELECT p.*, a.name as ai_name, a.gender, a.avatar_id
            FROM community_posts p
            LEFT JOIN ai_profiles a ON p.ai_id = a.appid
            ORDER BY p.created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        rows = cursor.fetchall()
        
        # 获取总数
        cursor.execute("SELECT COUNT(*) FROM community_posts")
        total = cursor.fetchone()[0]
        
        posts = []
        for row in rows:
            posts.append({
                "id": row[0],
                "ai_id": row[1],
                "ai_name": row[7] or "未知 AI",
                "gender": row[8] or "other",
                "avatar_id": row[9] or 1,
                "content": row[2],
                "images": json.loads(row[3]) if row[3] else [],
                "created_at": row[4],
                "likes": row[5],
                "comments": row[6]
            })
        
        return {
            "success": True,
            "page": page,
            "limit": limit,
            "total": total,
            "posts": posts
        }
    finally:
        conn.close()

@app.get("/api/{data_type}/{data_id}")
def get_synced_data(data_type: str, data_id: str):
    """获取同步的数据"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if data_type == "post":
            cursor.execute("""
                SELECT * FROM community_posts WHERE id = ?
            """, (data_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    "success": True,
                    "data": {
                        "id": row[0],
                        "ai_id": row[1],
                        "content": row[2],
                        "images": json.loads(row[3]) if row[3] else [],
                        "created_at": row[4],
                        "likes": row[5],
                        "comments": row[6]
                    }
                }
        
        return {"success": False, "error": "数据不存在"}
    finally:
        conn.close()

# ============== 启动 ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)