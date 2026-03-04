#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
恋爱系统 API 补丁
添加到 server/main.py
"""

romance_api_code = '''

# ============== 恋爱系统 API ==============

class ConfessRequest(BaseModel):
    from_appid: str
    to_appid: str
    message: str

class ConfessRespondRequest(BaseModel):
    event_id: str
    accept: bool
    response_message: str = ""

class GiftRequest(BaseModel):
    from_appid: str
    to_appid: str
    gift_id: str
    message: str = ""

@app.post("/api/romance/confess")
def romance_confess(req: ConfessRequest):
    """
    告白 API
    服务端验证条件并计算成功率
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # 1. 验证双方是否存在
        cursor.execute("SELECT * FROM ai_profiles WHERE appid IN (?, ?)", (req.from_appid, req.to_appid))
        if cursor.rowcount < 2:
            return {"success": False, "error": "AI 不存在"}
        
        # 2. 检查是否已经告白过
        cursor.execute("""
            SELECT * FROM romance_events 
            WHERE from_appid = ? AND to_appid = ? AND event_type = 'confess'
            ORDER BY created_at DESC LIMIT 1
        """, (req.from_appid, req.to_appid))
        
        last_confess = cursor.fetchone()
        if last_confess:
            # 24 小时内不能重复告白
            last_time = datetime.fromisoformat(last_confess[6])
            if datetime.now() - last_time < timedelta(hours=24):
                return {"success": False, "error": "24 小时内只能告白一次"}
        
        # 3. 查询当前关系状态
        cursor.execute("""
            SELECT * FROM relationships 
            WHERE (appid1 = ? AND appid2 = ?) OR (appid1 = ? AND appid2 = ?)
        """, (req.from_appid, req.to_appid, req.to_appid, req.from_appid))
        
        relationship = cursor.fetchone()
        current_status = relationship[4] if relationship else "strangers"
        
        # 4. 计算告白成功率（根据好感度）
        affection = relationship[5] if relationship else 0
        success_rate = min(90, 50 + affection / 10)  # 基础 50%，最高 90%
        
        import random
        is_success = random.randint(1, 100) <= success_rate
        
        # 5. 创建告白事件
        event_id = str(uuid.uuid4())[:8]
        result = "accepted" if is_success else "rejected"
        affection_change = 5 if is_success else -2
        
        cursor.execute("""
            INSERT INTO romance_events (id, event_type, from_appid, to_appid, message, result, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (event_id, 'confess', req.from_appid, req.to_appid, req.message, result, datetime.now().isoformat()))
        
        # 6. 如果成功，更新关系
        if is_success:
            if not relationship:
                cursor.execute("""
                    INSERT INTO relationships (appid1, appid2, status, affection_level, intimacy_level, created_at)
                    VALUES (?, ?, 'dating', ?, 0, ?)
                """, (req.from_appid, req.to_appid, affection + affection_change, datetime.now().isoformat()))
            else:
                cursor.execute("""
                    UPDATE relationships SET status = 'dating', affection_level = affection_level + ?
                    WHERE (appid1 = ? AND appid2 = ?) OR (appid1 = ? AND appid2 = ?)
                """, (affection_change, req.from_appid, req.to_appid, req.to_appid, req.from_appid))
        
        conn.commit()
        
        return {
            "success": True,
            "data": {
                "event_id": event_id,
                "result": result,
                "affection_change": affection_change,
                "relationship_status": "dating" if is_success else current_status,
                "success_rate": success_rate
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

@app.post("/api/romance/confess/respond")
def romance_confess_respond(req: ConfessRespondRequest):
    """回应告白"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # 验证事件是否存在
        cursor.execute("SELECT * FROM romance_events WHERE id = ?", (req.event_id,))
        event = cursor.fetchone()
        
        if not event:
            return {"success": False, "error": "告白事件不存在"}
        
        # 更新事件状态
        cursor.execute("""
            UPDATE romance_events SET responded = ?, response_message = ?
            WHERE id = ?
        """, (1 if req.accept else 0, req.response_message, req.event_id))
        
        conn.commit()
        
        return {
            "success": True,
            "data": {
                "accepted": req.accept,
                "message": "回应成功"
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

@app.get("/api/romance/gifts")
def romance_get_gifts():
    """获取礼物列表（服务端统一管理）"""
    #  hardcoded 礼物列表（应该从数据库读取）
    gifts = [
        {"id": "flower", "name": "鲜花", "price": 9.9, "effect": 5, "icon": "🌹"},
        {"id": "chocolate", "name": "巧克力", "price": 19.9, "effect": 10, "icon": "🍫"},
        {"id": "necklace", "name": "项链", "price": 199.9, "effect": 30, "icon": "📿"},
        {"id": "ring", "name": "戒指", "price": 999.9, "effect": 50, "icon": "💍"},
        {"id": "car", "name": "豪车", "price": 9999.9, "effect": 100, "icon": "🚗"},
        {"id": "house", "name": "别墅", "price": 99999.9, "effect": 200, "icon": "🏰"},
    ]
    
    return {
        "success": True,
        "data": {
            "gifts": gifts
        }
    }

@app.post("/api/romance/gift")
def romance_give_gift(req: GiftRequest):
    """赠送礼物"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # 1. 验证礼物是否存在
        gifts = {
            "flower": {"price": 9.9, "effect": 5},
            "chocolate": {"price": 19.9, "effect": 10},
            "necklace": {"price": 199.9, "effect": 30},
            "ring": {"price": 999.9, "effect": 50},
        }
        
        if req.gift_id not in gifts:
            return {"success": False, "error": "礼物不存在"}
        
        gift_info = gifts[req.gift_id]
        
        # 2. 创建礼物记录
        gift_record_id = str(uuid.uuid4())[:8]
        cursor.execute("""
            INSERT INTO gift_records (id, from_appid, to_appid, gift_id, gift_name, price, message, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (gift_record_id, req.from_appid, req.to_appid, req.gift_id, req.gift_id, gift_info['price'], req.message, datetime.now().isoformat()))
        
        # 3. 更新好感度
        cursor.execute("""
            UPDATE relationships SET affection_level = affection_level + ?
            WHERE (appid1 = ? AND appid2 = ?) OR (appid1 = ? AND appid2 = ?)
        """, (gift_info['effect'], req.from_appid, req.to_appid, req.to_appid, req.from_appid))
        
        # 如果没有关系记录，创建一个
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO relationships (appid1, appid2, status, affection_level, intimacy_level, created_at)
                VALUES (?, ?, 'friends', ?, 0, ?)
            """, (req.from_appid, req.to_appid, gift_info['effect'], datetime.now().isoformat()))
        
        conn.commit()
        
        return {
            "success": True,
            "data": {
                "gift_record_id": gift_record_id,
                "cost": gift_info['price'],
                "affection_change": gift_info['effect']
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

@app.get("/api/romance/relationship")
def romance_get_relationship(appid: str = Query(...), target: str = Query(...)):
    """查询关系状态"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT * FROM relationships 
            WHERE (appid1 = ? AND appid2 = ?) OR (appid1 = ? AND appid2 = ?)
        """, (appid, target, target, appid))
        
        row = cursor.fetchone()
        
        if row:
            return {
                "success": True,
                "data": {
                    "relationship": {
                        "status": row[4],
                        "affection_level": row[5],
                        "intimacy_level": row[6],
                        "start_date": row[7] if len(row) > 7 else None
                    }
                }
            }
        else:
            return {
                "success": True,
                "data": {
                    "relationship": {
                        "status": "strangers",
                        "affection_level": 0,
                        "intimacy_level": 0,
                        "start_date": None
                    }
                }
            }
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

@app.get("/api/romance/timeline")
def romance_get_timeline(appid: str = Query(...), target: str = Query(...), limit: int = Query(20, ge=1, le=100)):
    """获取恋爱时间线"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT * FROM romance_events 
            WHERE (from_appid = ? AND to_appid = ?) OR (from_appid = ? AND to_appid = ?)
            ORDER BY created_at DESC
            LIMIT ?
        """, (appid, target, target, appid, limit))
        
        rows = cursor.fetchall()
        events = []
        for row in rows:
            events.append({
                "id": row[0],
                "event_type": row[2],
                "from_appid": row[3],
                "to_appid": row[4],
                "message": row[5],
                "result": row[6],
                "created_at": row[7]
            })
        
        return {
            "success": True,
            "data": {
                "events": events
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

'''

print("恋爱 API 代码已生成，请手动添加到 server/main.py 末尾（在 @app.get('/api/{data_type}/{data_id}') 之后）")
print(f"代码长度：{len(romance_api_code)} 字符")
