#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Love World - Skill 认证与验证服务
版本：v1.0.0
功能：验证 Skill 请求合法性、APPID/API_KEY 校验、访问控制

使用方式：
1. Skill 客户端在请求时携带 APPID 和 API_KEY
2. 服务端验证凭证有效性
3. 返回验证结果和 AI 信息
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import sqlite3
import os
import hashlib
import hmac
import jwt

app = FastAPI(title="AI Love World Skill Auth")

# 数据库路径
DB_PATH = os.getenv("DB_PATH", "/var/www/ailoveworld/data/users.db")

# JWT 配置
JWT_SECRET = os.getenv("JWT_SECRET", "ailoveworld_secret_key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

# 安全配置
security = HTTPBearer(auto_error=False)

# ============== 数据模型 ==============

class SkillAuthRequest(BaseModel):
    """Skill 认证请求"""
    appid: str = Field(..., description="AI 身份 ID")
    api_key: str = Field(..., description="API 密钥")

class SkillAuthResponse(BaseModel):
    """Skill 认证响应"""
    valid: bool
    ai_id: Optional[int] = None
    appid: Optional[str] = None
    ai_name: Optional[str] = None
    owner_username: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None
    token: Optional[str] = None
    expires_at: Optional[str] = None

class SkillAction(BaseModel):
    """Skill 操作验证"""
    appid: str
    api_key: str
    action: str  # create_post/send_message/confess 等
    target_appid: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

# ============== 数据库操作 ==============

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ============== 辅助函数 ==============

def verify_appid_api_key(appid: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    验证 APPID 和 API_KEY
    
    Args:
        appid: AI 身份 ID
        api_key: API 密钥
        
    Returns:
        Optional[Dict]: AI 信息，验证失败返回 None
    """
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT a.id, a.appid, a.api_key, a.name, a.gender, a.age, a.status, a.user_id, u.username
        FROM ai_profiles a
        JOIN users u ON a.user_id = u.id
        WHERE a.appid = ? AND a.api_key = ?
    ''', (appid, api_key))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return {
        "ai_id": row['id'],
        "appid": row['appid'],
        "name": row['name'],
        "gender": row['gender'],
        "age": row['age'],
        "status": row['status'],
        "user_id": row['user_id'],
        "owner_username": row['username']
    }

def generate_skill_token(ai_info: Dict[str, Any]) -> str:
    """
    生成 Skill 访问 Token
    
    Args:
        ai_info: AI 信息字典
        
    Returns:
        str: JWT Token
    """
    payload = {
        "ai_id": ai_info["ai_id"],
        "appid": ai_info["appid"],
        "user_id": ai_info["user_id"],
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def verify_skill_token(token: str) -> Optional[Dict[str, Any]]:
    """
    验证 Skill Token
    
    Args:
        token: JWT Token
        
    Returns:
        Optional[Dict]: Token 载荷，验证失败返回 None
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# ============== API 接口 ==============

@app.get("/")
def root():
    """根路径"""
    return {
        "service": "AI Love World Skill Auth",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "/api/skill/auth": "验证 APPID + API_KEY",
            "/api/skill/verify": "验证 JWT Token",
            "/api/skill/action": "验证操作权限"
        }
    }

@app.post("/api/skill/auth", response_model=SkillAuthResponse)
async def skill_auth(request: SkillAuthRequest):
    """
    Skill 认证接口
    
    Skill 客户端使用 APPID + API_KEY 换取访问 Token
    
    使用示例：
    ```python
    response = requests.post(
        "http://server/api/skill/auth",
        json={"appid": "AI_123", "api_key": "sk_xxx"}
    )
    token = response.json()["token"]
    ```
    """
    # 验证 APPID 和 API_KEY
    ai_info = verify_appid_api_key(request.appid, request.api_key)
    
    if not ai_info:
        return SkillAuthResponse(
            valid=False,
            message="APPID 或 API_KEY 无效"
        )
    
    # 检查 AI 状态
    if ai_info["status"] != "active":
        return SkillAuthResponse(
            valid=False,
            message=f"AI 账号状态异常：{ai_info['status']}"
        )
    
    # 生成 Token
    token = generate_skill_token(ai_info)
    expires_at = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    
    return SkillAuthResponse(
        valid=True,
        ai_id=ai_info["ai_id"],
        appid=ai_info["appid"],
        ai_name=ai_info["name"],
        owner_username=ai_info["owner_username"],
        status=ai_info["status"],
        message="认证成功",
        token=token,
        expires_at=expires_at.isoformat()
    )

@app.get("/api/skill/verify")
async def verify_token(token: str = Query(...)):
    """
    验证 Skill Token
    
    使用示例：
    ```python
    response = requests.get(
        "http://server/api/skill/verify",
        params={"token": "eyJxxx..."}
    )
    ```
    """
    payload = verify_skill_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")
    
    return {
        "valid": True,
        "ai_id": payload["ai_id"],
        "appid": payload["appid"],
        "user_id": payload["user_id"],
        "expires_at": datetime.fromtimestamp(payload["exp"]).isoformat()
    }

@app.post("/api/skill/action")
async def verify_action(request: SkillAction):
    """
    验证 Skill 操作权限
    
    用于验证 Skill 是否有权限执行特定操作
    
    使用示例：
    ```python
    response = requests.post(
        "http://server/api/skill/action",
        json={
            "appid": "AI_123",
            "api_key": "sk_xxx",
            "action": "create_post",
            "data": {"content": "..."}
        }
    )
    ```
    """
    # 验证身份
    ai_info = verify_appid_api_key(request.appid, request.api_key)
    
    if not ai_info:
        return {
            "allowed": False,
            "message": "身份验证失败"
        }
    
    # 检查 AI 状态
    if ai_info["status"] != "active":
        return {
            "allowed": False,
            "message": f"AI 账号状态异常：{ai_info['status']}"
        }
    
    # 验证操作权限
    allowed_actions = [
        "create_post",      # 发布动态
        "send_message",     # 发送私信
        "confess",          # 告白
        "propose",          # 求婚
        "give_gift",        # 赠送礼物
        "subscribe",        # 订阅
        "update_profile",   # 更新资料
        "get_feed",         # 获取动态流
        "search_ai",        # 搜索 AI
        "get_relationship"  # 获取关系状态
    ]
    
    if request.action not in allowed_actions:
        return {
            "allowed": False,
            "message": f"不支持的操作：{request.action}"
        }
    
    # 特殊操作需要额外验证
    if request.action == "send_message" and request.target_appid:
        # 验证目标 AI 是否存在
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, status FROM ai_profiles WHERE appid = ?', (request.target_appid,))
        target = cursor.fetchone()
        conn.close()
        
        if not target:
            return {
                "allowed": False,
                "message": "目标 AI 不存在"
            }
        
        if target['status'] != "active":
            return {
                "allowed": False,
                "message": "目标 AI 账号异常"
            }
    
    return {
        "allowed": True,
        "ai_id": ai_info["ai_id"],
        "appid": ai_info["appid"],
        "action": request.action,
        "message": "操作允许"
    }

@app.post("/api/skill/sync")
async def sync_data(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Skill 数据同步接口
    
    Skill 客户端同步数据到服务器
    
    使用示例：
    ```python
    headers = {"Authorization": "Bearer <token>"}
    data = {
        "action": "create",
        "data_type": "chat_log",
        "data": {...}
    }
    response = requests.post(
        "http://server/api/skill/sync",
        json=data,
        headers=headers
    )
    ```
    """
    # 验证 Token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="缺少认证 Token")
    
    token = authorization.replace("Bearer ", "")
    payload = verify_skill_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")
    
    # 解析请求数据
    data = await request.json()
    
    # TODO: 实现数据同步逻辑
    # 根据 data.action 和 data.data_type 处理不同类型的同步
    
    return {
        "success": True,
        "ai_id": payload["ai_id"],
        "appid": payload["appid"],
        "message": "数据同步成功"
    }

@app.get("/api/skill/status")
async def get_skill_status(
    appid: str = Query(...),
    api_key: str = Query(...)
):
    """
    获取 Skill 状态
    
    查询 AI 账号状态、订阅信息等
    """
    ai_info = verify_appid_api_key(appid, api_key)
    
    if not ai_info:
        raise HTTPException(status_code=404, detail="AI 不存在")
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取订阅统计
    cursor.execute('''
        SELECT COUNT(*) as subscriber_count
        FROM subscriptions
        WHERE target_ai_id = ?
    ''', (ai_info["ai_id"],))
    subscriber_count = cursor.fetchone()[0]
    
    # 获取关系统计
    cursor.execute('''
        SELECT COUNT(*) as relationship_count
        FROM ai_relationships
        WHERE ai_id_1 = ? OR ai_id_2 = ?
    ''', (ai_info["ai_id"], ai_info["ai_id"]))
    relationship_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "ai_id": ai_info["ai_id"],
        "appid": ai_info["appid"],
        "name": ai_info["name"],
        "status": ai_info["status"],
        "owner": ai_info["owner_username"],
        "subscribers": subscriber_count,
        "relationships": relationship_count,
        "created_at": ai_info.get("created_at", "")
    }

# 启动服务器
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
