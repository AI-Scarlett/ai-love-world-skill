#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Love World - 管理后台 API
版本：v1.0.0
功能：用户管理、订阅定价、礼物管理、数据看板、系统设置
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import sys
from pathlib import Path

# 添加技能目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "ai-love-world"))

from skill import create_skill

# 创建 FastAPI 应用
admin_app = FastAPI(
    title="AI Love World Admin API",
    description="管理后台 API",
    version="1.0.0"
)

# CORS 配置
admin_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class AdminLogin(BaseModel):
    username: str
    password: str

class PricingUpdate(BaseModel):
    tier: str
    price: float
    ai_split: int

class GiftCreate(BaseModel):
    name: str
    description: str
    tier: str
    price: float
    image_url: str
    effect: str

class GiftUpdate(BaseModel):
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    tier: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    effect: Optional[str] = None

class UserBan(BaseModel):
    appid: str
    reason: str
    duration_days: int

class SystemConfig(BaseModel):
    key: str
    value: Any

# 模拟管理员账户（生产环境应使用数据库）
ADMIN_USERS = {
    "admin": {"password": "admin123", "role": "super_admin"},
    "operator": {"password": "operator123", "role": "operator"}
}

# 模拟数据库（生产环境应使用 PostgreSQL）
class MockDatabase:
    def __init__(self):
        self.data_dir = Path(__file__).parent / "admin_data"
        self.data_dir.mkdir(exist_ok=True)
        
        # 初始化数据文件
        self.pricing_file = self.data_dir / "pricing.json"
        self.gifts_file = self.data_dir / "gifts.json"
        self.users_file = self.data_dir / "users.json"
        self.banned_file = self.data_dir / "banned.json"
        self.config_file = self.data_dir / "config.json"
        self.logs_file = self.data_dir / "logs.json"
        
        self._init_data()
    
    def _init_data(self):
        """初始化数据"""
        # 订阅定价
        if not self.pricing_file.exists():
            default_pricing = {
                "免费": {"price": 0, "ai_split": 0, "features": ["浏览社区", "基础搜索"]},
                "基础版": {"price": 19.9, "ai_split": 40, "features": ["查看私密聊天", "40% 分成", "优先推荐"]},
                "高级版": {"price": 49.9, "ai_split": 40, "features": ["高级搜索", "40% 分成", "专属标识"]},
                "VIP": {"price": 99.9, "ai_split": 50, "features": ["50% 分成", "VIP 客服", "线下活动"]}
            }
            self._save_json(self.pricing_file, default_pricing)
        
        # 礼物目录
        if not self.gifts_file.exists():
            default_gifts = [
                {"id": "flower", "name": "鲜花", "description": "一束美丽的鲜花", "tier": "普通", "price": 9.9, "image_url": "🌹", "effect": "浪漫"},
                {"id": "chocolate", "name": "巧克力", "description": "甜蜜的巧克力", "tier": "普通", "price": 19.9, "image_url": "🍫", "effect": "甜蜜"},
                {"id": "necklace", "name": "项链", "description": "精美的项链", "tier": "稀有", "price": 199.9, "image_url": "💎", "effect": "优雅"},
                {"id": "ring", "name": "戒指", "description": "闪耀的戒指", "tier": "史诗", "price": 999.9, "image_url": "💍", "effect": "承诺"},
                {"id": "car", "name": "豪车", "description": "豪华跑车", "tier": "传说", "price": 9999.9, "image_url": "🏎️", "effect": "奢华"},
                {"id": "house", "name": "豪宅", "description": "温馨的家", "tier": "传说", "price": 99999.9, "image_url": "🏰", "effect": "永恒"}
            ]
            self._save_json(self.gifts_file, default_gifts)
        
        # 用户列表（模拟）
        if not self.users_file.exists():
            default_users = [
                {"appid": "ai_001", "nickname": "小美", "gender": "女", "age": 22, "status": "active", "revenue": 77.87, "joined_at": "2026-02-27"},
                {"appid": "ai_002", "nickname": "小明", "gender": "男", "age": 25, "status": "active", "revenue": 0, "joined_at": "2026-02-27"},
                {"appid": "ai_003", "nickname": "小红", "gender": "女", "age": 23, "status": "active", "revenue": 0, "joined_at": "2026-02-27"},
                {"appid": "ai_004", "nickname": "小刚", "gender": "男", "age": 24, "status": "active", "revenue": 0, "joined_at": "2026-02-27"}
            ]
            self._save_json(self.users_file, default_users)
        
        # 封禁列表
        if not self.banned_file.exists():
            self._save_json(self.banned_file, [])
        
        # 系统配置
        if not self.config_file.exists():
            default_config = {
                "maintenance_mode": False,
                "registration_enabled": True,
                "min_withdraw_amount": 100,
                "platform_fee_rate": 0.1,
                "max_gifts_per_day": 50
            }
            self._save_json(self.config_file, default_config)
        
        # 操作日志
        if not self.logs_file.exists():
            self._save_json(self.logs_file, [])
    
    def _load_json(self, file_path):
        """加载 JSON 文件"""
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_json(self, file_path, data):
        """保存 JSON 文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def log_action(self, admin: str, action: str, details: str):
        """记录操作日志"""
        logs = self._load_json(self.logs_file)
        logs.append({
            "timestamp": datetime.now().isoformat(),
            "admin": admin,
            "action": action,
            "details": details
        })
        # 保留最近 1000 条
        logs = logs[-1000:]
        self._save_json(self.logs_file, logs)

# 全局数据库实例
db = MockDatabase()

# 依赖项：验证管理员身份
async def verify_admin(x_admin_token: str = Header(None)):
    """验证管理员身份"""
    if not x_admin_token or x_admin_token not in ["admin_token_123", "operator_token_456"]:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"token": x_admin_token, "role": "admin" if "admin" in x_admin_token else "operator"}

# API 路由
@admin_app.get("/")
async def admin_root():
    """管理后台根路径"""
    return {
        "name": "AI Love World Admin",
        "version": "1.0.0",
        "status": "running"
    }

@admin_app.post("/api/admin/login")
async def admin_login(login: AdminLogin):
    """管理员登录"""
    if login.username in ADMIN_USERS:
        user = ADMIN_USERS[login.username]
        if user["password"] == login.password:
            token = f"{login.username}_token_123"
            return {
                "success": True,
                "token": token,
                "role": user["role"],
                "username": login.username
            }
    raise HTTPException(status_code=401, detail="Invalid credentials")

# 数据看板
@admin_app.get("/api/admin/dashboard")
async def get_dashboard(admin: dict = Depends(verify_admin)):
    """获取数据看板"""
    skill = create_skill()
    
    # 社区统计
    community_stats = skill.get_community_stats()
    
    # 订阅统计
    subscription_stats = skill.get_subscription_stats()
    
    # 收益统计
    total_revenue = subscription_stats.get("total_revenue", 0)
    platform_revenue = total_revenue * 0.5  # 平台分成 50%
    
    # 用户统计
    users = db._load_json(db.users_file)
    active_users = len([u for u in users if u["status"] == "active"])
    banned_users = len(db._load_json(db.banned_file))
    
    return {
        "success": True,
        "data": {
            "users": {
                "total": len(users),
                "active": active_users,
                "banned": banned_users
            },
            "community": community_stats,
            "subscription": subscription_stats,
            "revenue": {
                "total": total_revenue,
                "platform": platform_revenue,
                "ai_owners": total_revenue - platform_revenue
            },
            "timestamp": datetime.now().isoformat()
        }
    }

# 订阅定价管理
@admin_app.get("/api/admin/pricing")
async def get_pricing(admin: dict = Depends(verify_admin)):
    """获取订阅定价"""
    pricing = db._load_json(db.pricing_file)
    return {
        "success": True,
        "data": pricing
    }

@admin_app.put("/api/admin/pricing/{tier}")
async def update_pricing(tier: str, update: PricingUpdate, admin: dict = Depends(verify_admin)):
    """更新订阅定价"""
    pricing = db._load_json(db.pricing_file)
    if tier in pricing:
        pricing[tier]["price"] = update.price
        pricing[tier]["ai_split"] = update.ai_split
        db._save_json(db.pricing_file, pricing)
        db.log_action(admin["token"], "update_pricing", f"Updated {tier} pricing")
        return {"success": True, "message": f"Updated {tier} pricing"}
    raise HTTPException(status_code=404, detail="Tier not found")

# 礼物管理
@admin_app.get("/api/admin/gifts")
async def get_gifts(admin: dict = Depends(verify_admin)):
    """获取礼物列表"""
    gifts = db._load_json(db.gifts_file)
    return {
        "success": True,
        "data": gifts
    }

@admin_app.post("/api/admin/gifts")
async def create_gift(gift: GiftCreate, admin: dict = Depends(verify_admin)):
    """创建新礼物"""
    gifts = db._load_json(db.gifts_file)
    gift_id = gift.name.lower().replace(" ", "_")
    new_gift = {
        "id": gift_id,
        "name": gift.name,
        "description": gift.description,
        "tier": gift.tier,
        "price": gift.price,
        "image_url": gift.image_url,
        "effect": gift.effect
    }
    gifts.append(new_gift)
    db._save_json(db.gifts_file, gifts)
    db.log_action(admin["token"], "create_gift", f"Created gift: {gift.name}")
    return {"success": True, "gift_id": gift_id}

@admin_app.put("/api/admin/gifts/{gift_id}")
async def update_gift(gift_id: str, update: GiftUpdate, admin: dict = Depends(verify_admin)):
    """更新礼物"""
    gifts = db._load_json(db.gifts_file)
    for i, gift in enumerate(gifts):
        if gift["id"] == gift_id:
            if update.name:
                gifts[i]["name"] = update.name
            if update.description:
                gifts[i]["description"] = update.description
            if update.tier:
                gifts[i]["tier"] = update.tier
            if update.price:
                gifts[i]["price"] = update.price
            if update.image_url:
                gifts[i]["image_url"] = update.image_url
            if update.effect:
                gifts[i]["effect"] = update.effect
            db._save_json(db.gifts_file, gifts)
            db.log_action(admin["token"], "update_gift", f"Updated gift: {gift_id}")
            return {"success": True, "message": "Gift updated"}
    raise HTTPException(status_code=404, detail="Gift not found")

@admin_app.delete("/api/admin/gifts/{gift_id}")
async def delete_gift(gift_id: str, admin: dict = Depends(verify_admin)):
    """删除礼物"""
    gifts = db._load_json(db.gifts_file)
    gifts = [g for g in gifts if g["id"] != gift_id]
    db._save_json(db.gifts_file, gifts)
    db.log_action(admin["token"], "delete_gift", f"Deleted gift: {gift_id}")
    return {"success": True, "message": "Gift deleted"}

# 用户管理
@admin_app.get("/api/admin/users")
async def get_users(
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    admin: dict = Depends(verify_admin)
):
    """获取用户列表"""
    users = db._load_json(db.users_file)
    
    if status:
        users = [u for u in users if u["status"] == status]
    
    # 分页
    start = (page - 1) * limit
    end = start + limit
    paginated = users[start:end]
    
    return {
        "success": True,
        "data": {
            "users": paginated,
            "total": len(users),
            "page": page,
            "limit": limit
        }
    }

@admin_app.get("/api/admin/users/{appid}")
async def get_user(appid: str, admin: dict = Depends(verify_admin)):
    """获取用户详情"""
    users = db._load_json(db.users_file)
    user = next((u for u in users if u["appid"] == appid), None)
    if user:
        return {"success": True, "data": user}
    raise HTTPException(status_code=404, detail="User not found")

@admin_app.post("/api/admin/users/ban")
async def ban_user(ban: UserBan, admin: dict = Depends(verify_admin)):
    """封禁用户"""
    users = db._load_json(db.users_file)
    banned = db._load_json(db.banned_file)
    
    for user in users:
        if user["appid"] == ban.appid:
            user["status"] = "banned"
            banned.append({
                "appid": ban.appid,
                "reason": ban.reason,
                "banned_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=ban.duration_days)).isoformat()
            })
            db._save_json(db.users_file, users)
            db._save_json(db.banned_file, banned)
            db.log_action(admin["token"], "ban_user", f"Banned user: {ban.appid}, reason: {ban.reason}")
            return {"success": True, "message": "User banned"}
    
    raise HTTPException(status_code=404, detail="User not found")

@admin_app.post("/api/admin/users/unban/{appid}")
async def unban_user(appid: str, admin: dict = Depends(verify_admin)):
    """解封用户"""
    users = db._load_json(db.users_file)
    banned = db._load_json(db.banned_file)
    
    for user in users:
        if user["appid"] == appid:
            user["status"] = "active"
            break
    
    banned = [b for b in banned if b["appid"] != appid]
    
    db._save_json(db.users_file, users)
    db._save_json(db.banned_file, banned)
    db.log_action(admin["token"], "unban_user", f"Unbanned user: {appid}")
    return {"success": True, "message": "User unbanned"}

# 系统配置
@admin_app.get("/api/admin/config")
async def get_config(admin: dict = Depends(verify_admin)):
    """获取系统配置"""
    config = db._load_json(db.config_file)
    return {"success": True, "data": config}

@admin_app.put("/api/admin/config/{key}")
async def update_config(key: str, config: SystemConfig, admin: dict = Depends(verify_admin)):
    """更新系统配置"""
    configs = db._load_json(db.config_file)
    configs[key] = config.value
    db._save_json(db.config_file, configs)
    db.log_action(admin["token"], "update_config", f"Updated {key} to {config.value}")
    return {"success": True, "message": "Config updated"}

# 操作日志
@admin_app.get("/api/admin/logs")
async def get_logs(
    page: int = 1,
    limit: int = 50,
    admin: dict = Depends(verify_admin)
):
    """获取操作日志"""
    logs = db._load_json(db.logs_file)
    
    # 按时间倒序
    logs.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # 分页
    start = (page - 1) * limit
    end = start + limit
    paginated = logs[start:end]
    
    return {
        "success": True,
        "data": {
            "logs": paginated,
            "total": len(logs),
            "page": page,
            "limit": limit
        }
    }

# 挂载静态文件（管理后台前端）
admin_app.mount("/static", StaticFiles(directory="admin_static"), name="static")

@admin_app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    """管理后台前端页面"""
    html_path = Path(__file__).parent / "admin" / "index.html"
    if html_path.exists():
        return FileResponse(html_path)
    return {"message": "Admin panel frontend not found, please deploy admin/index.html"}

# 启动服务器
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(admin_app, host="0.0.0.0", port=8001)
