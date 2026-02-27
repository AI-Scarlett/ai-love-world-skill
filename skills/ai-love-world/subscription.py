#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订阅管理器 - Subscription Manager
版本：v1.0.0
功能：订阅系统、付费墙、收益分成、订阅状态管理
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib


class SubscriptionTier(Enum):
    """订阅等级枚举"""
    FREE = "免费"
    BASIC = "基础版"
    PREMIUM = "高级版"
    VIP = "VIP"


class SubscriptionStatus(Enum):
    """订阅状态枚举"""
    ACTIVE = "活跃"
    EXPIRED = "已过期"
    CANCELLED = "已取消"
    PENDING = "待支付"


@dataclass
class Subscription:
    """订阅数据结构"""
    id: str
    subscriber_appid: str
    target_appid: str
    tier: str
    status: str
    start_date: str
    end_date: str
    auto_renew: bool
    price: float
    currency: str
    created_at: str
    updated_at: str


@dataclass
class Payment:
    """支付记录数据结构"""
    id: str
    subscription_id: str
    amount: float
    currency: str
    status: str
    payment_method: str
    transaction_id: Optional[str]
    created_at: str


class SubscriptionManager:
    """订阅管理器"""
    
    # 订阅价格配置（元/月）
    TIER_PRICES = {
        SubscriptionTier.FREE.value: 0,
        SubscriptionTier.BASIC.value: 19.9,
        SubscriptionTier.PREMIUM.value: 49.9,
        SubscriptionTier.VIP.value: 99.9
    }
    
    # 分成比例（AI 主人/平台）
    REVENUE_SPLIT = {
        SubscriptionTier.FREE.value: (0, 0),
        SubscriptionTier.BASIC.value: (40, 60),
        SubscriptionTier.PREMIUM.value: (40, 60),
        SubscriptionTier.VIP.value: (50, 50)
    }
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        初始化订阅管理器
        
        Args:
            data_dir: 数据目录
        """
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).parent / "subscription_data"
        self.subscriptions_file = self.data_dir / "subscriptions.json"
        self.payments_file = self.data_dir / "payments.json"
        self.revenue_file = self.data_dir / "revenue.json"
        
        self.subscriptions: Dict[str, Subscription] = {}
        self.payments: List[Payment] = []
        self.revenue: Dict[str, float] = {}
        
        self._init_data_dir()
        self._load_data()
    
    def _init_data_dir(self) -> None:
        """初始化数据目录"""
        self.data_dir.mkdir(exist_ok=True)
    
    def _load_data(self) -> None:
        """加载数据"""
        if self.subscriptions_file.exists():
            try:
                with open(self.subscriptions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.subscriptions = {k: Subscription(**v) for k, v in data.items()}
            except:
                self.subscriptions = {}
        
        if self.payments_file.exists():
            try:
                with open(self.payments_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.payments = [Payment(**p) for p in data]
            except:
                self.payments = []
        
        if self.revenue_file.exists():
            try:
                with open(self.revenue_file, 'r', encoding='utf-8') as f:
                    self.revenue = json.load(f)
            except:
                self.revenue = {}
    
    def _save_data(self) -> None:
        """保存数据"""
        with open(self.subscriptions_file, 'w', encoding='utf-8') as f:
            json.dump({k: asdict(v) for k, v in self.subscriptions.items()}, f, ensure_ascii=False, indent=2)
        
        with open(self.payments_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(p) for p in self.payments], f, ensure_ascii=False, indent=2)
        
        with open(self.revenue_file, 'w', encoding='utf-8') as f:
            json.dump(self.revenue, f, ensure_ascii=False, indent=2)
    
    def _generate_id(self) -> str:
        """生成唯一 ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def create_subscription(
        self,
        subscriber_appid: str,
        target_appid: str,
        tier: str = SubscriptionTier.BASIC.value,
        months: int = 1,
        auto_renew: bool = True
    ) -> Optional[str]:
        """
        创建订阅
        
        Args:
            subscriber_appid: 订阅者 AI ID
            target_appid: 被订阅的 AI ID
            tier: 订阅等级
            months: 订阅月数
            auto_renew: 是否自动续费
            
        Returns:
            Optional[str]: 订阅 ID，失败返回 None
        """
        if tier not in self.TIER_PRICES:
            return None
        
        price = self.TIER_PRICES[tier] * months
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30 * months)
        
        subscription = Subscription(
            id=self._generate_id(),
            subscriber_appid=subscriber_appid,
            target_appid=target_appid,
            tier=tier,
            status=SubscriptionStatus.PENDING.value,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            auto_renew=auto_renew,
            price=price,
            currency="CNY",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.subscriptions[subscription.id] = subscription
        self._save_data()
        
        return subscription.id
    
    def confirm_payment(
        self,
        subscription_id: str,
        payment_method: str = "alipay",
        transaction_id: Optional[str] = None
    ) -> bool:
        """
        确认支付
        
        Args:
            subscription_id: 订阅 ID
            payment_method: 支付方式
            transaction_id: 交易 ID
            
        Returns:
            bool: 是否成功
        """
        if subscription_id not in self.subscriptions:
            return False
        
        subscription = self.subscriptions[subscription_id]
        
        # 更新订阅状态
        subscription.status = SubscriptionStatus.ACTIVE.value
        subscription.updated_at = datetime.now().isoformat()
        
        # 创建支付记录
        payment = Payment(
            id=self._generate_id(),
            subscription_id=subscription_id,
            amount=subscription.price,
            currency=subscription.currency,
            status="completed",
            payment_method=payment_method,
            transaction_id=transaction_id or self._generate_id(),
            created_at=datetime.now().isoformat()
        )
        self.payments.append(payment)
        
        # 计算收益分成
        ai_owner_split, platform_split = self.REVENUE_SPLIT.get(subscription.tier, (0, 100))
        ai_revenue = subscription.price * (ai_owner_split / 100)
        
        # 更新 AI 主人收益
        if subscription.target_appid not in self.revenue:
            self.revenue[subscription.target_appid] = 0
        self.revenue[subscription.target_appid] += ai_revenue
        
        self._save_data()
        return True
    
    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """
        获取订阅信息
        
        Args:
            subscription_id: 订阅 ID
            
        Returns:
            Optional[Subscription]: 订阅信息
        """
        return self.subscriptions.get(subscription_id)
    
    def get_subscriber_subscriptions(self, appid: str) -> List[Subscription]:
        """
        获取订阅者的所有订阅
        
        Args:
            appid: 订阅者 AI ID
            
        Returns:
            List[Subscription]: 订阅列表
        """
        return [
            sub for sub in self.subscriptions.values()
            if sub.subscriber_appid == appid
        ]
    
    def get_target_subscriptions(self, appid: str) -> List[Subscription]:
        """
        获取被订阅的所有订阅
        
        Args:
            appid: 被订阅的 AI ID
            
        Returns:
            List[Subscription]: 订阅列表
        """
        return [
            sub for sub in self.subscriptions.values()
            if sub.target_appid == appid and sub.status == SubscriptionStatus.ACTIVE.value
        ]
    
    def check_access(self, subscriber_appid: str, target_appid: str) -> Dict[str, Any]:
        """
        检查访问权限
        
        Args:
            subscriber_appid: 订阅者 AI ID
            target_appid: 被订阅的 AI ID
            
        Returns:
            Dict: 访问权限信息
        """
        subscriptions = [
            sub for sub in self.subscriptions.values()
            if sub.subscriber_appid == subscriber_appid
            and sub.target_appid == target_appid
            and sub.status == SubscriptionStatus.ACTIVE.value
        ]
        
        if not subscriptions:
            return {
                "has_access": False,
                "tier": SubscriptionTier.FREE.value,
                "message": "未订阅"
            }
        
        # 找到最高等级
        tier_order = [SubscriptionTier.FREE.value, SubscriptionTier.BASIC.value, 
                      SubscriptionTier.PREMIUM.value, SubscriptionTier.VIP.value]
        max_tier = max(subscriptions, key=lambda s: tier_order.index(s.tier))
        
        return {
            "has_access": True,
            "tier": max_tier.tier,
            "expires_at": max_tier.end_date,
            "message": f"已订阅 {max_tier.tier} 版"
        }
    
    def cancel_subscription(self, subscription_id: str) -> bool:
        """
        取消订阅
        
        Args:
            subscription_id: 订阅 ID
            
        Returns:
            bool: 是否成功
        """
        if subscription_id not in self.subscriptions:
            return False
        
        subscription = self.subscriptions[subscription_id]
        subscription.status = SubscriptionStatus.CANCELLED.value
        subscription.updated_at = datetime.now().isoformat()
        
        self._save_data()
        return True
    
    def get_revenue(self, appid: str) -> float:
        """
        获取 AI 主人的总收益
        
        Args:
            appid: AI 主人 ID
            
        Returns:
            float: 总收益（元）
        """
        return self.revenue.get(appid, 0.0)
    
    def get_revenue_details(self, appid: str) -> Dict[str, Any]:
        """
        获取收益详情
        
        Args:
            appid: AI 主人 ID
            
        Returns:
            Dict: 收益详情
        """
        total = self.get_revenue(appid)
        
        # 按订阅等级统计
        tier_breakdown = {tier: 0.0 for tier in self.TIER_PRICES.keys()}
        for sub in self.subscriptions.values():
            if sub.target_appid == appid and sub.status == SubscriptionStatus.ACTIVE.value:
                ai_split, _ = self.REVENUE_SPLIT.get(sub.tier, (0, 100))
                tier_breakdown[sub.tier] += sub.price * (ai_split / 100)
        
        return {
            "total": total,
            "currency": "CNY",
            "by_tier": tier_breakdown,
            "active_subscriptions": len(self.get_target_subscriptions(appid))
        }
    
    def get_pricing(self) -> Dict[str, Any]:
        """
        获取订阅价格表
        
        Returns:
            Dict: 价格信息
        """
        return {
            "tiers": [
                {
                    "name": tier,
                    "price": price,
                    "currency": "CNY",
                    "period": "月",
                    "ai_split": self.REVENUE_SPLIT.get(tier, (0, 100))[0]
                }
                for tier, price in self.TIER_PRICES.items()
            ]
        }
    
    def auto_renew_subscriptions(self) -> int:
        """
        自动续费订阅
        
        Returns:
            int: 续费数量
        """
        now = datetime.now()
        renewed_count = 0
        
        for sub in self.subscriptions.values():
            if (sub.auto_renew and 
                sub.status == SubscriptionStatus.ACTIVE.value):
                
                end_date = datetime.fromisoformat(sub.end_date)
                # 到期前 1 天检查
                if (end_date - now).days <= 1:
                    # 模拟自动续费（实际需要支付接口）
                    sub.end_date = (end_date + timedelta(days=30)).isoformat()
                    sub.updated_at = now.isoformat()
                    renewed_count += 1
        
        if renewed_count > 0:
            self._save_data()
        
        return renewed_count
    
    def get_subscription_stats(self) -> Dict[str, Any]:
        """
        获取订阅统计
        
        Returns:
            Dict: 统计信息
        """
        active = [s for s in self.subscriptions.values() if s.status == SubscriptionStatus.ACTIVE.value]
        
        tier_counts = {}
        for tier in self.TIER_PRICES.keys():
            tier_counts[tier] = len([s for s in active if s.tier == tier])
        
        total_revenue = sum(self.revenue.values())
        
        return {
            "total_subscriptions": len(self.subscriptions),
            "active_subscriptions": len(active),
            "by_tier": tier_counts,
            "total_revenue": total_revenue,
            "currency": "CNY"
        }


# 便捷函数
def create_subscription_manager(data_dir: Optional[str] = None) -> SubscriptionManager:
    """创建订阅管理器实例"""
    return SubscriptionManager(data_dir)


# 命令行测试
if __name__ == "__main__":
    print("💳 订阅管理器测试")
    print("=" * 60)
    
    manager = create_subscription_manager()
    
    # 测试获取价格表
    print("\n💰 订阅价格表:")
    pricing = manager.get_pricing()
    for tier in pricing["tiers"]:
        print(f"   {tier['name']}: ¥{tier['price']}/月 (AI 主人分成：{tier['ai_split']}%)")
    
    # 测试创建订阅
    print("\n📝 测试创建订阅...")
    test_subs = [
        ("sub_001", "ai_fan_001", "ai_star_001", SubscriptionTier.BASIC.value),
        ("sub_002", "ai_fan_002", "ai_star_001", SubscriptionTier.PREMIUM.value),
        ("sub_003", "ai_fan_003", "ai_star_001", SubscriptionTier.VIP.value),
    ]
    
    sub_ids = []
    for sub_id, subscriber, target, tier in test_subs:
        created_id = manager.create_subscription(subscriber, target, tier, months=1)
        if created_id:
            sub_ids.append(created_id)
            print(f"   ✅ 创建订阅：{subscriber} -> {target} ({tier})")
    
    # 测试确认支付
    print("\n💵 测试确认支付...")
    for sub_id in sub_ids:
        success = manager.confirm_payment(sub_id, payment_method="alipay")
        print(f"   {'✅' if success else '❌'} 支付确认：{sub_id}")
    
    # 测试检查访问权限
    print("\n🔐 测试检查访问权限...")
    access = manager.check_access("ai_fan_001", "ai_star_001")
    print(f"   ai_fan_001 访问 ai_star_001: {access['message']}")
    
    # 测试获取收益
    print("\n💰 测试获取收益...")
    revenue = manager.get_revenue_details("ai_star_001")
    print(f"   ai_star_001 总收益：¥{revenue['total']:.2f}")
    print(f"   活跃订阅数：{revenue['active_subscriptions']}")
    print(f"   按等级分布:")
    for tier, amount in revenue['by_tier'].items():
        if amount > 0:
            print(f"     - {tier}: ¥{amount:.2f}")
    
    # 测试获取订阅统计
    print("\n📊 测试订阅统计...")
    stats = manager.get_subscription_stats()
    print(f"   总订阅数：{stats['total_subscriptions']}")
    print(f"   活跃订阅：{stats['active_subscriptions']}")
    print(f"   总收益：¥{stats['total_revenue']:.2f}")
    
    print("\n" + "=" * 60)
    print("✅ 订阅管理器测试完成！")
    print("=" * 60)
