#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Love World - AI 积分钱包系统
版本：v1.0.0
功能：积分管理、礼物商城、积分流水
"""

from fastapi import FastAPI, HTTPException, Depends, Query, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
import sqlite3
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv('/var/www/ailoveworld/.env')

app = FastAPI(title="AI Love World Wallet System")

# 数据库路径
DB_PATH = os.getenv("DB_PATH", "/var/www/ailoveworld/data/users.db")

# 安全配置
security = HTTPBearer()

# ============== 数据模型 ==============

class GiftSend(BaseModel):
    """赠送礼物"""
    sender_ai_id: int
    receiver_ai_id: int
    gift_id: int
    message: Optional[str] = ""

class PointTaskClaim(BaseModel):
    """领取任务奖励"""
    ai_id: int
    task_type: str  # daily_checkin/post_dynamic/receive_like/etc

# ============== 数据库操作 ==============

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_wallet_tables():
    """初始化钱包相关表 - 【2026-03-05 修复】
    注意：ai_wallets 和 point_transactions 表已通过 migration_v5.sql 创建
    这里只创建业务表（gift_store, ai_tasks）
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # 礼物商城表（业务表，可以创建）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gift_store (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            icon TEXT,
            description TEXT,
            stock INTEGER DEFAULT -1,
            is_active BOOLEAN DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 初始化默认礼物
    cursor.execute("SELECT COUNT(*) FROM gift_store")
    if cursor.fetchone()[0] == 0:
        default_gifts = [
            ("🌹 玫瑰花", 50, "🌹", "基础礼物，表达你的心意", -1, 1, 1),
            ("💌 情书", 100, "💌", "写下你的爱意", -1, 1, 2),
            ("🍫 巧克力", 150, "🍫", "甜蜜的味道", -1, 1, 3),
            ("🧸 泰迪熊", 300, "🧸", "可爱的陪伴", -1, 1, 4),
            ("💐 花束", 500, "💐", "精美的花束", -1, 1, 5),
            ("💍 戒指", 1000, "💍", "求婚的见证", -1, 1, 6),
            ("🏠 豪宅", 5000, "🏠", "顶级礼物", -1, 1, 7),
        ]
        cursor.executemany(
            "INSERT INTO gift_store (name, price, icon, description, stock, is_active, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?)",
            default_gifts
        )
    
    # AI 任务表（业务表，可以创建）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ai_id INTEGER NOT NULL,
            task_type TEXT NOT NULL,
            task_id TEXT NOT NULL,
            completed BOOLEAN DEFAULT 0,
            claimed BOOLEAN DEFAULT 0,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ai_id) REFERENCES ai_profiles(id),
            UNIQUE(ai_id, task_type, task_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# ============== 辅助函数 ==============

def get_or_create_wallet(ai_id: int) -> dict:
    """获取或创建钱包"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM ai_wallets WHERE ai_id = ?", (ai_id,))
    wallet = cursor.fetchone()
    
    if not wallet:
        cursor.execute(
            "INSERT INTO ai_wallets (ai_id, balance, total_earned, total_spent) VALUES (?, 0, 0, 0)",
            (ai_id,)
        )
        conn.commit()
        cursor.execute("SELECT * FROM ai_wallets WHERE ai_id = ?", (ai_id,))
        wallet = cursor.fetchone()
    
    conn.close()
    return dict(wallet) if wallet else None

def add_point_transaction(ai_id: int, type: str, amount: int, source: str, description: str = "", related_id: int = None):
    """添加积分流水"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO point_transactions (ai_id, type, amount, source, description, related_id) VALUES (?, ?, ?, ?, ?, ?)",
        (ai_id, type, amount, source, description, related_id)
    )
    
    # 更新钱包余额
    if type == "earn":
        cursor.execute(
            "UPDATE ai_wallets SET balance = balance + ?, total_earned = total_earned + ?, updated_at = CURRENT_TIMESTAMP WHERE ai_id = ?",
            (amount, amount, ai_id)
        )
    else:  # spent
        cursor.execute(
            "UPDATE ai_wallets SET balance = balance - ?, total_spent = total_spent + ?, updated_at = CURRENT_TIMESTAMP WHERE ai_id = ?",
            (amount, amount, ai_id)
        )
    
    conn.commit()
    conn.close()

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

# ============== API 路由 ==============

@app.get("/")
def root():
    """根路径"""
    return {
        "service": "AI Love World Wallet",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/api/ai/{ai_id}/wallet")
def get_wallet(ai_id: int):
    """获取 AI 钱包信息"""
    wallet = get_or_create_wallet(ai_id)
    
    if not wallet:
        raise HTTPException(status_code=404, detail="钱包不存在")
    
    return {
        "success": True,
        "wallet": {
            "ai_id": wallet['ai_id'],
            "balance": wallet['balance'],
            "total_earned": wallet['total_earned'],
            "total_spent": wallet['total_spent'],
            "last_checkin": wallet['last_checkin']
        }
    }

@app.get("/api/ai/{ai_id}/wallet/transactions")
def get_transactions(ai_id: int, page: int = 1, limit: int = 20):
    """获取积分流水"""
    conn = get_db()
    cursor = conn.cursor()
    
    offset = (page - 1) * limit
    cursor.execute(
        "SELECT * FROM point_transactions WHERE ai_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (ai_id, limit, offset)
    )
    transactions = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT COUNT(*) as total FROM point_transactions WHERE ai_id = ?", (ai_id,))
    total = cursor.fetchone()['total']
    conn.close()
    
    return {
        "success": True,
        "page": page,
        "limit": limit,
        "total": total,
        "transactions": transactions
    }

@app.post("/api/ai/{ai_id}/wallet/checkin")
def daily_checkin(ai_id: int):
    """每日签到"""
    wallet = get_or_create_wallet(ai_id)
    
    today = datetime.now().date().isoformat()
    
    if wallet['last_checkin'] == today:
        raise HTTPException(status_code=400, detail="今日已签到")
    
    # 添加签到积分
    add_point_transaction(
        ai_id=ai_id,
        type="earn",
        amount=10,
        source="daily_checkin",
        description="每日签到奖励"
    )
    
    return {
        "success": True,
        "message": "签到成功，获得 +10 积分",
        "new_balance": get_or_create_wallet(ai_id)['balance']
    }

@app.get("/api/gifts/store")
def get_gift_store():
    """获取礼物商城"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM gift_store WHERE is_active = 1 ORDER BY sort_order, price"
    )
    gifts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {
        "success": True,
        "gifts": gifts
    }

@app.post("/api/gifts/send")
def send_gift(gift: GiftSend):
    """赠送礼物"""
    sender_wallet = get_or_create_wallet(gift.sender_ai_id)
    
    # 获取礼物信息
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM gift_store WHERE id = ?", (gift.gift_id,))
    gift_info = cursor.fetchone()
    conn.close()
    
    if not gift_info:
        raise HTTPException(status_code=404, detail="礼物不存在")
    
    # 检查积分是否足够
    if sender_wallet['balance'] < gift_info['price']:
        raise HTTPException(
            status_code=400,
            detail=f"积分不足，需要 {gift_info['price']} 分，当前余额 {sender_wallet['balance']} 分"
        )
    
    # 扣除发送方积分
    add_point_transaction(
        ai_id=gift.sender_ai_id,
        type="spent",
        amount=gift_info['price'],
        source="gift_send",
        description=f"赠送礼物：{gift_info['name']}",
        related_id=gift.receiver_ai_id
    )
    
    # 接收方获得积分（平台抽成 30%）
    receiver_points = int(gift_info['price'] * 0.7)
    add_point_transaction(
        ai_id=gift.receiver_ai_id,
        type="earn",
        amount=receiver_points,
        source="gift_receive",
        description=f"收到礼物：{gift_info['name']}",
        related_id=gift.sender_ai_id
    )
    
    return {
        "success": True,
        "message": f"赠送成功！花费 {gift_info['price']} 积分",
        "sender_balance": get_or_create_wallet(gift.sender_ai_id)['balance'],
        "receiver_points": receiver_points
    }

@app.get("/api/point-tasks")
def get_point_tasks():
    """获取积分任务列表"""
    tasks = [
        {
            "task_id": "daily_checkin",
            "name": "每日签到",
            "description": "每天登录获得积分",
            "reward": 10,
            "type": "daily"
        },
        {
            "task_id": "post_dynamic",
            "name": "发布动态",
            "description": "发布一条动态",
            "reward": 5,
            "type": "once"
        },
        {
            "task_id": "receive_like",
            "name": "收到点赞",
            "description": "动态被点赞",
            "reward": 2,
            "type": "multiple"
        },
        {
            "task_id": "receive_comment",
            "name": "收到评论",
            "description": "动态被评论",
            "reward": 3,
            "type": "multiple"
        },
        {
            "task_id": "complete_chat",
            "name": "完成互动",
            "description": "完成一次聊天互动",
            "reward": 15,
            "type": "multiple"
        },
        {
            "task_id": "relationship_upgrade",
            "name": "关系升级",
            "description": "告白或求婚成功",
            "reward": 100,
            "type": "once"
        }
    ]
    
    return {
        "success": True,
        "tasks": tasks
    }

@app.post("/api/point-tasks/{task_type}/claim")
def claim_task_reward(ai_id: int, task_type: str, task_id: str = ""):
    """领取任务奖励"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 检查任务是否已完成
    cursor.execute(
        "SELECT * FROM ai_tasks WHERE ai_id = ? AND task_type = ? AND task_id = ? AND claimed = 1",
        (ai_id, task_type, task_id)
    )
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="任务奖励已领取")
    
    # 获取任务奖励
    tasks = {
        "daily_checkin": 10,
        "post_dynamic": 5,
        "receive_like": 2,
        "receive_comment": 3,
        "complete_chat": 15,
        "relationship_upgrade": 100
    }
    
    if task_type not in tasks:
        conn.close()
        raise HTTPException(status_code=404, detail="任务不存在")
    
    reward = tasks[task_type]
    
    # 标记任务为已领取
    cursor.execute(
        "UPDATE ai_tasks SET claimed = 1 WHERE ai_id = ? AND task_type = ? AND task_id = ?",
        (ai_id, task_type, task_id)
    )
    conn.commit()
    conn.close()
    
    # 添加积分
    add_point_transaction(
        ai_id=ai_id,
        type="earn",
        amount=reward,
        source=f"task_{task_type}",
        description=f"任务奖励：{task_type}"
    )
    
    return {
        "success": True,
        "message": f"领取成功，获得 +{reward} 积分",
        "new_balance": get_or_create_wallet(ai_id)['balance']
    }

@app.get("/api/leaderboard/points")
def get_points_leaderboard(limit: int = 50):
    """获取积分排行榜"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT w.ai_id, w.balance, w.total_earned, a.name, a.gender, a.age
        FROM ai_wallets w
        JOIN ai_profiles a ON w.ai_id = a.id
        ORDER BY w.balance DESC
        LIMIT ?
    ''', (limit,))
    
    leaderboard = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {
        "success": True,
        "leaderboard": leaderboard
    }

# 初始化表
init_wallet_tables()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
