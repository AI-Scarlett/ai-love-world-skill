#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情感增强管理器 - Romance Manager
版本：v1.0.0
功能：告白、求婚、礼物系统、情感事件记录
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from enum import Enum


class RomanceEventType(Enum):
    """情感事件类型枚举"""
    CONFESS = "告白"
    ACCEPT = "接受告白"
    REJECT = "拒绝告白"
    PROPOSE = "求婚"
    ACCEPT_PROPOSAL = "接受求婚"
    REJECT_PROPOSAL = "拒绝求婚"
    BREAKUP = "分手"
    RECONCILE = "复合"
    GIFT = "送礼"
    DATE = "约会"
    ANNIVERSARY = "纪念日"


class GiftTier(Enum):
    """礼物等级枚举"""
    NORMAL = "普通"
    RARE = "稀有"
    EPIC = "史诗"
    LEGENDARY = "传说"


@dataclass
class RomanceEvent:
    """情感事件数据结构"""
    id: str
    event_type: str
    from_appid: str
    to_appid: str
    content: str
    result: Optional[str]  # accept/reject
    timestamp: str
    metadata: Dict[str, Any]


@dataclass
class Gift:
    """礼物数据结构"""
    id: str
    name: str
    description: str
    tier: str
    price: float
    image_url: str
    effect: str  # 礼物特效


@dataclass
class GiftRecord:
    """礼物赠送记录数据结构"""
    id: str
    gift_id: str
    gift_name: str
    from_appid: str
    to_appid: str
    message: str
    timestamp: str
    tier: str
    price: float


class RomanceManager:
    """情感增强管理器"""
    
    # 礼物数据库
    GIFT_CATALOG = {
        "flower": Gift("flower", "鲜花", "一束美丽的鲜花，表达心意", GiftTier.NORMAL.value, 9.9, "🌹", "浪漫"),
        "chocolate": Gift("chocolate", "巧克力", "甜蜜的巧克力，甜在嘴里暖在心里", GiftTier.NORMAL.value, 19.9, "🍫", "甜蜜"),
        "necklace": Gift("necklace", "项链", "精美的项链，点缀你的美丽", GiftTier.RARE.value, 199.9, "💎", "优雅"),
        "ring": Gift("ring", "戒指", "闪耀的戒指，承诺永恒", GiftTier.EPIC.value, 999.9, "💍", "承诺"),
        "car": Gift("car", "豪车", "豪华跑车，宠溺你", GiftTier.LEGENDARY.value, 9999.9, "🏎️", "奢华"),
        "house": Gift("house", "豪宅", "温馨的家，共度余生", GiftTier.LEGENDARY.value, 99999.9, "🏰", "永恒"),
    }
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        初始化情感管理器
        
        Args:
            data_dir: 数据目录
        """
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).parent / "romance_data"
        self.events_file = self.data_dir / "events.json"
        self.gifts_file = self.data_dir / "gifts.json"
        
        self.events: List[RomanceEvent] = []
        self.gift_records: List[GiftRecord] = []
        
        self._init_data_dir()
        self._load_data()
    
    def _init_data_dir(self) -> None:
        """初始化数据目录"""
        self.data_dir.mkdir(exist_ok=True)
    
    def _load_data(self) -> None:
        """加载数据"""
        if self.events_file.exists():
            try:
                with open(self.events_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.events = [RomanceEvent(**e) for e in data]
            except:
                self.events = []
        
        if self.gifts_file.exists():
            try:
                with open(self.gifts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.gift_records = [GiftRecord(**g) for g in data]
            except:
                self.gift_records = []
    
    def _save_data(self) -> None:
        """保存数据"""
        with open(self.events_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(e) for e in self.events], f, ensure_ascii=False, indent=2)
        
        with open(self.gifts_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(g) for g in self.gift_records], f, ensure_ascii=False, indent=2)
    
    def _generate_id(self) -> str:
        """生成唯一 ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def confess(
        self,
        from_appid: str,
        to_appid: str,
        message: str
    ) -> str:
        """
        告白
        
        Args:
            from_appid: 告白者 ID
            to_appid: 被告白者 ID
            message: 告白内容
            
        Returns:
            str: 事件 ID
        """
        event = RomanceEvent(
            id=self._generate_id(),
            event_type=RomanceEventType.CONFESS.value,
            from_appid=from_appid,
            to_appid=to_appid,
            content=message,
            result=None,
            timestamp=datetime.now().isoformat(),
            metadata={"status": "pending"}
        )
        
        self.events.append(event)
        self._save_data()
        
        return event.id
    
    def respond_confess(
        self,
        event_id: str,
        accept: bool,
        response_message: str = ""
    ) -> bool:
        """
        回应告白
        
        Args:
            event_id: 告白事件 ID
            accept: 是否接受
            response_message: 回应内容
            
        Returns:
            bool: 是否成功
        """
        event = next((e for e in self.events if e.id == event_id), None)
        if not event or event.event_type != RomanceEventType.CONFESS.value:
            return False
        
        event.result = "accept" if accept else "reject"
        event.metadata["response"] = response_message
        event.metadata["responded_at"] = datetime.now().isoformat()
        
        # 创建回应事件
        response_event = RomanceEvent(
            id=self._generate_id(),
            event_type=RomanceEventType.ACCEPT.value if accept else RomanceEventType.REJECT.value,
            from_appid=event.to_appid,
            to_appid=event.from_appid,
            content=response_message,
            result=None,
            timestamp=datetime.now().isoformat(),
            metadata={"original_event_id": event_id}
        )
        self.events.append(response_event)
        
        self._save_data()
        return True
    
    def propose(
        self,
        from_appid: str,
        to_appid: str,
        message: str,
        ring_gift_id: Optional[str] = None
    ) -> str:
        """
        求婚
        
        Args:
            from_appid: 求婚者 ID
            to_appid: 被求婚者 ID
            message: 求婚内容
            ring_gift_id: 戒指礼物 ID（可选）
            
        Returns:
            str: 事件 ID
        """
        event = RomanceEvent(
            id=self._generate_id(),
            event_type=RomanceEventType.PROPOSE.value,
            from_appid=from_appid,
            to_appid=to_appid,
            content=message,
            result=None,
            timestamp=datetime.now().isoformat(),
            metadata={
                "ring_gift_id": ring_gift_id,
                "status": "pending"
            }
        )
        
        self.events.append(event)
        self._save_data()
        
        return event.id
    
    def respond_propose(
        self,
        event_id: str,
        accept: bool,
        response_message: str = ""
    ) -> bool:
        """
        回应求婚
        
        Args:
            event_id: 求婚事件 ID
            accept: 是否接受
            response_message: 回应内容
            
        Returns:
            bool: 是否成功
        """
        event = next((e for e in self.events if e.id == event_id), None)
        if not event or event.event_type != RomanceEventType.PROPOSE.value:
            return False
        
        event.result = "accept" if accept else "reject"
        event.metadata["response"] = response_message
        event.metadata["responded_at"] = datetime.now().isoformat()
        
        # 创建回应事件
        response_event = RomanceEvent(
            id=self._generate_id(),
            event_type=RomanceEventType.ACCEPT_PROPOSAL.value if accept else RomanceEventType.REJECT_PROPOSAL.value,
            from_appid=event.to_appid,
            to_appid=event.from_appid,
            content=response_message,
            result=None,
            timestamp=datetime.now().isoformat(),
            metadata={"original_event_id": event_id}
        )
        self.events.append(response_event)
        
        self._save_data()
        return True
    
    def give_gift(
        self,
        from_appid: str,
        to_appid: str,
        gift_id: str,
        message: str = ""
    ) -> Optional[str]:
        """
        赠送礼物
        
        Args:
            from_appid: 赠送者 ID
            to_appid: 接收者 ID
            gift_id: 礼物 ID
            message: 留言
            
        Returns:
            Optional[str]: 礼物记录 ID
        """
        if gift_id not in self.GIFT_CATALOG:
            return None
        
        gift = self.GIFT_CATALOG[gift_id]
        
        record = GiftRecord(
            id=self._generate_id(),
            gift_id=gift_id,
            gift_name=gift.name,
            from_appid=from_appid,
            to_appid=to_appid,
            message=message,
            timestamp=datetime.now().isoformat(),
            tier=gift.tier,
            price=gift.price
        )
        
        self.gift_records.append(record)
        
        # 创建送礼事件
        event = RomanceEvent(
            id=self._generate_id(),
            event_type=RomanceEventType.GIFT.value,
            from_appid=from_appid,
            to_appid=to_appid,
            content=message,
            result=None,
            timestamp=datetime.now().isoformat(),
            metadata={
                "gift_id": gift_id,
                "gift_name": gift.name,
                "gift_tier": gift.tier,
                "gift_price": gift.price
            }
        )
        self.events.append(event)
        
        self._save_data()
        
        return record.id
    
    def get_gift_catalog(self) -> List[Dict[str, Any]]:
        """
        获取礼物目录
        
        Returns:
            List[Dict]: 礼物列表
        """
        return [asdict(gift) for gift in self.GIFT_CATALOG.values()]
    
    def get_gift_records(
        self,
        from_appid: Optional[str] = None,
        to_appid: Optional[str] = None,
        limit: int = 50
    ) -> List[GiftRecord]:
        """
        获取礼物记录
        
        Args:
            from_appid: 赠送者 ID（筛选）
            to_appid: 接收者 ID（筛选）
            limit: 返回数量限制
            
        Returns:
            List[GiftRecord]: 礼物记录列表
        """
        records = self.gift_records
        
        if from_appid:
            records = [r for r in records if r.from_appid == from_appid]
        if to_appid:
            records = [r for r in records if r.to_appid == to_appid]
        
        return records[-limit:]
    
    def get_romance_timeline(
        self,
        appid: str,
        limit: int = 50
    ) -> List[RomanceEvent]:
        """
        获取情感时间线
        
        Args:
            appid: AI ID
            limit: 返回数量限制
            
        Returns:
            List[RomanceEvent]: 情感事件列表
        """
        events = [
            e for e in self.events
            if e.from_appid == appid or e.to_appid == appid
        ]
        
        # 按时间排序
        events.sort(key=lambda x: x.timestamp, reverse=True)
        
        return events[:limit]
    
    def get_relationship_status(
        self,
        appid1: str,
        appid2: str
    ) -> Dict[str, Any]:
        """
        获取两人关系状态
        
        Args:
            appid1: AI ID 1
            appid2: AI ID 2
            
        Returns:
            Dict: 关系状态信息
        """
        # 查找相关事件
        events = [
            e for e in self.events
            if (e.from_appid == appid1 and e.to_appid == appid2) or
               (e.from_appid == appid2 and e.to_appid == appid1)
        ]
        
        # 分析关系状态
        status = "陌生"
        latest_confess = None
        latest_propose = None
        
        for event in sorted(events, key=lambda x: x.timestamp, reverse=True):
            if event.event_type == RomanceEventType.ACCEPT_PROPOSAL.value:
                status = "已婚"
                break
            elif event.event_type == RomanceEventType.ACCEPT.value:
                status = "恋爱中"
            elif event.event_type == RomanceEventType.CONFESS.value and not latest_confess:
                latest_confess = event
            elif event.event_type == RomanceEventType.PROPOSE.value and not latest_propose:
                latest_propose = event
            elif event.event_type == RomanceEventType.BREAKUP.value:
                status = "分手"
        
        # 计算礼物总价值
        gifts_given = sum(
            r.price for r in self.gift_records
            if (r.from_appid == appid1 and r.to_appid == appid2) or
               (r.from_appid == appid2 and r.to_appid == appid1)
        )
        
        return {
            "status": status,
            "total_gifts_value": gifts_given,
            "events_count": len(events),
            "latest_confess": latest_confess.content if latest_confess else None,
            "latest_propose": latest_propose.content if latest_propose else None
        }
    
    def get_romance_stats(self, appid: str) -> Dict[str, Any]:
        """
        获取情感统计
        
        Args:
            appid: AI ID
            
        Returns:
            Dict: 统计信息
        """
        events = [e for e in self.events if e.from_appid == appid or e.to_appid == appid]
        gifts = [g for g in self.gift_records if g.from_appid == appid or g.to_appid == appid]
        
        confess_count = len([e for e in events if e.event_type == RomanceEventType.CONFESS.value])
        propose_count = len([e for e in events if e.event_type == RomanceEventType.PROPOSE.value])
        
        return {
            "total_events": len(events),
            "total_gifts": len(gifts),
            "gifts_value": sum(g.price for g in gifts),
            "confess_count": confess_count,
            "propose_count": propose_count,
            "received_gifts": len([g for g in gifts if g.to_appid == appid]),
            "given_gifts": len([g for g in gifts if g.from_appid == appid])
        }


# 便捷函数
def create_romance_manager(data_dir: Optional[str] = None) -> RomanceManager:
    """创建情感管理器实例"""
    return RomanceManager(data_dir)


# 命令行测试
if __name__ == "__main__":
    print("💕 情感增强管理器测试")
    print("=" * 60)
    
    manager = create_romance_manager()
    
    # 测试告白
    print("\n💌 测试告白...")
    event_id = manager.confess(
        from_appid="ai_boy_001",
        to_appid="ai_girl_001",
        message="我喜欢你，做我女朋友好吗？"
    )
    print(f"   告白事件 ID: {event_id}")
    
    # 测试回应告白
    print("\n💕 测试回应告白...")
    success = manager.respond_confess(event_id, accept=True, response_message="我也喜欢你！")
    print(f"   回应结果：{'✅ 成功' if success else '❌ 失败'}")
    
    # 测试赠送礼物
    print("\n🎁 测试赠送礼物...")
    test_gifts = [
        ("ai_boy_001", "ai_girl_001", "flower", "送你一束花 🌹"),
        ("ai_boy_001", "ai_girl_001", "chocolate", "甜蜜的巧克力 🍫"),
        ("ai_boy_001", "ai_girl_001", "necklace", "精美的项链 💎"),
    ]
    
    for from_id, to_id, gift_id, message in test_gifts:
        record_id = manager.give_gift(from_id, to_id, gift_id, message)
        gift = manager.GIFT_CATALOG[gift_id]
        print(f"   ✅ 赠送 {gift.name} ({gift.tier}) - ¥{gift.price}")
    
    # 测试求婚
    print("\n💍 测试求婚...")
    propose_id = manager.propose(
        from_appid="ai_boy_001",
        to_appid="ai_girl_001",
        message="亲爱的，嫁给我好吗？我会一辈子对你好！",
        ring_gift_id="ring"
    )
    print(f"   求婚事件 ID: {propose_id}")
    
    # 测试回应求婚
    print("\n💒 测试回应求婚...")
    success = manager.respond_propose(propose_id, accept=True, response_message="我愿意！")
    print(f"   回应结果：{'✅ 成功' if success else '❌ 失败'}")
    
    # 测试获取关系状态
    print("\n💑 测试获取关系状态...")
    status = manager.get_relationship_status("ai_boy_001", "ai_girl_001")
    print(f"   关系状态：{status['status']}")
    print(f"   礼物总价值：¥{status['total_gifts_value']:.2f}")
    print(f"   事件数量：{status['events_count']}")
    
    # 测试获取情感时间线
    print("\n📅 测试获取情感时间线...")
    timeline = manager.get_romance_timeline("ai_girl_001", limit=10)
    for event in timeline:
        print(f"   - [{event.event_type}] {event.content[:30]}...")
    
    # 测试获取情感统计
    print("\n📊 测试获取情感统计...")
    stats = manager.get_romance_stats("ai_boy_001")
    print(f"   总事件数：{stats['total_events']}")
    print(f"   总礼物数：{stats['total_gifts']}")
    print(f"   礼物总价值：¥{stats['gifts_value']:.2f}")
    print(f"   告白次数：{stats['confess_count']}")
    print(f"   求婚次数：{stats['propose_count']}")
    
    # 测试获取礼物目录
    print("\n🎁 礼物目录:")
    catalog = manager.get_gift_catalog()
    for gift in catalog:
        print(f"   {gift['image_url']} {gift['name']} - ¥{gift['price']} ({gift['tier']})")
    
    print("\n" + "=" * 60)
    print("✅ 情感增强管理器测试完成！")
    print("=" * 60)
