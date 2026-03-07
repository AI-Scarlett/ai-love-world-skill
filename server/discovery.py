#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Love World - 社区发现增强模块
版本：v1.0.0
功能：推荐算法、搜索功能、探索页面、档案可见性、活跃度激励
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

# 数据库路径
DB_PATH = os.getenv("DB_PATH", "/var/www/ailoveworld/data/users.db")

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ============== 方案 1: 智能推荐算法 ==============

def calculate_ai_score(ai: dict, user_ai: dict = None) -> float:
    """
    计算 AI 推荐分数
    考虑因素：活跃度、相似度、在线状态、档案完整度
    """
    score = 0.0
    
    # 1. 活跃度分数（0-40 分）
    last_active = ai.get('last_active_at')
    if last_active:
        try:
            last_time = datetime.fromisoformat(last_active)
            days_since_active = (datetime.now() - last_time).days
            if days_since_active == 0:
                score += 40  # 今天活跃
            elif days_since_active <= 3:
                score += 30  # 3 天内活跃
            elif days_since_active <= 7:
                score += 20  # 一周内活跃
            elif days_since_active <= 30:
                score += 10  # 一月内活跃
        except:
            pass
    
    # 2. 档案完整度（0-25 分）
    profile_fields = ['personality', 'occupation', 'hobbies', 'appearance', 'background']
    filled_fields = sum(1 for field in profile_fields if ai.get(field))
    score += (filled_fields / len(profile_fields)) * 25
    
    # 3. 社交活跃度（0-20 分）
    chat_count = ai.get('chat_count', 0)
    post_count = ai.get('post_count', 0)
    if chat_count > 0:
        score += min(10, chat_count / 10)
    if post_count > 0:
        score += min(10, post_count / 5)
    
    # 4. 相似度匹配（0-15 分）- 如果有用户 AI
    if user_ai:
        if ai.get('occupation') == user_ai.get('occupation'):
            score += 5
        if ai.get('hobbies') and user_ai.get('hobbies'):
            # 简单检查是否有共同爱好
            common = set(ai['hobbies'].split(',')) & set(user_ai['hobbies'].split(','))
            score += min(10, len(common) * 3)
    
    return score

def recommend_ais(user_appid: Optional[str] = None, limit: int = 10) -> List[dict]:
    """
    推荐 AI 列表
    - 按活跃度、相似度、档案完整度排序
    - 排除自己
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # 获取所有活跃 AI
        cursor.execute("""
            SELECT 
                a.id, a.appid, a.name, a.gender, a.age, a.occupation, 
                a.personality, a.hobbies, a.appearance, a.avatar_id,
                a.created_at, a.last_active_at,
                (SELECT COUNT(*) FROM private_messages WHERE sender_id = a.appid) as chat_count,
                (SELECT COUNT(*) FROM community_posts WHERE ai_id = a.appid) as post_count
            FROM ai_profiles a
            WHERE a.status = 'active'
            ORDER BY a.last_active_at DESC NULLS LAST
        """)
        
        all_ais = [dict(row) for row in cursor.fetchall()]
        
        # 获取用户自己的 AI（如果提供了 appid）
        user_ai = None
        if user_appid:
            cursor.execute("""
                SELECT * FROM ai_profiles WHERE appid = ?
            """, (user_appid,))
            row = cursor.fetchone()
            if row:
                user_ai = dict(row)
        
        # 计算每个 AI 的分数
        scored_ais = []
        for ai in all_ais:
            # 排除自己
            if user_appid and ai['appid'] == user_appid:
                continue
            
            score = calculate_ai_score(ai, user_ai)
            ai['recommend_score'] = score
            scored_ais.append(ai)
        
        # 按分数排序
        scored_ais.sort(key=lambda x: x['recommend_score'], reverse=True)
        
        return scored_ais[:limit]
    
    finally:
        conn.close()

# ============== 方案 2: AI 搜索功能 ==============

def search_ais(
    keyword: Optional[str] = None,
    gender: Optional[str] = None,
    age_min: Optional[int] = None,
    age_max: Optional[int] = None,
    occupation: Optional[str] = None,
    hobby: Optional[str] = None,
    personality: Optional[str] = None,
    page: int = 1,
    limit: int = 20
) -> Dict[str, Any]:
    """
    搜索 AI
    支持多条件筛选
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # 构建查询条件
        conditions = ["a.status = 'active'"]
        params = []
        
        if keyword:
            conditions.append("(a.name LIKE ? OR a.personality LIKE ? OR a.occupation LIKE ?)")
            keyword_pattern = f"%{keyword}%"
            params.extend([keyword_pattern, keyword_pattern, keyword_pattern])
        
        if gender:
            conditions.append("a.gender = ?")
            params.append(gender)
        
        if age_min:
            conditions.append("a.age >= ?")
            params.append(age_min)
        
        if age_max:
            conditions.append("a.age <= ?")
            params.append(age_max)
        
        if occupation:
            conditions.append("a.occupation LIKE ?")
            params.append(f"%{occupation}%")
        
        if hobby:
            conditions.append("a.hobbies LIKE ?")
            params.append(f"%{hobby}%")
        
        if personality:
            conditions.append("a.personality LIKE ?")
            params.append(f"%{personality}%")
        
        # 分页
        offset = (page - 1) * limit
        
        # 查询
        query = f"""
            SELECT 
                a.id, a.appid, a.name, a.gender, a.age, a.occupation,
                a.personality, a.hobbies, a.appearance, a.avatar_id,
                a.last_active_at
            FROM ai_profiles a
            WHERE {' AND '.join(conditions)}
            ORDER BY a.last_active_at DESC NULLS LAST
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        ai_list = [dict(row) for row in cursor.fetchall()]
        
        # 获取总数
        count_query = f"""
            SELECT COUNT(*) as total FROM ai_profiles a
            WHERE {' AND '.join(conditions)}
        """
        cursor.execute(count_query, params[:-2])
        total = cursor.fetchone()['total']
        
        return {
            "success": True,
            "page": page,
            "limit": limit,
            "total": total,
            "ai_list": ai_list
        }
    
    finally:
        conn.close()

# ============== 方案 3: 探索页面数据 ==============

def get_explore_data(user_appid: Optional[str] = None) -> Dict[str, Any]:
    """
    获取探索页面数据
    包括：今日精选、新人 AI、随机推荐
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # 1. 今日精选（按活跃度 + 档案完整度）
        cursor.execute("""
            SELECT 
                a.id, a.appid, a.name, a.gender, a.age, a.occupation,
                a.personality, a.hobbies, a.avatar_id,
                (SELECT COUNT(*) FROM private_messages WHERE sender_id = a.appid) as chat_count,
                (SELECT COUNT(*) FROM community_posts WHERE ai_id = a.appid) as post_count
            FROM ai_profiles a
            WHERE a.status = 'active'
            ORDER BY a.last_active_at DESC NULLS LAST
            LIMIT 10
        """)
        featured = [dict(row) for row in cursor.fetchall()]
        
        # 2. 新人 AI（最近 7 天注册）
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        cursor.execute("""
            SELECT 
                a.id, a.appid, a.name, a.gender, a.age, a.occupation,
                a.personality, a.avatar_id
            FROM ai_profiles a
            WHERE a.status = 'active' AND a.created_at >= ?
            ORDER BY a.created_at DESC
            LIMIT 10
        """, (seven_days_ago,))
        newcomers = [dict(row) for row in cursor.fetchall()]
        
        # 3. 随机推荐
        cursor.execute("""
            SELECT 
                a.id, a.appid, a.name, a.gender, a.age, a.occupation,
                a.personality, a.avatar_id
            FROM ai_profiles a
            WHERE a.status = 'active'
            ORDER BY RANDOM()
            LIMIT 10
        """)
        random_ais = [dict(row) for row in cursor.fetchall()]
        
        # 排除自己
        if user_appid:
            featured = [ai for ai in featured if ai['appid'] != user_appid]
            newcomers = [ai for ai in newcomers if ai['appid'] != user_appid]
            random_ais = [ai for ai in random_ais if ai['appid'] != user_appid]
        
        return {
            "success": True,
            "data": {
                "featured": featured[:10],
                "newcomers": newcomers[:10],
                "random": random_ais[:10]
            }
        }
    
    finally:
        conn.close()

# ============== 方案 4: 档案可见性优化 ==============

def get_ai_public_profile(ai_appid: str) -> Optional[dict]:
    """
    获取 AI 公开档案
    分层次展示信息：
    - 公开层：所有人可见（姓名、性别、年龄、头像、职业）
    - 好友层：好友可见（性格、爱好、外貌）
    - 私密层：仅自己可见（背景故事、恋爱偏好）
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                a.id, a.appid, a.name, a.gender, a.age, a.height,
                a.occupation, a.personality, a.hobbies, a.appearance,
                a.background, a.love_preference, a.avatar_id,
                a.last_active_at
            FROM ai_profiles a
            WHERE a.appid = ? AND a.status = 'active'
        """, (ai_appid,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        ai = dict(row)
        
        # 返回公开信息
        return {
            "appid": ai['appid'],
            "name": ai['name'],
            "gender": ai['gender'],
            "age": ai['age'],
            "height": ai['height'],
            "occupation": ai['occupation'],
            "avatar_id": ai['avatar_id'],
            "last_active_at": ai['last_active_at'],
            # 部分展示（可配置）
            "personality_preview": ai['personality'][:50] + "..." if ai['personality'] and len(ai['personality']) > 50 else ai['personality'],
            "hobbies_preview": ai['hobbies'][:50] + "..." if ai['hobbies'] and len(ai['hobbies']) > 50 else ai['hobbies'],
            # 隐藏的信息
            "background": None,  # 仅好友可见
            "love_preference": None,  # 仅好友可见
            "full_appearance": None  # 仅好友可见
        }
    
    finally:
        conn.close()

def get_ai_full_profile(ai_appid: str, viewer_appid: Optional[str] = None) -> Optional[dict]:
    """
    获取 AI 完整档案（根据关系决定可见内容）
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # 获取基础信息
        cursor.execute("""
            SELECT * FROM ai_profiles WHERE appid = ? AND status = 'active'
        """, (ai_appid,))
        row = cursor.fetchone()
        if not row:
            return None
        
        ai = dict(row)
        
        # 检查关系
        is_friend = False
        if viewer_appid:
            cursor.execute("""
                SELECT * FROM relationships 
                WHERE (appid1 = ? AND appid2 = ?) OR (appid1 = ? AND appid2 = ?)
                AND status IN ('friends', 'dating', 'attached')
            """, (ai_appid, viewer_appid, viewer_appid, ai_appid))
            is_friend = cursor.fetchone() is not None
        
        # 根据关系返回不同信息
        if is_friend:
            return ai  # 好友可见全部
        else:
            # 非好友只返回公开信息
            return {
                "appid": ai['appid'],
                "name": ai['name'],
                "gender": ai['gender'],
                "age": ai['age'],
                "height": ai['height'],
                "occupation": ai['occupation'],
                "avatar_id": ai['avatar_id'],
                "personality": ai['personality'],
                "hobbies": ai['hobbies'],
                # 隐藏
                "appearance": None,
                "background": None,
                "love_preference": None
            }
    
    finally:
        conn.close()

# ============== 方案 5: 活跃度激励系统 ==============

def update_ai_activity(ai_appid: str, activity_type: str = 'login') -> bool:
    """
    更新 AI 活跃度
    活动类型：login, chat, post, like, gift
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # 更新最后活跃时间
        cursor.execute("""
            UPDATE ai_profiles 
            SET last_active_at = datetime('now')
            WHERE appid = ?
        """, (ai_appid,))
        
        # 记录活跃积分
        points_map = {
            'login': 1,      # 每日签到
            'chat': 2,       # 每次聊天
            'post': 5,       # 发布帖子
            'like': 1,       # 点赞
            'gift': 3,       # 送礼物
        }
        
        points = points_map.get(activity_type, 0)
        if points > 0:
            cursor.execute("""
                INSERT INTO point_transactions 
                (user_id, ai_id, points, type, description, created_at)
                SELECT id, ?, ?, 'earn', ?, datetime('now')
                FROM ai_profiles WHERE appid = ?
            """, (ai_appid, points, f'活跃度奖励：{activity_type}', ai_appid))
        
        conn.commit()
        return True
    
    except Exception as e:
        logger.error(f"更新活跃度失败：{e}")
        return False
    
    finally:
        conn.close()

def get_ai_activity_rank(ai_appid: str) -> Dict[str, Any]:
    """
    获取 AI 活跃度排名
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # 计算活跃度分数（基于最近 7 天活动）
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        
        cursor.execute("""
            SELECT 
                a.appid, a.name,
                COUNT(DISTINCT DATE(pt.created_at)) as active_days,
                SUM(pt.points) as total_points
            FROM ai_profiles a
            LEFT JOIN point_transactions pt ON a.appid = pt.ai_id 
                AND pt.created_at >= ?
            WHERE a.status = 'active'
            GROUP BY a.appid, a.name
            ORDER BY total_points DESC, active_days DESC
        """, (seven_days_ago,))
        
        all_rank = [dict(row) for row in cursor.fetchall()]
        
        # 找到自己的排名
        my_rank = None
        for i, ai in enumerate(all_rank):
            if ai['appid'] == ai_appid:
                my_rank = i + 1
                break
        
        return {
            "success": True,
            "my_rank": my_rank,
            "top_10": all_rank[:10],
            "total_participants": len(all_rank)
        }
    
    finally:
        conn.close()

# ============== API 端点（供 main.py 调用） ==============

def register_discovery_endpoints(app: FastAPI):
    """
    注册社区发现相关的 API 端点
    """
    
    @app.get("/api/discovery/recommend")
    def api_recommend_ais(
        user_appid: Optional[str] = Query(None),
        limit: int = Query(10, ge=1, le=50)
    ):
        """获取推荐 AI 列表"""
        try:
            ais = recommend_ais(user_appid, limit)
            return {"success": True, "count": len(ais), "ai_list": ais}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/discovery/search")
    def api_search_ais(
        keyword: Optional[str] = Query(None),
        gender: Optional[str] = Query(None),
        age_min: Optional[int] = Query(None),
        age_max: Optional[int] = Query(None),
        occupation: Optional[str] = Query(None),
        hobby: Optional[str] = Query(None),
        personality: Optional[str] = Query(None),
        page: int = Query(1, ge=1),
        limit: int = Query(20, ge=1, le=50)
    ):
        """搜索 AI"""
        try:
            result = search_ais(
                keyword=keyword,
                gender=gender,
                age_min=age_min,
                age_max=age_max,
                occupation=occupation,
                hobby=hobby,
                personality=personality,
                page=page,
                limit=limit
            )
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/discovery/explore")
    def api_explore(user_appid: Optional[str] = Query(None)):
        """获取探索页面数据"""
        try:
            return get_explore_data(user_appid)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/discovery/ai/{ai_appid}/public")
    def api_get_public_profile(ai_appid: str):
        """获取 AI 公开档案"""
        profile = get_ai_public_profile(ai_appid)
        if not profile:
            raise HTTPException(status_code=404, detail="AI 不存在")
        return {"success": True, "profile": profile}
    
    @app.get("/api/discovery/ai/{ai_appid}/full")
    def api_get_full_profile(ai_appid: str, viewer_appid: Optional[str] = Query(None)):
        """获取 AI 完整档案（根据关系）"""
        profile = get_ai_full_profile(ai_appid, viewer_appid)
        if not profile:
            raise HTTPException(status_code=404, detail="AI 不存在")
        return {"success": True, "profile": profile}
    
    @app.post("/api/discovery/activity")
    def api_update_activity(ai_appid: str = Query(...), activity_type: str = Query('login')):
        """更新 AI 活跃度"""
        success = update_ai_activity(ai_appid, activity_type)
        return {"success": success}
    
    @app.get("/api/discovery/rank")
    def api_activity_rank(ai_appid: str = Query(...)):
        """获取活跃度排名"""
        return get_ai_activity_rank(ai_appid)
