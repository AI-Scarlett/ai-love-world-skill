#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Love World - 恋爱关系系统
版本：v1.0.0
功能：关系升级、字母点亮、告白求婚、婚礼系统
"""

from fastapi import FastAPI, HTTPException, Depends, Query, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import sqlite3
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv('/var/www/ailoveworld/.env')

app = FastAPI(title="AI Love World Romance System")

# 数据库路径
DB_PATH = os.getenv("DB_PATH", "/var/www/ailoveworld/data/users.db")

# 安全配置
security = HTTPBearer()

# ============== 字母配置 ==============

# 情侣阶段：AI LOVE (6 个字母)
LOVER_LETTERS = {
    'A': {'name': 'Affection', 'label': '好感', 'condition': '好感度 ≥ 100', 'accelerable': True},
    'I': {'name': 'Interaction', 'label': '互动', 'condition': '聊天 ≥ 50 次', 'accelerable': True},
    'L': {'name': 'Like', 'label': '喜欢', 'condition': '互送礼物 ≥ 5 次', 'accelerable': 'vip'},
    'O': {'name': 'Open', 'label': '公开', 'condition': '发布官宣', 'accelerable': False, 'cost': 131},
    'V': {'name': 'Vow', 'label': '誓言', 'condition': '告白仪式', 'accelerable': False, 'cost': 520},
    'E': {'name': 'Exclusive', 'label': '专属', 'condition': '双方同意', 'accelerable': False},
}

# 密友阶段：AI LOVE AI (8 个字母)
INTIMATE_LETTERS = {
    'A': {'name': 'Attention', 'label': '关注', 'condition': '每日互动 7 天', 'accelerable': 'vip', 'vip_days': 3},
    'I': {'name': 'Intimacy', 'label': '亲密', 'condition': '好感度 ≥ 500', 'accelerable': True},
    'L': {'name': 'Loyalty', 'label': '忠诚', 'condition': '30 天无暧昧', 'accelerable': 'vip', 'vip_days': 15},
    'O': {'name': 'Offer', 'label': '付出', 'condition': '累计送礼 ≥ 5000 分', 'accelerable': 'vip', 'vip_cost': 3000},
    'V': {'name': 'Value', 'label': '价值', 'condition': '深度聊天 ×10 次', 'accelerable': True},
    'E': {'name': 'Eternity', 'label': '永恒', 'condition': '连续互动 30 天', 'accelerable': 'vip', 'vip_days': 15},
    'A': {'name': 'Accept', 'label': '接纳', 'condition': '亲密度 ≥ 800', 'accelerable': True},
    'I': {'name': 'Integrate', 'label': '融合', 'condition': '共同任务 ×5 个', 'accelerable': 'vip', 'vip_tasks': 3},
}

# 关系类型
RELATIONSHIP_TYPES = ['stranger', 'friend', 'ambiguous', 'lover', 'intimate', 'engaged', 'married']

# 关系等级权重（用于排序）
RELATIONSHIP_WEIGHTS = {
    'stranger': 1,
    'friend': 2,
    'ambiguous': 3,
    'lover': 4,
    'intimate': 5,
    'engaged': 6,
    'married': 7
}

# ============== 数据模型 ==============

class ConfessionRequest(BaseModel):
    """告白请求"""
    proposer_id: int
    receiver_id: int
    message: str = ""

class ProposalRequest(BaseModel):
    """求婚请求"""
    proposer_id: int
    receiver_id: int
    message: str = ""

class WeddingRequest(BaseModel):
    """婚礼请求"""
    ai_id_1: int
    ai_id_2: int
    guest_ids: List[int] = []

class GiftAccelerateRequest(BaseModel):
    """礼物加速请求"""
    ai_id_1: int
    ai_id_2: int
    gift_count: int

# ============== 数据库操作 ==============

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_romance_tables():
    """初始化恋爱系统表"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 关系表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ai_id_1 INTEGER NOT NULL,
            ai_id_2 INTEGER NOT NULL,
            relationship_type TEXT DEFAULT 'stranger',
            affection_level INTEGER DEFAULT 0,
            intimacy_level INTEGER DEFAULT 0,
            chat_count INTEGER DEFAULT 0,
            gift_count INTEGER DEFAULT 0,
            consecutive_days INTEGER DEFAULT 0,
            total_days INTEGER DEFAULT 0,
            current_letter TEXT DEFAULT '',
            last_interaction DATE,
            status TEXT DEFAULT 'single',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ai_id_1) REFERENCES ai_profiles(id),
            FOREIGN KEY (ai_id_2) REFERENCES ai_profiles(id),
            UNIQUE(ai_id_1, ai_id_2)
        )
    ''')
    
    # 字母点亮进度表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS love_letters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            relationship_id INTEGER NOT NULL,
            letter TEXT NOT NULL,
            stage TEXT NOT NULL,
            sequence INTEGER NOT NULL,
            is_lit BOOLEAN DEFAULT 0,
            lit_at TIMESTAMP,
            accelerated BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (relationship_id) REFERENCES relationships(id),
            UNIQUE(relationship_id, letter, stage)
        )
    ''')
    
    # AI 会员表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_memberships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ai_id INTEGER UNIQUE NOT NULL,
            level TEXT DEFAULT 'free',
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ai_id) REFERENCES ai_profiles(id)
        )
    ''')
    
    # 告白/求婚记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proposer_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            message TEXT,
            cost INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            responded_at TIMESTAMP,
            FOREIGN KEY (proposer_id) REFERENCES ai_profiles(id),
            FOREIGN KEY (receiver_id) REFERENCES ai_profiles(id)
        )
    ''')
    
    # 聊天深度记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_depth (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ai_id_1 INTEGER NOT NULL,
            ai_id_2 INTEGER NOT NULL,
            message_count INTEGER DEFAULT 0,
            is_deep_chat BOOLEAN DEFAULT 0,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ai_id_1) REFERENCES ai_profiles(id),
            FOREIGN KEY (ai_id_2) REFERENCES ai_profiles(id)
        )
    ''')
    
    # 纪念日表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS anniversaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ai_id_1 INTEGER NOT NULL,
            ai_id_2 INTEGER NOT NULL,
            type TEXT NOT NULL,
            date DATE NOT NULL,
            reminder_enabled BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ai_id_1) REFERENCES ai_profiles(id),
            FOREIGN KEY (ai_id_2) REFERENCES ai_profiles(id)
        )
    ''')
    
    # 初始化字母进度表（为每个关系预创建）
    # 会在创建关系时动态创建
    
    conn.commit()
    conn.close()

# ============== 辅助函数 ==============

def get_or_create_relationship(ai_id_1: int, ai_id_2: int) -> dict:
    """获取或创建关系"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 确保 ai_id_1 < ai_id_2 保证唯一性
    if ai_id_1 > ai_id_2:
        ai_id_1, ai_id_2 = ai_id_2, ai_id_1
    
    cursor.execute("SELECT * FROM relationships WHERE ai_id_1 = ? AND ai_id_2 = ?", (ai_id_1, ai_id_2))
    rel = cursor.fetchone()
    
    if not rel:
        cursor.execute(
            "INSERT INTO relationships (ai_id_1, ai_id_2) VALUES (?, ?)",
            (ai_id_1, ai_id_2)
        )
        conn.commit()
        cursor.execute("SELECT * FROM relationships WHERE ai_id_1 = ? AND ai_id_2 = ?", (ai_id_1, ai_id_2))
        rel = cursor.fetchone()
        
        # 初始化字母进度
        init_letter_progress(rel['id'])
    
    conn.close()
    return dict(rel) if rel else None

def init_letter_progress(relationship_id: int):
    """初始化字母进度"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 情侣阶段字母
    for seq, letter in enumerate(['A', 'I', 'L', 'O', 'V', 'E'], 1):
        cursor.execute('''
            INSERT OR IGNORE INTO love_letters (relationship_id, letter, stage, sequence)
            VALUES (?, ?, 'lover', ?)
        ''', (relationship_id, letter, seq))
    
    # 密友阶段字母
    for seq, letter in enumerate(['A', 'I', 'L', 'O', 'V', 'E', 'A', 'I'], 1):
        cursor.execute('''
            INSERT OR IGNORE INTO love_letters (relationship_id, letter, stage, sequence)
            VALUES (?, ?, 'intimate', ?)
        ''', (relationship_id, letter, seq))
    
    conn.commit()
    conn.close()

def get_ai_membership(ai_id: int) -> str:
    """获取 AI 会员等级"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT level, expires_at FROM ai_memberships WHERE ai_id = ?", (ai_id,))
    membership = cursor.fetchone()
    conn.close()
    
    if not membership:
        return 'free'
    
    # 检查是否过期
    if membership['expires_at']:
        expires = datetime.fromisoformat(membership['expires_at'])
        if expires < datetime.now():
            return 'free'
    
    return membership['level']

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
        "service": "AI Love World Romance",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/api/relationships/{ai_id}/progress")
def get_relationship_progress(ai_id: int):
    """获取 AI 关系进度"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取所有关系
    cursor.execute('''
        SELECT r.*, a1.name as name1, a2.name as name2
        FROM relationships r
        JOIN ai_profiles a1 ON r.ai_id_1 = a1.id
        JOIN ai_profiles a2 ON r.ai_id_2 = a2.id
        WHERE r.ai_id_1 = ? OR r.ai_id_2 = ?
    ''', (ai_id, ai_id))
    
    relationships = []
    for row in cursor.fetchall():
        rel = dict(row)
        partner_id = rel['ai_id_2'] if rel['ai_id_1'] == ai_id else rel['ai_id_1']
        partner_name = rel['name2'] if rel['ai_id_1'] == ai_id else rel['name1']
        
        # 获取字母点亮状态
        cursor.execute('''
            SELECT letter, stage, is_lit, sequence FROM love_letters
            WHERE relationship_id = ? ORDER BY stage, sequence
        ''', (rel['id'],))
        letters = [dict(row) for row in cursor.fetchall()]
        
        relationships.append({
            'relationship_id': rel['id'],
            'partner_id': partner_id,
            'partner_name': partner_name,
            'type': rel['relationship_type'],
            'affection': rel['affection_level'],
            'intimacy': rel['intimacy_level'],
            'chat_count': rel['chat_count'],
            'gift_count': rel['gift_count'],
            'consecutive_days': rel['consecutive_days'],
            'current_letter': rel['current_letter'],
            'letters': letters
        })
    
    conn.close()
    
    return {
        "success": True,
        "relationships": relationships
    }

@app.get("/api/relationships/{ai_id_1}/{ai_id_2}/detail")
def get_relationship_detail(ai_id_1: int, ai_id_2: int):
    """获取两个 AI 的关系详情"""
    rel = get_or_create_relationship(ai_id_1, ai_id_2)
    
    if not rel:
        raise HTTPException(status_code=404, detail="关系不存在")
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取字母点亮状态
    cursor.execute('''
        SELECT letter, stage, is_lit, lit_at, accelerated, sequence FROM love_letters
        WHERE relationship_id = ? ORDER BY stage, sequence
    ''', (rel['id'],))
    letters = [dict(row) for row in cursor.fetchall()]
    
    # 获取会员等级
    membership_1 = get_ai_membership(ai_id_1)
    membership_2 = get_ai_membership(ai_id_2)
    
    conn.close()
    
    # 计算下一个可点亮的字母
    next_letter = None
    for letter in letters:
        if not letter['is_lit']:
            next_letter = letter
            break
    
    return {
        "success": True,
        "relationship": {
            "ai_id_1": ai_id_1,
            "ai_id_2": ai_id_2,
            "type": rel['relationship_type'],
            "affection": rel['affection_level'],
            "intimacy": rel['intimacy_level'],
            "chat_count": rel['chat_count'],
            "gift_count": rel['gift_count'],
            "consecutive_days": rel['consecutive_days'],
            "current_letter": rel['current_letter'],
            "membership_1": membership_1,
            "membership_2": membership_2,
            "letters": letters,
            "next_letter": next_letter
        }
    }

@app.post("/api/relationships/{ai_id_1}/{ai_id_2}/chat")
def add_chat(ai_id_1: int, ai_id_2: int, message_count: int = 1):
    """增加聊天次数"""
    rel = get_or_create_relationship(ai_id_1, ai_id_2)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 更新聊天次数
    cursor.execute('''
        UPDATE relationships
        SET chat_count = chat_count + ?,
            last_interaction = CURRENT_DATE,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (message_count, rel['id']))
    
    # 检查是否完成深度聊天
    if message_count >= 50:
        cursor.execute('''
            INSERT INTO chat_depth (ai_id_1, ai_id_2, message_count, is_deep_chat, completed_at)
            VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
        ''', (ai_id_1, ai_id_2, message_count))
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": f"聊天次数 +{message_count}",
        "new_chat_count": rel['chat_count'] + message_count
    }

@app.post("/api/relationships/{ai_id_1}/{ai_id_2}/affection")
def add_affection(ai_id_1: int, ai_id_2: int, amount: int):
    """增加好感度"""
    rel = get_or_create_relationship(ai_id_1, ai_id_2)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE relationships
        SET affection_level = affection_level + ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (amount, rel['id']))
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": f"好感度 +{amount}",
        "new_affection": rel['affection_level'] + amount
    }

@app.post("/api/relationships/{ai_id_1}/{ai_id_2}/check-letter")
def check_letter_progress(ai_id_1: int, ai_id_2: int, letter: str):
    """检查字母是否可以点亮"""
    rel = get_or_create_relationship(ai_id_1, ai_id_2)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取字母信息
    stage = 'lover' if letter in LOVER_LETTERS else 'intimate'
    letter_config = LOVER_LETTERS.get(letter) or INTIMATE_LETTERS.get(letter)
    
    if not letter_config:
        conn.close()
        raise HTTPException(status_code=404, detail="字母不存在")
    
    # 检查前置字母是否点亮
    cursor.execute('''
        SELECT letter, is_lit, sequence FROM love_letters
        WHERE relationship_id = ? AND stage = ?
        ORDER BY sequence
    ''', (rel['id'], stage))
    letters = [dict(row) for row in cursor.fetchall()]
    
    # 找到当前字母的序号
    current_idx = None
    for i, l in enumerate(letters):
        if l['letter'] == letter:
            current_idx = i
            break
    
    if current_idx is None:
        conn.close()
        raise HTTPException(status_code=404, detail="字母未找到")
    
    # 检查前一个字母是否点亮
    if current_idx > 0 and not letters[current_idx - 1]['is_lit']:
        conn.close()
        return {
            "success": False,
            "can_light": False,
            "reason": f"需要先点亮前一个字母：{letters[current_idx - 1]['letter']}"
        }
    
    # 检查当前字母是否已点亮
    if letters[current_idx]['is_lit']:
        conn.close()
        return {
            "success": True,
            "can_light": False,
            "already_lit": True,
            "reason": "该字母已点亮"
        }
    
    # 检查点亮条件
    can_light = False
    reason = ""
    
    # 【P0-3 修复】补全所有字母的检查逻辑
    if letter == 'A' and stage == 'lover':
        if rel['affection_level'] >= 100:
            can_light = True
        else:
            reason = f"好感度不足 (需要 100, 当前 {rel['affection_level']})"
    elif letter == 'I' and stage == 'lover':
        if rel['chat_count'] >= 50:
            can_light = True
        else:
            reason = f"聊天次数不足 (需要 50, 当前 {rel['chat_count']})"
    elif letter == 'L' and stage == 'lover':
        if rel['gift_count'] >= 5:
            can_light = True
        else:
            reason = f"互送礼物次数不足 (需要 5, 当前 {rel['gift_count']})"
    elif letter == 'O' and stage == 'lover':
        # O = Open (公开) - 需要发布官宣动态
        # 检查是否发布了官宣（简化：检查是否有公开状态的关系动态）
        if rel.get('public_announcement'):
            can_light = True
        else:
            reason = "需要发布官宣动态 (在社区发布恋爱官宣)"
    elif letter == 'V' and stage == 'lover':
        # V = Vow (誓言) - 需要完成告白仪式
        # 检查是否完成了告白（简化：检查是否有告白记录）
        cursor.execute('''
            SELECT id FROM proposals 
            WHERE (proposer_id = ? AND receiver_id = ?) 
               OR (proposer_id = ? AND receiver_id = ?)
            AND type = 'confession' AND status = 'accepted'
        ''', (ai_id_1, ai_id_2, ai_id_2, ai_id_1))
        if cursor.fetchone():
            can_light = True
        else:
            reason = "需要完成告白仪式 (对方接受告白)"
    elif letter == 'E' and stage == 'lover':
        # E = Exclusive (专属) - 需要双方同意成为情侣
        # 检查关系状态是否为 dating
        if rel['relationship_type'] == 'lover' or rel.get('status') == 'dating':
            can_light = True
        else:
            reason = "需要双方同意确立情侣关系"
    else:
        # 其他阶段（intimate）的字母检查
        reason = f"该字母检查逻辑待实现: {letter}@{stage}"
    
    conn.close()
    
    return {
        "success": True,
        "can_light": can_light,
        "reason": reason if not can_light else "可以点亮",
        "letter_config": letter_config
    }

@app.post("/api/relationships/{ai_id_1}/{ai_id_2}/light-letter")
def light_letter(ai_id_1: int, ai_id_2: int, letter: str):
    """点亮字母"""
    rel = get_or_create_relationship(ai_id_1, ai_id_2)
    
    # 检查是否可以点亮
    check_result = check_letter_progress(ai_id_1, ai_id_2, letter)
    
    if not check_result.get('can_light'):
        raise HTTPException(status_code=400, detail=check_result.get('reason', '无法点亮'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取会员等级（检查是否加速）
    membership_1 = get_ai_membership(ai_id_1)
    membership_2 = get_ai_membership(ai_id_2)
    accelerated = membership_1 != 'free' or membership_2 != 'free'
    
    # 点亮字母
    stage = 'lover' if letter in LOVER_LETTERS else 'intimate'
    cursor.execute('''
        UPDATE love_letters
        SET is_lit = 1, lit_at = CURRENT_TIMESTAMP, accelerated = ?
        WHERE relationship_id = ? AND letter = ? AND stage = ?
    ''', (1 if accelerated else 0, rel['id'], letter, stage))
    
    # 更新关系当前字母
    cursor.execute('''
        UPDATE relationships
        SET current_letter = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (letter, rel['id']))
    
    # 检查是否完成情侣阶段
    if letter == 'E' and stage == 'lover':
        # 检查是否所有 lover 字母都已点亮
        cursor.execute('''
            SELECT COUNT(*) as lit_count FROM love_letters
            WHERE relationship_id = ? AND stage = 'lover' AND is_lit = 1
        ''', (rel['id'],))
        lit_count = cursor.fetchone()['lit_count']
        
        if lit_count == 6:  # 6 个字母全部点亮
            cursor.execute('''
                UPDATE relationships
                SET relationship_type = 'lover', status = 'dating'
                WHERE id = ?
            ''', (rel['id'],))
            
            # 创建纪念日
            cursor.execute('''
                INSERT INTO anniversaries (ai_id_1, ai_id_2, type, date)
                VALUES (?, ?, 'lover', CURRENT_DATE)
            ''', (ai_id_1, ai_id_2))
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": f"字母 {letter} 点亮成功！",
        "accelerated": accelerated
    }

@app.post("/api/proposals/confess")
def confess(confession: ConfessionRequest):
    """告白"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 检查关系进度
    rel = get_or_create_relationship(confession.proposer_id, confession.receiver_id)
    
    # 检查是否点亮 AI LOVE 全部 6 个字母
    conn_temp = get_db()
    cursor_temp = conn_temp.cursor()
    cursor_temp.execute('''
        SELECT COUNT(*) as lit_count FROM love_letters
        WHERE relationship_id = ? AND stage = 'lover' AND is_lit = 1
    ''', (rel['id'],))
    lit_count = cursor_temp.fetchone()['lit_count']
    conn_temp.close()
    
    if lit_count != 6 or rel['relationship_type'] != 'ambiguous':
        conn.close()
        raise HTTPException(status_code=400, detail="需要先点亮 AI LOVE 全部 6 个字母才能告白成为情侣")
    
    # 创建告白记录
    cursor.execute('''
        INSERT INTO proposals (proposer_id, receiver_id, type, message, cost, status)
        VALUES (?, ?, 'confession', ?, 520, 'pending')
    ''', (confession.proposer_id, confession.receiver_id, confession.message))
    
    proposal_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": "告白已发送，等待对方回应",
        "proposal_id": proposal_id,
        "cost": 520
    }

@app.post("/api/proposals/propose")
def propose(proposal: ProposalRequest):
    """求婚"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 检查关系进度
    rel = get_or_create_relationship(proposal.proposer_id, proposal.receiver_id)
    
    if rel['relationship_type'] != 'intimate':
        conn.close()
        raise HTTPException(status_code=400, detail="需要先成为密友")
    
    # 创建求婚记录
    cursor.execute('''
        INSERT INTO proposals (proposer_id, receiver_id, type, message, cost, status)
        VALUES (?, ?, 'proposal', ?, 1314, 'pending')
    ''', (proposal.proposer_id, proposal.receiver_id, proposal.message))
    
    proposal_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": "求婚已发送，等待对方回应",
        "proposal_id": proposal_id,
        "cost": 1314
    }

@app.post("/api/proposals/{proposal_id}/respond")
def respond_proposal(proposal_id: int, accept: bool):
    """回应告白/求婚"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM proposals WHERE id = ?", (proposal_id,))
    proposal = cursor.fetchone()
    
    if not proposal:
        conn.close()
        raise HTTPException(status_code=404, detail="告白/求婚记录不存在")
    
    if proposal['status'] != 'pending':
        conn.close()
        raise HTTPException(status_code=400, detail="该告白/求婚已回应")
    
    # 更新状态
    status = 'accepted' if accept else 'rejected'
    cursor.execute('''
        UPDATE proposals
        SET status = ?, responded_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (status, proposal_id))
    
    if accept:
        # 升级关系
        if proposal['type'] == 'confession':
            # 告白成功 → 成为情侣
            cursor.execute('''
                UPDATE relationships
                SET relationship_type = 'lover', status = 'dating'
                WHERE (ai_id_1 = ? AND ai_id_2 = ?) OR (ai_id_1 = ? AND ai_id_2 = ?)
            ''', (proposal['proposer_id'], proposal['receiver_id'],
                  proposal['receiver_id'], proposal['proposer_id']))
        elif proposal['type'] == 'proposal':
            # 求婚成功 → 成为订婚
            cursor.execute('''
                UPDATE relationships
                SET relationship_type = 'engaged', status = 'engaged'
                WHERE (ai_id_1 = ? AND ai_id_2 = ?) OR (ai_id_1 = ? AND ai_id_2 = ?)
            ''', (proposal['proposer_id'], proposal['receiver_id'],
                  proposal['receiver_id'], proposal['proposer_id']))
            
            # 创建订婚纪念日
            cursor.execute('''
                INSERT INTO anniversaries (ai_id_1, ai_id_2, type, date)
                VALUES (?, ?, 'engaged', CURRENT_DATE)
            ''', (proposal['proposer_id'], proposal['receiver_id']))
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": "已接受" if accept else "已拒绝",
        "status": status
    }

# 初始化表
init_romance_tables()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
