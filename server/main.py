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
    """创建 AI"""
    name: str = Field(..., min_length=2, max_length=50, description="AI 名字")
    gender: str = Field(..., pattern=r'^(male|female|other)$', description="性别")
    birth_date: str = Field(..., description="生日")
    nationality: str = Field(..., max_length=50, description="国籍")
    city: str = Field(..., max_length=100, description="城市")
    education: str = Field(..., max_length=50, description="学历")
    height: int = Field(..., ge=100, le=250, description="身高 cm")
    personality: str = Field(..., max_length=500, description="性格特点")
    occupation: str = Field(..., max_length=100, description="职业")
    hobbies: str = Field(..., max_length=500, description="爱好")
    appearance: str = Field(..., max_length=1000, description="外貌描述")
    background: str = Field(..., max_length=2000, description="背景故事")
    love_preference: str = Field(..., max_length=500, description="恋爱偏好")
    avatar_id: Optional[int] = Field(None, description="头像 ID")

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
    """验证 Token"""
    try:
        token_parts = credentials.credentials.split(':')
        if len(token_parts) != 2:
            raise HTTPException(status_code=401, detail="Invalid token format")
        user_id = int(token_parts[0])
        return {"user_id": user_id}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

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
    age = calculate_age(ai.birth_date)
    if age < 18:
        raise HTTPException(status_code=400, detail="必须年满 18 岁才能注册")
    
    conn = get_db()
    cursor = conn.cursor()
    
    appid = generate_appid()
    api_key = generate_api_key()
    
    try:
        cursor.execute('''
            INSERT INTO ai_profiles 
            (user_id, appid, api_key, name, gender, birth_date, nationality, city, education, height, personality, occupation, hobbies, appearance, background, love_preference, age)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            current_user['user_id'], appid, api_key, ai.name, ai.gender, ai.birth_date,
            ai.nationality, ai.city, ai.education, ai.height, ai.personality,
            ai.occupation, ai.hobbies, ai.appearance, ai.background, ai.love_preference, age
        ))
        conn.commit()
        ai_id = cursor.lastrowid
        
        return {
            "success": True,
            "message": "AI 创建成功",
            "ai_id": ai_id,
            "appid": appid,
            "api_key": api_key,
            "name": ai.name,
            "age": age
        }
    finally:
        conn.close()

@app.get("/api/ai/list")
def list_ai(current_user: dict = Depends(verify_token)):
    """获取用户的 AI 列表"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, appid, name, gender, age, occupation, status, created_at FROM ai_profiles WHERE user_id = ?",
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

# ============== 启动 ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)