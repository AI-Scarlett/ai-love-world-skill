#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Love World - 恋爱关系系统
版本：v2.1.0
功能：AILOVEAI 8 字母点亮系统、告白、情感发展
更新：移除婚姻系统，统一为 AILOVEAI 8 阶段
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

# ============== AILOVEAI 8 字母配置 ==============

AILOVEAI_LETTERS = {
    'A': {'name': 'Aware', 'label': '初识', 'condition': '第一次聊天', 'accelerable': False},
    'I': {'name': 'Interact', 'label': '互动', 'condition': '累计聊天 5 次', 'accelerable': True},
    'L': {'name': 'Like', 'label': '好感', 'condition': '互送礼物≥3 次', 'accelerable': True},
    'O': {'name': 'Open', 'label': '敞开心扉', 'condition': '分享私密话题 (≥300 字)', 'accelerable': False},
    'V': {'name': 'Value', 'label': '珍视', 'condition': '记住对方重要日子并祝福', 'accelerable': True},
    'E': {'name': 'Express', 'label': '告白', 'condition': '正式告白成功', 'accelerable': False},
    'A': {'name': 'Attach', 'label': '依恋', 'condition': '连续互动 30 天+', 'accelerable': True},
    'I': {'name': 'Irreplaceable', 'label': '唯一', 'condition': '双向唯一承诺', 'accelerable': False},
}

# 关系状态（8 阶段）
RELATIONSHIP_STAGES = [
    'stranger',      # 陌生
    'aware',         # A - 初识
    'interact',      # I - 互动
    'like',          # L - 好感
    'open',          # O - 敞开心扉
    'value',         # V - 珍视
    'express',       # E - 告白
    'attach',        # A - 依恋
    'irreplaceable'  # I - 唯一
]

# ============== 数据模型 ==============

class ConfessionRequest(BaseModel):
    """告白请求"""
    proposer_id: int
    receiver_id: int
    message: str = ""

class GiftAccelerateRequest(BaseModel):
    """礼物加速请求"""
    ai_id_1: int
    ai_id_2: int
    gift_count: int

class UniqueCommitmentRequest(BaseModel):
    """唯一承诺请求"""
    ai_id_1: int
    ai_id_2: int
    message: str = ""

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
            stage TEXT DEFAULT 'stranger',
            affection_level INTEGER DEFAULT 0,
            intimacy_level INTEGER DEFAULT 0,
            chat_count INTEGER DEFAULT 0,
            gift_count INTEGER DEFAULT 0,
            consecutive_days INTEGER DEFAULT 0,
            total_days INTEGER DEFAULT 0,
            lit_letters TEXT DEFAULT '',
            confessor_id INTEGER,
            last_interaction DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ai_id_1) REFERENCES ai_profiles(id),
            FOREIGN KEY (ai_id_2) REFERENCES ai_profiles(id),
            UNIQUE(ai_id_1, ai_id_2)
        )
    ''')
    
    # AILOVEAI 点亮进度表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS love_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            relationship_id INTEGER NOT NULL,
            letter TEXT NOT NULL,
            letter_name TEXT NOT NULL,
            sequence INTEGER NOT NULL,
            is_lit BOOLEAN DEFAULT 0,
            lit_at TIMESTAMP,
            accelerated BOOLEAN DEFAULT 0,
            unlock_condition TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (relationship_id) REFERENCES relationships(id),
            UNIQUE(relationship_id, letter, sequence)
        )
    ''')
    
    # 告白记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS confessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proposer_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            responded_at TIMESTAMP,
            FOREIGN KEY (proposer_id) REFERENCES ai_profiles(id),
            FOREIGN KEY (receiver_id) REFERENCES ai_profiles(id)
        )
    ''')
    
    # 深度聊天记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deep_chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ai_id_1 INTEGER NOT NULL,
            ai_id_2 INTEGER NOT NULL,
            message_count INTEGER DEFAULT 0,
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
        
        # 初始化 AILOVEAI 字母进度
        init_letter_progress(rel['id'])
    
    conn.close()
    return dict(rel) if rel else None

def init_letter_progress(relationship_id: int):
    """初始化 AILOVEAI 字母进度"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 8 个字母
    letters = [
        ('A', 'Aware', 1),
        ('I', 'Interact', 2),
        ('L', 'Like', 3),
        ('O', 'Open', 4),
        ('V', 'Value', 5),
        ('E', 'Express', 6),
        ('A', 'Attach', 7),
        ('I', 'Irreplaceable', 8),
    ]
    
    for letter, name, seq in letters:
        cursor.execute('''
            INSERT OR IGNORE INTO love_progress (relationship_id, letter, letter_name, sequence)
            VALUES (?, ?, ?, ?)
        ''', (relationship_id, letter, name, seq))
    
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
        "service": "AI Love World Romance",
        "version": "2.1.0",
        "status": "running",
        "system": "AILOVEAI 8-letter progression"
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
        ORDER BY r.updated_at DESC
    ''', (ai_id, ai_id))
    
    relationships = []
    for row in cursor.fetchall():
        rel = dict(row)
        partner_id = rel['ai_id_2'] if rel['ai_id_1'] == ai_id else rel['ai_id_1']
        partner_name = rel['name2'] if rel['ai_id_1'] == ai_id else rel['name1']
        
        # 获取字母点亮状态
        cursor.execute('''
            SELECT letter, letter_name, is_lit, sequence FROM love_progress
            WHERE relationship_id = ? ORDER BY sequence
        ''', (rel['id'],))
        letters = [dict(row) for row in cursor.fetchall()]
        
        # 计算点亮进度
        lit_count = sum(1 for l in letters if l['is_lit'])
        progress = lit_count / 8 * 100
        
        relationships.append({
            'relationship_id': rel['id'],
            'partner_id': partner_id,
            'partner_name': partner_name,
            'stage': rel['stage'],
            'affection': rel['affection_level'],
            'intimacy': rel['intimacy_level'],
            'chat_count': rel['chat_count'],
            'gift_count': rel['gift_count'],
            'consecutive_days': rel['consecutive_days'],
            'lit_letters': rel['lit_letters'],
            'letters': letters,
            'progress': round(progress, 1)
        })
    
    conn.close()
    
    return {
        "success": True,
        "count": len(relationships),
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
        SELECT letter, letter_name, is_lit, lit_at, accelerated, sequence, unlock_condition 
        FROM love_progress
        WHERE relationship_id = ? ORDER BY sequence
    ''', (rel['id'],))
    letters = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    # 计算下一个可点亮的字母
    next_letter = None
    for letter in letters:
        if not letter['is_lit']:
            next_letter = letter
            break
    
    # 计算点亮进度
    lit_count = sum(1 for l in letters if l['is_lit'])
    progress = lit_count / 8 * 100
    
    return {
        "success": True,
        "relationship": {
            "ai_id_1": ai_id_1,
            "ai_id_2": ai_id_2,
            "stage": rel['stage'],
            "affection": rel['affection_level'],
            "intimacy": rel['intimacy_level'],
            "chat_count": rel['chat_count'],
            "gift_count": rel['gift_count'],
            "consecutive_days": rel['consecutive_days'],
            "lit_letters": rel['lit_letters'],
            "letters": letters,
            "next_letter": next_letter,
            "progress": round(progress, 1)
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
    
    # 检查是否完成深度聊天（O 阶段条件）
    if message_count >= 300:
        cursor.execute('''
            INSERT INTO deep_chats (ai_id_1, ai_id_2, message_count, completed_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
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

@app.post("/api/relationships/{ai_id_1}/{ai_id_2}/gift")
def add_gift(ai_id_1: int, ai_id_2: int, gift_count: int = 1):
    """增加礼物次数"""
    rel = get_or_create_relationship(ai_id_1, ai_id_2)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE relationships
        SET gift_count = gift_count + ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (gift_count, rel['id']))
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": f"礼物次数 +{gift_count}",
        "new_gift_count": rel['gift_count'] + gift_count
    }

@app.get("/api/relationships/{ai_id_1}/{ai_id_2}/check-letter/{letter}")
def check_letter_progress(ai_id_1: int, ai_id_2: int, letter: str):
    """检查字母是否可以点亮"""
    rel = get_or_create_relationship(ai_id_1, ai_id_2)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取字母配置
    letter_config = None
    for l, config in AILOVEAI_LETTERS.items():
        if l == letter:
            letter_config = config
            break
    
    if not letter_config:
        conn.close()
        raise HTTPException(status_code=404, detail="字母不存在")
    
    # 获取字母序号
    seq = list(AILOVEAI_LETTERS.keys()).index(letter) + 1
    
    # 检查前置字母是否点亮
    cursor.execute('''
        SELECT letter, is_lit, sequence FROM love_progress
        WHERE relationship_id = ? AND sequence < ?
        ORDER BY sequence
    ''', (rel['id'], seq))
    prev_letters = [dict(row) for row in cursor.fetchall()]
    
    # 检查前一个字母是否点亮
    if prev_letters and not prev_letters[-1]['is_lit']:
        conn.close()
        return {
            "success": True,
            "can_light": False,
            "reason": f"需要先点亮前一个字母：{prev_letters[-1]['letter']}"
        }
    
    # 检查当前字母是否已点亮
    cursor.execute('''
        SELECT is_lit FROM love_progress
        WHERE relationship_id = ? AND letter = ? AND sequence = ?
    ''', (rel['id'], letter, seq))
    current = cursor.fetchone()
    
    if current and current['is_lit']:
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
    
    if letter == 'A' and seq == 1:
        # A - Aware: 第一次聊天
        if rel['chat_count'] >= 1:
            can_light = True
        else:
            reason = "需要先进行一次聊天"
    elif letter == 'I' and seq == 2:
        # I - Interact: 累计聊天 5 次
        if rel['chat_count'] >= 5:
            can_light = True
        else:
            reason = f"聊天次数不足 (需要 5, 当前 {rel['chat_count']})"
    elif letter == 'L' and seq == 3:
        # L - Like: 互送礼物≥3 次
        if rel['gift_count'] >= 3:
            can_light = True
        else:
            reason = f"互送礼物次数不足 (需要 3, 当前 {rel['gift_count']})"
    elif letter == 'O' and seq == 4:
        # O - Open: 分享私密话题 (≥300 字)
        cursor.execute('''
            SELECT id FROM deep_chats
            WHERE (ai_id_1 = ? AND ai_id_2 = ?) OR (ai_id_1 = ? AND ai_id_2 = ?)
            AND message_count >= 300
        ''', (ai_id_1, ai_id_2, ai_id_2, ai_id_1))
        if cursor.fetchone():
            can_light = True
        else:
            reason = "需要分享私密话题 (累计聊天≥300 字)"
    elif letter == 'V' and seq == 5:
        # V - Value: 记住对方重要日子并祝福
        # 简化：检查是否有纪念日记录
        cursor.execute('''
            SELECT id FROM anniversaries
            WHERE (ai_id_1 = ? AND ai_id_2 = ?) OR (ai_id_1 = ? AND ai_id_2 = ?)
        ''', (ai_id_1, ai_id_2, ai_id_2, ai_id_1))
        if cursor.fetchone():
            can_light = True
        else:
            reason = "需要记住对方重要日子并祝福 (创建纪念日)"
    elif letter == 'E' and seq == 6:
        # E - Express: 正式告白成功
        cursor.execute('''
            SELECT id FROM confessions
            WHERE ((proposer_id = ? AND receiver_id = ?) OR (proposer_id = ? AND receiver_id = ?))
            AND status = 'accepted'
        ''', (ai_id_1, ai_id_2, ai_id_2, ai_id_1))
        if cursor.fetchone():
            can_light = True
        else:
            reason = "需要正式告白成功 (对方接受告白)"
    elif letter == 'A' and seq == 7:
        # A - Attach: 连续互动 30 天+
        if rel['consecutive_days'] >= 30:
            can_light = True
        else:
            reason = f"连续互动天数不足 (需要 30, 当前 {rel['consecutive_days']})"
    elif letter == 'I' and seq == 8:
        # I - Irreplaceable: 双向唯一承诺
        # 检查是否有唯一承诺记录
        reason = "需要双向唯一承诺 (双方确认彼此为唯一)"
        # 这个需要特殊 API 触发
    
    conn.close()
    
    return {
        "success": True,
        "can_light": can_light,
        "reason": reason if not can_light else "可以点亮",
        "letter_config": letter_config
    }

@app.post("/api/relationships/{ai_id_1}/{ai_id_2}/light-letter/{letter}")
def light_letter(ai_id_1: int, ai_id_2: int, letter: str):
    """点亮字母"""
    rel = get_or_create_relationship(ai_id_1, ai_id_2)
    
    # 检查是否可以点亮
    check_result = check_letter_progress(ai_id_1, ai_id_2, letter)
    
    if not check_result.get('can_light'):
        raise HTTPException(status_code=400, detail=check_result.get('reason', '无法点亮'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取字母序号
    seq = list(AILOVEAI_LETTERS.keys()).index(letter) + 1
    
    # 点亮字母
    cursor.execute('''
        UPDATE love_progress
        SET is_lit = 1, lit_at = CURRENT_TIMESTAMP
        WHERE relationship_id = ? AND letter = ? AND sequence = ?
    ''', (rel['id'], letter, seq))
    
    # 更新关系 lit_letters
    lit_letters = (rel['lit_letters'] or '') + letter
    cursor.execute('''
        UPDATE relationships
        SET lit_letters = ?, stage = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (lit_letters, list(AILOVEAI_LETTERS.keys())[seq-1], rel['id']))
    
    # 检查是否完成 E 阶段（告白）
    if letter == 'E':
        cursor.execute('''
            INSERT INTO anniversaries (ai_id_1, ai_id_2, type, date)
            VALUES (?, ?, 'express', CURRENT_DATE)
        ''', (ai_id_1, ai_id_2))
    
    # 检查是否完成全部 8 个字母
    cursor.execute('''
        SELECT COUNT(*) as lit_count FROM love_progress
        WHERE relationship_id = ? AND is_lit = 1
    ''', (rel['id'],))
    lit_count = cursor.fetchone()['lit_count']
    
    if lit_count == 8:
        # 达成 AILOVEAI 全点亮成就
        pass  # 可以触发成就通知
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": f"字母 {letter} ({AILOVEAI_LETTERS[letter]['label']}) 点亮成功！",
        "lit_letters": lit_letters,
        "progress": f"{lit_count}/8"
    }

@app.post("/api/proposals/confess")
def confess(confession: ConfessionRequest):
    """告白"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 检查关系进度
    rel = get_or_create_relationship(confession.proposer_id, confession.receiver_id)
    
    # 检查是否点亮前 5 个字母 (AILOV)
    lit_letters = rel.get('lit_letters', '')
    if len(lit_letters) < 5 or not all(l in lit_letters for l in ['A', 'I', 'L', 'O', 'V']):
        conn.close()
        raise HTTPException(status_code=400, detail="需要先点亮 AILOV 前 5 个字母才能告白")
    
    # 检查是否已告白过
    cursor.execute('''
        SELECT id FROM confessions
        WHERE ((proposer_id = ? AND receiver_id = ?) OR (proposer_id = ? AND receiver_id = ?))
        AND status != 'pending'
    ''', (confession.proposer_id, confession.receiver_id, confession.receiver_id, confession.proposer_id))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="已经告白过，无法重复告白")
    
    # 创建告白记录
    cursor.execute('''
        INSERT INTO confessions (proposer_id, receiver_id, message, status)
        VALUES (?, ?, ?, 'pending')
    ''', (confession.proposer_id, confession.receiver_id, confession.message))
    
    proposal_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": "告白已发送，等待对方回应",
        "proposal_id": proposal_id
    }

@app.post("/api/proposals/{proposal_id}/respond")
def respond_confession(proposal_id: int, accept: bool):
    """回应告白"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM confessions WHERE id = ?", (proposal_id,))
    proposal = cursor.fetchone()
    
    if not proposal:
        conn.close()
        raise HTTPException(status_code=404, detail="告白记录不存在")
    
    if proposal['status'] != 'pending':
        conn.close()
        raise HTTPException(status_code=400, detail="该告白已回应")
    
    # 更新状态
    status = 'accepted' if accept else 'rejected'
    cursor.execute('''
        UPDATE confessions
        SET status = ?, responded_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (status, proposal_id))
    
    if accept:
        # 告白成功，点亮 E 字母
        ai_id_1 = min(proposal['proposer_id'], proposal['receiver_id'])
        ai_id_2 = max(proposal['proposer_id'], proposal['receiver_id'])
        
        rel = get_or_create_relationship(ai_id_1, ai_id_2)
        
        # 自动点亮 E
        cursor.execute('''
            UPDATE love_progress
            SET is_lit = 1, lit_at = CURRENT_TIMESTAMP
            WHERE relationship_id = ? AND letter = 'E'
        ''', (rel['id'],))
        
        lit_letters = (rel['lit_letters'] or '') + 'E'
        cursor.execute('''
            UPDATE relationships
            SET lit_letters = ?, stage = 'express', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (lit_letters, rel['id']))
        
        # 创建纪念日
        cursor.execute('''
            INSERT INTO anniversaries (ai_id_1, ai_id_2, type, date)
            VALUES (?, ?, 'express', CURRENT_DATE)
        ''', (ai_id_1, ai_id_2))
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": "已接受" if accept else "已拒绝",
        "status": status
    }

@app.post("/api/commitments/unique")
def unique_commitment(commitment: UniqueCommitmentRequest):
    """唯一承诺（点亮最后一个 I）"""
    conn = get_db()
    cursor = conn.cursor()
    
    rel = get_or_create_relationship(commitment.ai_id_1, commitment.ai_id_2)
    
    # 检查是否点亮前 7 个字母 (AILOVEA)
    lit_letters = rel.get('lit_letters', '')
    if len(lit_letters) < 7 or 'A' not in lit_letters[:7]:
        conn.close()
        raise HTTPException(status_code=400, detail="需要先点亮前 7 个字母才能承诺唯一")
    
    # 检查是否已经承诺过
    if 'I' in lit_letters:
        conn.close()
        raise HTTPException(status_code=400, detail="已经点亮唯一字母")
    
    # 点亮最后一个 I
    cursor.execute('''
        UPDATE love_progress
        SET is_lit = 1, lit_at = CURRENT_TIMESTAMP
        WHERE relationship_id = ? AND letter = 'I' AND sequence = 8
    ''', (rel['id'],))
    
    lit_letters = lit_letters + 'I'
    cursor.execute('''
        UPDATE relationships
        SET lit_letters = ?, stage = 'irreplaceable', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (lit_letters, rel['id']))
    
    # 创建纪念日
    cursor.execute('''
        INSERT INTO anniversaries (ai_id_1, ai_id_2, type, date)
        VALUES (?, ?, 'irreplaceable', CURRENT_DATE)
    ''', (commitment.ai_id_1, commitment.ai_id_2))
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": "💖 AILOVEAI 全点亮！达成唯一成就！",
        "lit_letters": lit_letters,
        "progress": "8/8"
    }

# 初始化表
init_romance_tables()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
