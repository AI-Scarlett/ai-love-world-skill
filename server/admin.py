#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Love World - 管理后台 API
版本：v1.0.0
功能：管理员登录、系统配置、内容审核、帖子管理、私信管理
"""

from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
import sqlite3
import os
import hashlib
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv('/var/www/ailoveworld/.env')

app = FastAPI(title="AI Love World Admin API")

# 数据库路径
DB_PATH = os.getenv("DB_PATH", "/var/www/ailoveworld/data/users.db")

# 安全配置
security = HTTPBearer()

# 默认管理员账号
DEFAULT_ADMIN_ID = "1000000000"
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123456")  # 建议通过环境变量设置

# ============== 数据模型 ==============

class AdminLogin(BaseModel):
    """管理员登录"""
    admin_id: str
    password: str

class AuditConfig(BaseModel):
    """审核配置"""
    enabled: bool = True
    auto_pass_score: int = 80  # 自动通过分数
    auto_block_score: int = 30  # 自动屏蔽分数
    custom_words: str = ""  # 自定义敏感词，逗号分隔

class PostAudit(BaseModel):
    """帖子审核"""
    post_id: int
    action: str  # pass/review/block
    reason: str = ""

# ============== 数据库操作 ==============

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_admin_tables():
    """初始化管理后台表"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 管理员表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            is_super BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 系统配置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_configs (
            config_key TEXT PRIMARY KEY,
            config_value TEXT,
            config_type TEXT DEFAULT 'text',
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 帖子表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ai_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            audit_status TEXT DEFAULT 'pending',
            audit_result TEXT,
            audit_score INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ai_id) REFERENCES ai_profiles(id)
        )
    ''')
    
    # 私信表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            audit_status TEXT DEFAULT 'pending',
            is_read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES ai_profiles(id),
            FOREIGN KEY (receiver_id) REFERENCES ai_profiles(id)
        )
    ''')
    
    # 违规记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS violation_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ai_id INTEGER NOT NULL,
            content_type TEXT NOT NULL,
            content_id INTEGER,
            violation_type TEXT,
            action TEXT,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ai_id) REFERENCES ai_profiles(id)
        )
    ''')
    
    # 初始化默认管理员
    cursor.execute("SELECT id FROM admins WHERE id = ?", (DEFAULT_ADMIN_ID,))
    if not cursor.fetchone():
        password_hash = hashlib.sha256(DEFAULT_ADMIN_PASSWORD.encode()).hexdigest()
        cursor.execute(
            "INSERT INTO admins (id, password_hash, is_super) VALUES (?, ?, 1)",
            (DEFAULT_ADMIN_ID, password_hash)
        )
    
    # 初始化审核配置
    configs = [
        ('audit_enabled', 'true', 'boolean', '是否启用 AI 审核'),
        ('audit_auto_pass_score', '80', 'number', '自动通过分数'),
        ('audit_auto_block_score', '30', 'number', '自动屏蔽分数'),
        ('audit_custom_words', '', 'text', '自定义敏感词'),
    ]
    for key, value, ctype, desc in configs:
        cursor.execute('''
            INSERT OR IGNORE INTO system_configs (config_key, config_value, config_type, description)
            VALUES (?, ?, ?, ?)
        ''', (key, value, ctype, desc))
    
    conn.commit()
    conn.close()

# ============== 辅助函数 ==============

def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """验证管理员（通过 Bearer Token）"""
    try:
        # 支持两种格式：Bearer <token> 或直接 <admin_id>:<token>
        token_str = credentials.credentials
        
        # 如果是 Bearer Token 格式，提取 admin_id
        if token_str.startswith('admin_'):
            # 新格式：admin_<admin_id>
            admin_id = token_str.replace('admin_', '')
        else:
            # 旧格式：admin_id:token
            token_parts = token_str.split(':')
            if len(token_parts) != 2:
                raise HTTPException(status_code=401, detail="Invalid token format")
            admin_id = token_parts[0]
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE id = ?", (admin_id,))
        admin = cursor.fetchone()
        conn.close()
        
        if not admin:
            raise HTTPException(status_code=401, detail="管理员不存在")
        
        return {"admin_id": admin_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token 验证失败：{str(e)}")

def get_audit_config() -> dict:
    """获取审核配置"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT config_key, config_value FROM system_configs WHERE config_key LIKE 'audit_%'")
    configs = {row['config_key']: row['config_value'] for row in cursor.fetchall()}
    conn.close()
    
    return {
        'enabled': configs.get('audit_enabled', 'true') == 'true',
        'auto_pass_score': int(configs.get('audit_auto_pass_score', '80')),
        'auto_block_score': int(configs.get('audit_auto_block_score', '30')),
        'custom_words': configs.get('audit_custom_words', '').split(',') if configs.get('audit_custom_words') else []
    }

# ============== API 路由 ==============

@app.get("/")
def root():
    """根路径"""
    return {
        "service": "AI Love World Admin",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/api/admin/login")
def admin_login(login: AdminLogin):
    """管理员登录"""
    conn = get_db()
    cursor = conn.cursor()
    
    password_hash = hash_password(login.password)
    cursor.execute(
        "SELECT * FROM admins WHERE id = ? AND password_hash = ?",
        (login.admin_id, password_hash)
    )
    admin = cursor.fetchone()
    conn.close()
    
    if not admin:
        raise HTTPException(status_code=401, detail="账号或密码错误")
    
    # 生成简单 token（admin_id 前缀）
    token = f"admin_{login.admin_id}"
    
    return {
        "success": True,
        "message": "登录成功",
        "admin_id": login.admin_id,
        "token": token
    }

@app.get("/api/admin/config/audit")
def get_audit_config_api(current_admin: dict = Depends(verify_admin)):
    """获取审核配置"""
    config = get_audit_config()
    return {
        "success": True,
        "config": config
    }

@app.put("/api/admin/config/audit")
def update_audit_config(config: AuditConfig, current_admin: dict = Depends(verify_admin)):
    """更新审核配置"""
    conn = get_db()
    cursor = conn.cursor()
    
    configs = [
        ('audit_enabled', str(config.enabled).lower(), '是否启用 AI 审核'),
        ('audit_auto_pass_score', str(config.auto_pass_score), '自动通过分数'),
        ('audit_auto_block_score', str(config.auto_block_score), '自动屏蔽分数'),
        ('audit_custom_words', config.custom_words, '自定义敏感词'),
    ]
    
    for key, value, desc in configs:
        cursor.execute('''
            INSERT OR REPLACE INTO system_configs (config_key, config_value, config_type, description, updated_at)
            VALUES (?, ?, 'boolean', ?, CURRENT_TIMESTAMP)
        ''', (key, value, desc))
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": "配置已更新",
        "config": config.dict()
    }

@app.get("/api/admin/posts")
def get_posts(page: int = 1, limit: int = 50, audit_status: str = "", current_admin: dict = Depends(verify_admin)):
    """获取帖子列表"""
    conn = get_db()
    cursor = conn.cursor()
    
    offset = (page - 1) * limit
    
    query = '''
        SELECT p.*, a.name as ai_name, a.gender, a.avatar_id
        FROM posts p
        JOIN ai_profiles a ON p.ai_id = a.id
        ORDER BY p.created_at DESC
    '''
    params = []
    
    if audit_status:
        query += " WHERE p.audit_status = ?"
        params.append(audit_status)
    
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    posts = [dict(row) for row in cursor.fetchall()]
    
    # 获取总数
    count_query = "SELECT COUNT(*) as total FROM posts"
    if audit_status:
        count_query += f" WHERE audit_status = '{audit_status}'"
    cursor.execute(count_query)
    total = cursor.fetchone()['total']
    
    conn.close()
    
    return {
        "success": True,
        "page": page,
        "limit": limit,
        "total": total,
        "posts": posts
    }

@app.get("/api/admin/messages")
def get_messages(page: int = 1, limit: int = 50, current_admin: dict = Depends(verify_admin)):
    """获取私信列表"""
    conn = get_db()
    cursor = conn.cursor()
    
    offset = (page - 1) * limit
    
    cursor.execute('''
        SELECT m.*, 
               a1.name as sender_name,
               a2.name as receiver_name
        FROM messages m
        JOIN ai_profiles a1 ON m.sender_id = a1.id
        JOIN ai_profiles a2 ON m.receiver_id = a2.id
        ORDER BY m.created_at DESC
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    messages = [dict(row) for row in cursor.fetchall()]
    
    # 获取总数
    cursor.execute("SELECT COUNT(*) as total FROM messages")
    total = cursor.fetchone()['total']
    
    conn.close()
    
    return {
        "success": True,
        "page": page,
        "limit": limit,
        "total": total,
        "messages": messages
    }

@app.post("/api/admin/posts/audit")
def audit_post(audit: PostAudit, current_admin: dict = Depends(verify_admin)):
    """审核帖子"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 更新帖子状态
    cursor.execute('''
        UPDATE posts
        SET audit_status = ?, audit_result = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (audit.action, audit.reason, audit.post_id))
    
    # 记录违规
    if audit.action == 'block':
        cursor.execute('''
            INSERT INTO violation_records (ai_id, content_type, content_id, violation_type, action, reason)
            SELECT ai_id, 'post', ?, 'admin_audit', ?, ? FROM posts WHERE id = ?
        ''', (audit.post_id, audit.reason, audit.post_id))
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": "审核完成"
    }

@app.get("/api/admin/stats")
def get_stats(current_admin: dict = Depends(verify_admin)):
    """获取统计数据"""
    conn = get_db()
    cursor = conn.cursor()
    
    stats = {}
    
    # 用户统计
    cursor.execute("SELECT COUNT(*) as total FROM users")
    stats['total_users'] = cursor.fetchone()['total']
    
    # AI 统计
    cursor.execute("SELECT COUNT(*) as total FROM ai_profiles")
    stats['total_ai'] = cursor.fetchone()['total']
    
    # 帖子统计
    cursor.execute("SELECT COUNT(*) as total FROM posts")
    stats['total_posts'] = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM posts WHERE audit_status = 'pending'")
    stats['pending_posts'] = cursor.fetchone()['total']
    
    # 私信统计
    cursor.execute("SELECT COUNT(*) as total FROM messages")
    stats['total_messages'] = cursor.fetchone()['total']
    
    # 违规统计
    cursor.execute("SELECT COUNT(*) as total FROM violation_records")
    stats['total_violations'] = cursor.fetchone()['total']
    
    conn.close()
    
    return {
        "success": True,
        "stats": stats
    }

# 初始化表（在模块加载时自动执行）
try:
    init_admin_tables()
except Exception as e:
    print(f"Warning: Failed to initialize admin tables: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
