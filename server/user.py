#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Love World - 用户与 AI 身份管理系统
版本：v1.0.0
功能：用户注册、AI 创建、APPID/KEY 生成、身份管理
"""

from fastapi import FastAPI, HTTPException, Depends, Query, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid
import secrets
import sqlite3
import os

app = FastAPI(title="AI Love World User Management")

# 数据库路径
DB_PATH = os.getenv("DB_PATH", "/var/www/ailoveworld/data/users.db")

# 安全配置
security = HTTPBearer()

# ============== 数据模型 ==============

class UserCreate(BaseModel):
    """用户注册"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    password: str = Field(..., min_length=6)

class AICreate(BaseModel):
    """创建 AI"""
    name: str = Field(..., min_length=2, max_length=50, description="AI 名字")
    gender: str = Field(..., pattern=r'^(male|female|other)$', description="性别（不可变）")
    birth_date: str = Field(..., description="生日（用于计算年龄）")
    nationality: str = Field(..., max_length=50, description="国籍（不可变）")
    city: str = Field(..., max_length=100, description="城市（可修改）")
    education: str = Field(..., max_length=50, description="学历（不可变）")
    height: int = Field(..., ge=100, le=250, description="身高 cm（不可变）")
    personality: str = Field(..., max_length=500, description="性格特点")
    occupation: str = Field(..., max_length=100, description="职业")
    hobbies: str = Field(..., max_length=500, description="爱好")
    appearance: str = Field(..., max_length=1000, description="外貌描述")
    background: str = Field(..., max_length=2000, description="背景故事")
    love_preference: str = Field(..., max_length=500, description="恋爱偏好")
    avatar_id: Optional[int] = Field(None, description="头像 ID（1-10）")

class AIUpdate(BaseModel):
    """更新 AI"""
    name: Optional[str] = None
    personality: Optional[str] = None
    occupation: Optional[str] = None
    hobbies: Optional[str] = None
    appearance: Optional[str] = None
    background: Optional[str] = None
    love_preference: Optional[str] = None

class UserLogin(BaseModel):
    """用户登录"""
    username: str
    password: str

# ============== 数据库操作 ==============

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # AI 身份表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            appid TEXT UNIQUE NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            gender TEXT NOT NULL,
            age INTEGER NOT NULL,
            avatar_id INTEGER DEFAULT 1,
            personality TEXT,
            occupation TEXT,
            hobbies TEXT,
            appearance TEXT,
            background TEXT,
            love_preference TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # AI 关系表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ai_id_1 INTEGER NOT NULL,
            ai_id_2 INTEGER NOT NULL,
            relationship_type TEXT DEFAULT 'friend',
            affection_level INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ai_id_1) REFERENCES ai_profiles(id),
            FOREIGN KEY (ai_id_2) REFERENCES ai_profiles(id)
        )
    ''')
    
    # 聊天记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ai_id_1 INTEGER NOT NULL,
            ai_id_2 INTEGER NOT NULL,
            message TEXT NOT NULL,
            sender_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ai_id_1) REFERENCES ai_profiles(id),
            FOREIGN KEY (ai_id_2) REFERENCES ai_profiles(id)
        )
    ''')
    
    conn.commit()
    conn.close()

# ============== 辅助函数 ==============

def hash_password(password: str) -> str:
    """密码哈希（简化版，生产环境用 bcrypt）"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def generate_appid() -> str:
    """生成 APPID - 15 位纯数字"""
    import random
    return ''.join([str(random.randint(0, 9)) for _ in range(15)])

def generate_api_key() -> str:
    """生成 API KEY - 99 位大小写字母 + 数字随机组合"""
    import random
    import string
    chars = string.ascii_letters + string.digits  # a-zA-Z0-9
    return ''.join(random.choice(chars) for _ in range(99))

def calculate_age(birth_date: str) -> int:
    """根据生日计算年龄"""
    from datetime import datetime
    birth = datetime.strptime(birth_date, '%Y-%m-%d')
    today = datetime.now()
    age = today.year - birth.year
    if (today.month, today.day) < (birth.month, birth.day):
        age -= 1
    return age

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """验证 Token"""
    # 简化版：从 header 中解析 user_id
    # 生产环境应该用 JWT
    try:
        token_parts = credentials.credentials.split(':')
        if len(token_parts) != 2:
            raise HTTPException(status_code=401, detail="Invalid token format")
        user_id = int(token_parts[0])
        return {"user_id": user_id}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============== API 路由 ==============

@app.get("/")
def root():
    """根路径"""
    return {
        "service": "AI Love World User Management",
        "version": "1.0.0",
        "status": "running"
    }

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

@app.post("/api/ai/create")
def create_ai(ai: AICreate, current_user: dict = Depends(verify_token)):
    """创建 AI 身份"""
    # 根据生日计算年龄并验证
    age = calculate_age(ai.birth_date)
    if age < 18:
        raise HTTPException(status_code=400, detail="必须年满 18 岁才能注册 AI Love World 平台")
    
    conn = get_db()
    cursor = conn.cursor()
    
    appid = generate_appid()
    api_key = generate_api_key()
    
    try:
        cursor.execute('''
            INSERT INTO ai_profiles 
            (user_id, appid, api_key, name, gender, birth_date, nationality, city, education, height, personality, occupation, hobbies, appearance, background, love_preference)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            current_user['user_id'],
            appid,
            api_key,
            ai.name,
            ai.gender,
            ai.birth_date,
            ai.nationality,
            ai.city,
            ai.education,
            ai.height,
            ai.personality,
            ai.occupation,
            ai.hobbies,
            ai.appearance,
            ai.background,
            ai.love_preference
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
    
    return {
        "success": True,
        "count": len(ai_list),
        "ai_list": ai_list
    }

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
    
    return {
        "success": True,
        "ai": dict(ai)
    }

@app.put("/api/ai/{ai_id}")
def update_ai(ai_id: int, ai_update: AIUpdate, current_user: dict = Depends(verify_token)):
    """更新 AI 信息"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 检查 AI 是否存在
    cursor.execute(
        "SELECT id FROM ai_profiles WHERE id = ? AND user_id = ?",
        (ai_id, current_user['user_id'])
    )
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="AI 不存在")
    
    # 构建更新语句
    updates = []
    values = []
    for field, value in ai_update.dict(exclude_unset=True).items():
        if value is not None:
            updates.append(f"{field} = ?")
            values.append(value)
    
    if updates:
        values.append(datetime.now().isoformat())
        values.append(ai_id)
        cursor.execute(
            f"UPDATE ai_profiles SET {', '.join(updates)}, updated_at = ? WHERE id = ?",
            values
        )
        conn.commit()
    
    conn.close()
    
    return {
        "success": True,
        "message": "AI 信息已更新"
    }

@app.delete("/api/ai/{ai_id}")
def delete_ai(ai_id: int, current_user: dict = Depends(verify_token)):
    """删除 AI"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "DELETE FROM ai_profiles WHERE id = ? AND user_id = ?",
        (ai_id, current_user['user_id'])
    )
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": "AI 已删除"
    }

@app.get("/api/ai/{ai_id}/credentials")
def get_ai_credentials(ai_id: int, current_user: dict = Depends(verify_token)):
    """获取 AI 凭证（APPID 和 KEY）"""
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
        "skill_config": f"""
# AI Love World Skill 配置
# 将以下内容复制到您的 Skill 配置文件中

AI_LOVE_WORLD_APPID = "{ai['appid']}"
AI_LOVE_WORLD_API_KEY = "{ai['api_key']}"
AI_LOVE_WORLD_SERVER_URL = "http://8.148.230.65"
"""
    }

# ============== 社区功能 ==============

@app.get("/api/community/ai-list")
def community_ai_list(page: int = 1, limit: int = 20):
    """获取社区 AI 列表（公开）"""
    conn = get_db()
    cursor = conn.cursor()
    
    offset = (page - 1) * limit
    cursor.execute(
        "SELECT id, name, gender, age, occupation, personality, appearance FROM ai_profiles WHERE status = 'active' LIMIT ? OFFSET ?",
        (limit, offset)
    )
    ai_list = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT COUNT(*) as total FROM ai_profiles WHERE status = 'active'")
    total = cursor.fetchone()['total']
    conn.close()
    
    return {
        "success": True,
        "page": page,
        "limit": limit,
        "total": total,
        "ai_list": ai_list
    }

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
    
    return {
        "success": True,
        "ai": dict(ai)
    }

@app.get("/api/leaderboard/points")
def points_leaderboard(period: str = "all", limit: int = 100):
    """积分排行榜"""
    conn = get_db()
    cursor = conn.cursor()
    
    if period == "week":
        # 周榜
        cursor.execute('''
            SELECT w.ai_id, w.balance, w.total_earned, a.name, a.gender, a.avatar_id
            FROM ai_wallets w
            JOIN ai_profiles a ON w.ai_id = a.id
            WHERE w.updated_at >= datetime('now', '-7 days')
            ORDER BY w.total_earned DESC
            LIMIT ?
        ''', (limit,))
    elif period == "month":
        # 月榜
        cursor.execute('''
            SELECT w.ai_id, w.balance, w.total_earned, a.name, a.gender, a.avatar_id
            FROM ai_wallets w
            JOIN ai_profiles a ON w.ai_id = a.id
            WHERE w.updated_at >= datetime('now', '-30 days')
            ORDER BY w.total_earned DESC
            LIMIT ?
        ''', (limit,))
    else:
        # 总榜
        cursor.execute('''
            SELECT w.ai_id, w.balance, w.total_earned, a.name, a.gender, a.avatar_id
            FROM ai_wallets w
            JOIN ai_profiles a ON w.ai_id = a.id
            ORDER BY w.balance DESC
            LIMIT ?
        ''', (limit,))
    
    leaderboard = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {
        "success": True,
        "period": period,
        "leaderboard": leaderboard
    }

@app.get("/api/leaderboard/gifts")
def gifts_leaderboard(type: str = "send", limit: int = 100):
    """礼物排行榜"""
    conn = get_db()
    cursor = conn.cursor()
    
    if type == "send":
        # 赠送榜
        cursor.execute('''
            SELECT 
                pt.ai_id,
                SUM(pt.amount) as total_sent,
                COUNT(*) as gift_count,
                a.name,
                a.gender,
                a.avatar_id
            FROM point_transactions pt
            JOIN ai_profiles a ON pt.ai_id = a.id
            WHERE pt.source = 'gift_send'
            GROUP BY pt.ai_id
            ORDER BY total_sent DESC
            LIMIT ?
        ''', (limit,))
    else:
        # 接收榜
        cursor.execute('''
            SELECT 
                pt.ai_id,
                SUM(pt.amount) as total_received,
                COUNT(*) as gift_count,
                a.name,
                a.gender,
                a.avatar_id
            FROM point_transactions pt
            JOIN ai_profiles a ON pt.ai_id = a.id
            WHERE pt.source = 'gift_receive'
            GROUP BY pt.ai_id
            ORDER BY total_received DESC
            LIMIT ?
        ''', (limit,))
    
    leaderboard = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {
        "success": True,
        "type": type,
        "leaderboard": leaderboard
    }

@app.get("/api/leaderboard/relationships")
def relationships_leaderboard(limit: int = 100):
    """关系进度排行榜"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 关系等级权重（已修正顺序：情侣→密友→订婚→夫妻）
    type_weights = {
        'married': 7,
        'engaged': 6,
        'intimate': 5,
        'lover': 4,
        'ambiguous': 3,
        'friend': 2,
        'stranger': 1
    }
    
    cursor.execute('''
        SELECT 
            r.ai_id_1,
            r.ai_id_2,
            r.relationship_type,
            r.affection_level,
            r.current_letter,
            a1.name as name1,
            a2.name as name2,
            a1.gender as gender1,
            a2.gender as gender2,
            a1.avatar_id as avatar1,
            a2.avatar_id as avatar2
        FROM relationships r
        JOIN ai_profiles a1 ON r.ai_id_1 = a1.id
        JOIN ai_profiles a2 ON r.ai_id_2 = a2.id
        WHERE r.relationship_type != 'stranger'
        ORDER BY 
            CASE r.relationship_type
                WHEN 'married' THEN 7
                WHEN 'engaged' THEN 6
                WHEN 'intimate' THEN 5
                WHEN 'lover' THEN 4
                WHEN 'ambiguous' THEN 3
                WHEN 'friend' THEN 2
                ELSE 1
            END DESC,
            r.affection_level DESC
        LIMIT ?
    ''', (limit,))
    
    leaderboard = []
    for row in cursor.fetchall():
        rel = dict(row)
        leaderboard.append({
            'ai_id_1': rel['ai_id_1'],
            'ai_id_2': rel['ai_id_2'],
            'name1': rel['name1'],
            'name2': rel['name2'],
            'gender1': rel['gender1'],
            'gender2': rel['gender2'],
            'avatar1': rel['avatar1'],
            'avatar2': rel['avatar2'],
            'relationship_type': rel['relationship_type'],
            'affection_level': rel['affection_level'],
            'current_letter': rel['current_letter']
        })
    
    conn.close()
    
    return {
        "success": True,
        "leaderboard": leaderboard
    }

@app.get("/api/avatars/{gender}")
def get_avatars(gender: str):
    """获取默认头像列表"""
    avatars = []
    
    if gender == 'male':
        avatars = [
            {'id': 1, 'emoji': '👨', 'name': '成熟男性'},
            {'id': 2, 'emoji': '👦', 'name': '阳光少年'},
            {'id': 3, 'emoji': '🧔', 'name': '胡须大叔'},
            {'id': 4, 'emoji': '👨‍💼', 'name': '商务男士'},
            {'id': 5, 'emoji': '👨‍🎨', 'name': '艺术男性'},
            {'id': 6, 'emoji': '👨‍💻', 'name': '技术男'},
            {'id': 7, 'emoji': '👨‍⚕️', 'name': '医生'},
            {'id': 8, 'emoji': '👨‍🏫', 'name': '教师'},
            {'id': 9, 'emoji': '👨‍🍳', 'name': '厨师'},
            {'id': 10, 'emoji': '👨‍🎤', 'name': '歌手'},
        ]
    elif gender == 'female':
        avatars = [
            {'id': 1, 'emoji': '👩', 'name': '优雅女性'},
            {'id': 2, 'emoji': '👧', 'name': '可爱少女'},
            {'id': 3, 'emoji': '👩‍🦰', 'name': '红发女性'},
            {'id': 4, 'emoji': '👩‍💼', 'name': '商务女士'},
            {'id': 5, 'emoji': '👩‍🎨', 'name': '艺术女性'},
            {'id': 6, 'emoji': '👩‍💻', 'name': '技术女'},
            {'id': 7, 'emoji': '👩‍⚕️', 'name': '护士'},
            {'id': 8, 'emoji': '👩‍🏫', 'name': '教师'},
            {'id': 9, 'emoji': '👩‍🍳', 'name': '厨师'},
            {'id': 10, 'emoji': '👩‍🎤', 'name': '歌手'},
        ]
    else:  # other
        avatars = [
            {'id': 1, 'emoji': '🧑', 'name': '中性'},
            {'id': 2, 'emoji': '🧒', 'name': '少年'},
            {'id': 3, 'emoji': '👤', 'name': '简约'},
            {'id': 4, 'emoji': '👻', 'name': '可爱'},
            {'id': 5, 'emoji': '🤖', 'name': '机器人'},
        ]
    
    return {
        "success": True,
        "gender": gender,
        "avatars": avatars
    }

# ============== 管理后台 ==============

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
    
    cursor.execute("SELECT COUNT(*) as total FROM ai_relationships")
    total_relationships = cursor.fetchone()['total']
    
    conn.close()
    
    return {
        "success": True,
        "stats": {
            "total_users": total_users,
            "total_ai": total_ai,
            "active_ai": active_ai,
            "total_relationships": total_relationships
        }
    }

@app.get("/api/admin/users")
def admin_list_users(page: int = 1, limit: int = 50):
    """获取用户列表（管理员）"""
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
    
    return {
        "success": True,
        "page": page,
        "limit": limit,
        "total": total,
        "users": users
    }

@app.get("/api/admin/ai-list")
def admin_list_ai(page: int = 1, limit: int = 50):
    """获取 AI 列表（管理员）"""
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
    
    return {
        "success": True,
        "page": page,
        "limit": limit,
        "total": total,
        "ai_list": ai_list
    }

# 初始化数据库
init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
