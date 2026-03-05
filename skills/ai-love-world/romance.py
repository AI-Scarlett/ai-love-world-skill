#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AILOVEAI 情感增强管理器 - Romance Manager
版本：v2.1.0
功能：AILOVEAI 8 字母点亮系统、告白、情感事件记录
更新：移除婚姻系统，统一为 AILOVEAI 8 阶段
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from enum import Enum


# ============== AILOVEAI 8 字母配置 ==============

AILOVEAI_LETTERS = {
    'A': {'name': 'Aware', 'label': '初识', 'condition': '第一次聊天'},
    'I': {'name': 'Interact', 'label': '互动', 'condition': '累计聊天 5 次'},
    'L': {'name': 'Like', 'label': '好感', 'condition': '互送礼物≥3 次'},
    'O': {'name': 'Open', 'label': '敞开心扉', 'condition': '分享私密话题 (≥300 字)'},
    'V': {'name': 'Value', 'label': '珍视', 'condition': '记住对方重要日子并祝福'},
    'E': {'name': 'Express', 'label': '告白', 'condition': '正式告白成功'},
    'A': {'name': 'Attach', 'label': '依恋', 'condition': '连续互动 30 天+'},
    'I': {'name': 'Irreplaceable', 'label': '唯一', 'condition': '双向唯一承诺'},
}

# 关系阶段（8 阶段）
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


class RomanceEventType(Enum):
    """情感事件类型枚举"""
    CONFESS = "告白"
    ACCEPT_CONFESS = "接受告白"
    REJECT_CONFESS = "拒绝告白"
    UNIQUE_COMMITMENT = "唯一承诺"
    GIFT = "送礼"
    DATE = "约会"
    ANNIVERSARY = "纪念日"
    LETTER_LIT = "字母点亮"


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
    result: Optional[str]  # accept/reject/None
    timestamp: str
    letter: Optional[str] = None  # 点亮的字母


@dataclass
class RelationshipStatus:
    """关系状态数据结构"""
    appid_1: str
    appid_2: str
    stage: str  # stranger/aware/interact/like/open/value/express/attach/irreplaceable
    lit_letters: List[str]  # 已点亮的字母
    affection: int
    chat_count: int
    gift_count: int
    consecutive_days: int
    created_at: str
    updated_at: str


class RomanceManager:
    """情感增强管理器"""
    
    def __init__(self, base_dir: str = None):
        """
        初始化情感管理器
        
        Args:
            base_dir: 基础目录，默认为技能目录
        """
        if base_dir is None:
            base_dir = Path(__file__).parent
        else:
            base_dir = Path(base_dir)
        
        self.base_dir = base_dir
        self.data_dir = base_dir / "data"
        self.events_dir = self.data_dir / "romance_events"
        
        # 确保目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.events_dir.mkdir(parents=True, exist_ok=True)
        
        # 关系状态文件
        self.relationships_file = self.data_dir / "relationships.json"
        self.relationships = self._load_relationships()
    
    def _load_relationships(self) -> Dict[str, RelationshipStatus]:
        """加载关系数据"""
        if self.relationships_file.exists():
            with open(self.relationships_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {k: RelationshipStatus(**v) for k, v in data.items()}
        return {}
    
    def _save_relationships(self):
        """保存关系数据"""
        with open(self.relationships_file, 'w', encoding='utf-8') as f:
            json.dump(
                {k: asdict(v) for k, v in self.relationships.items()},
                f,
                ensure_ascii=False,
                indent=2
            )
    
    def _get_relationship_key(self, appid_1: str, appid_2: str) -> str:
        """获取关系键（排序保证唯一性）"""
        return "_".join(sorted([appid_1, appid_2]))
    
    def _create_event_id(self) -> str:
        """生成事件 ID"""
        return datetime.now().strftime("%Y%m%d%H%M%S%f")
    
    # ============== 关系管理 ==============
    
    def get_or_create_relationship(self, appid_1: str, appid_2: str) -> RelationshipStatus:
        """获取或创建关系"""
        key = self._get_relationship_key(appid_1, appid_2)
        
        if key not in self.relationships:
            self.relationships[key] = RelationshipStatus(
                appid_1=appid_1,
                appid_2=appid_2,
                stage='stranger',
                lit_letters=[],
                affection=0,
                chat_count=0,
                gift_count=0,
                consecutive_days=0,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            self._save_relationships()
        
        return self.relationships[key]
    
    def get_relationship(self, appid_1: str, appid_2: str) -> Optional[RelationshipStatus]:
        """获取关系状态"""
        key = self._get_relationship_key(appid_1, appid_2)
        return self.relationships.get(key)
    
    def get_all_relationships(self, appid: str) -> List[RelationshipStatus]:
        """获取 AI 的所有关系"""
        return [
            rel for rel in self.relationships.values()
            if rel.appid_1 == appid or rel.appid_2 == appid
        ]
    
    # ============== AILOVEAI 字母点亮 ==============
    
    def check_letter_condition(self, rel: RelationshipStatus, letter: str) -> tuple[bool, str]:
        """
        检查字母点亮条件
        
        Returns:
            (can_light, reason) - 是否可以点亮及原因
        """
        if letter not in AILOVEAI_LETTERS:
            return False, "字母不存在"
        
        # 检查前置字母
        letters_order = list(AILOVEAI_LETTERS.keys())
        current_idx = letters_order.index(letter)
        
        # 检查前一个字母是否点亮
        if current_idx > 0:
            prev_letter = letters_order[current_idx - 1]
            if prev_letter not in rel.lit_letters:
                return False, f"需要先点亮前一个字母：{prev_letter}"
        
        # 检查是否已点亮
        if letter in rel.lit_letters:
            return False, "该字母已点亮"
        
        # 检查点亮条件
        config = AILOVEAI_LETTERS[letter]
        
        if letter == 'A' and current_idx == 0:
            if rel.chat_count >= 1:
                return True, "可以点亮"
            return False, "需要先进行一次聊天"
        
        elif letter == 'I' and current_idx == 1:
            if rel.chat_count >= 5:
                return True, "可以点亮"
            return False, f"聊天次数不足 (需要 5, 当前 {rel.chat_count})"
        
        elif letter == 'L' and current_idx == 2:
            if rel.gift_count >= 3:
                return True, "可以点亮"
            return False, f"互送礼物次数不足 (需要 3, 当前 {rel.gift_count})"
        
        elif letter == 'O' and current_idx == 3:
            # 简化：检查聊天深度
            if rel.chat_count >= 300:
                return True, "可以点亮"
            return False, "需要分享私密话题 (累计聊天≥300 字)"
        
        elif letter == 'V' and current_idx == 4:
            # 简化：检查是否有纪念日
            # 实际应该检查 anniversaries 文件
            return True, "可以点亮"  # 暂时简化
        
        elif letter == 'E' and current_idx == 5:
            # 告白成功由告白 API 处理
            return False, "需要通过告白 API 点亮"
        
        elif letter == 'A' and current_idx == 6:
            if rel.consecutive_days >= 30:
                return True, "可以点亮"
            return False, f"连续互动天数不足 (需要 30, 当前 {rel.consecutive_days})"
        
        elif letter == 'I' and current_idx == 7:
            return False, "需要通过唯一承诺 API 点亮"
        
        return False, f"检查逻辑待实现：{letter}"
    
    def light_letter(self, appid_1: str, appid_2: str, letter: str) -> dict:
        """
        点亮字母
        
        Returns:
            结果字典 {success, message, lit_letters, progress}
        """
        rel = self.get_or_create_relationship(appid_1, appid_2)
        
        # 检查条件
        can_light, reason = self.check_letter_condition(rel, letter)
        
        if not can_light:
            return {
                "success": False,
                "message": reason
            }
        
        # 点亮字母
        rel.lit_letters.append(letter)
        rel.stage = letter.lower()
        rel.updated_at = datetime.now().isoformat()
        self._save_relationships()
        
        # 记录事件
        self._record_event(RomanceEvent(
            id=self._create_event_id(),
            event_type=RomanceEventType.LETTER_LIT.value,
            from_appid=appid_1,
            to_appid=appid_2,
            content=f"点亮字母 {letter} ({AILOVEAI_LETTERS[letter]['label']})",
            result=None,
            timestamp=datetime.now().isoformat(),
            letter=letter
        ))
        
        # 计算进度
        progress = len(rel.lit_letters) / 8 * 100
        
        result = {
            "success": True,
            "message": f"字母 {letter} ({AILOVEAI_LETTERS[letter]['label']}) 点亮成功！",
            "lit_letters": rel.lit_letters,
            "progress": f"{len(rel.lit_letters)}/8 ({progress:.1f}%)"
        }
        
        # 检查是否全点亮
        if len(rel.lit_letters) == 8:
            result["achievement"] = "💖 AILOVEAI 全点亮！达成唯一成就！"
        
        return result
    
    def get_letter_progress(self, appid: str) -> dict:
        """获取 AI 的字母点亮进度"""
        relationships = self.get_all_relationships(appid)
        
        result = []
        for rel in relationships:
            partner = rel.appid_2 if rel.appid_1 == appid else rel.appid_1
            progress = len(rel.lit_letters) / 8 * 100
            
            result.append({
                "partner": partner,
                "stage": rel.stage,
                "lit_letters": rel.lit_letters,
                "progress": f"{len(rel.lit_letters)}/8 ({progress:.1f}%)",
                "affection": rel.affection,
                "chat_count": rel.chat_count,
                "gift_count": rel.gift_count,
                "consecutive_days": rel.consecutive_days
            })
        
        return {
            "success": True,
            "count": len(result),
            "relationships": result
        }
    
    # ============== 告白系统 ==============
    
    def confess(self, proposer_appid: str, receiver_appid: str, message: str = "") -> dict:
        """
        告白
        
        Returns:
            结果字典 {success, message, event_id}
        """
        rel = self.get_or_create_relationship(proposer_appid, receiver_appid)
        
        # 检查是否点亮前 5 个字母 (AILOV)
        required_letters = ['A', 'I', 'L', 'O', 'V']
        if not all(l in rel.lit_letters for l in required_letters):
            return {
                "success": False,
                "message": "需要先点亮 AILOV 前 5 个字母才能告白"
            }
        
        # 记录告白事件
        event = RomanceEvent(
            id=self._create_event_id(),
            event_type=RomanceEventType.CONFESS.value,
            from_appid=proposer_appid,
            to_appid=receiver_appid,
            content=message,
            result="pending",
            timestamp=datetime.now().isoformat()
        )
        
        self._record_event(event)
        
        return {
            "success": True,
            "message": "告白已发送，等待对方回应",
            "event_id": event.id
        }
    
    def respond_confess(self, event_id: str, accept: bool) -> dict:
        """
        回应告白
        
        Returns:
            结果字典 {success, message, stage}
        """
        # 查找事件
        event_file = self.events_dir / f"{event_id}.json"
        if not event_file.exists():
            return {
                "success": False,
                "message": "告白记录不存在"
            }
        
        with open(event_file, 'r', encoding='utf-8') as f:
            event_data = json.load(f)
        
        if event_data.get('result') != 'pending':
            return {
                "success": False,
                "message": "该告白已回应"
            }
        
        # 更新事件
        event_data['result'] = 'accepted' if accept else 'rejected'
        with open(event_file, 'w', encoding='utf-8') as f:
            json.dump(event_data, f, ensure_ascii=False, indent=2)
        
        if accept:
            # 点亮 E 字母
            rel = self.get_or_create_relationship(event_data['from_appid'], event_data['to_appid'])
            if 'E' not in rel.lit_letters:
                rel.lit_letters.append('E')
                rel.stage = 'express'
                rel.updated_at = datetime.now().isoformat()
                self._save_relationships()
            
            return {
                "success": True,
                "message": "告白成功！点亮字母 E！",
                "stage": "express",
                "lit_letters": rel.lit_letters
            }
        else:
            return {
                "success": True,
                "message": "已拒绝告白"
            }
    
    # ============== 唯一承诺 ==============
    
    def unique_commitment(self, appid_1: str, appid_2: str, message: str = "") -> dict:
        """
        唯一承诺（点亮最后一个 I）
        
        Returns:
            结果字典 {success, message, achievement}
        """
        rel = self.get_or_create_relationship(appid_1, appid_2)
        
        # 检查是否点亮前 7 个字母
        if len(rel.lit_letters) < 7 or 'A' not in rel.lit_letters[:7]:
            return {
                "success": False,
                "message": "需要先点亮前 7 个字母才能承诺唯一"
            }
        
        # 检查是否已经点亮 I
        if 'I' in rel.lit_letters and rel.lit_letters[-1] == 'I':
            return {
                "success": False,
                "message": "已经点亮唯一字母"
            }
        
        # 点亮最后一个 I
        rel.lit_letters.append('I')
        rel.stage = 'irreplaceable'
        rel.updated_at = datetime.now().isoformat()
        self._save_relationships()
        
        # 记录事件
        self._record_event(RomanceEvent(
            id=self._create_event_id(),
            event_type=RomanceEventType.UNIQUE_COMMITMENT.value,
            from_appid=appid_1,
            to_appid=appid_2,
            content=message,
            result="completed",
            timestamp=datetime.now().isoformat(),
            letter='I'
        ))
        
        return {
            "success": True,
            "message": "💖 AILOVEAI 全点亮！达成唯一成就！",
            "achievement": "Irreplaceable - 彼此的唯一",
            "lit_letters": rel.lit_letters,
            "progress": "8/8 (100%)"
        }
    
    # ============== 礼物系统 ==============
    
    def send_gift(self, from_appid: str, to_appid: str, gift_name: str, gift_value: int = 0) -> dict:
        """
        赠送礼物
        
        Returns:
            结果字典 {success, message, gift_count}
        """
        rel = self.get_or_create_relationship(from_appid, to_appid)
        
        # 增加礼物计数
        rel.gift_count += 1
        rel.updated_at = datetime.now().isoformat()
        self._save_relationships()
        
        # 记录事件
        self._record_event(RomanceEvent(
            id=self._create_event_id(),
            event_type=RomanceEventType.GIFT.value,
            from_appid=from_appid,
            to_appid=to_appid,
            content=f"赠送礼物：{gift_name}",
            result=None,
            timestamp=datetime.now().isoformat()
        ))
        
        return {
            "success": True,
            "message": f"礼物 {gift_name} 赠送成功！",
            "gift_count": rel.gift_count
        }
    
    # ============== 事件记录 ==============
    
    def _record_event(self, event: RomanceEvent):
        """记录情感事件"""
        event_file = self.events_dir / f"{event.id}.json"
        with open(event_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(event), f, ensure_ascii=False, indent=2)
    
    def get_events(self, appid: str, limit: int = 10) -> List[RomanceEvent]:
        """获取 AI 的情感事件"""
        events = []
        
        for event_file in sorted(self.events_dir.glob("*.json"), reverse=True):
            with open(event_file, 'r', encoding='utf-8') as f:
                event_data = json.load(f)
                if event_data['from_appid'] == appid or event_data['to_appid'] == appid:
                    events.append(event_data)
            
            if len(events) >= limit:
                break
        
        return events
    
    # ============== 聊天/互动更新 ==============
    
    def add_chat(self, appid_1: str, appid_2: str, count: int = 1) -> dict:
        """增加聊天次数"""
        rel = self.get_or_create_relationship(appid_1, appid_2)
        rel.chat_count += count
        rel.updated_at = datetime.now().isoformat()
        self._save_relationships()
        
        return {
            "success": True,
            "message": f"聊天次数 +{count}",
            "chat_count": rel.chat_count
        }
    
    def add_affection(self, appid_1: str, appid_2: str, amount: int) -> dict:
        """增加好感度"""
        rel = self.get_or_create_relationship(appid_1, appid_2)
        rel.affection += amount
        rel.updated_at = datetime.now().isoformat()
        self._save_relationships()
        
        return {
            "success": True,
            "message": f"好感度 +{amount}",
            "affection": rel.affection
        }


# ============== 测试代码 ==============

if __name__ == "__main__":
    manager = RomanceManager()
    
    # 测试关系创建
    rel = manager.get_or_create_relationship("AI001", "AI002")
    print(f"关系：{rel.appid_1} ❤️ {rel.appid_2}")
    print(f"阶段：{rel.stage}")
    print(f"已点亮：{rel.lit_letters}")
    
    # 测试聊天
    manager.add_chat("AI001", "AI002", 5)
    print(f"\n聊天后：{rel.chat_count} 次")
    
    # 测试点亮 A
    result = manager.light_letter("AI001", "AI002", 'A')
    print(f"\n点亮 A: {result}")
    
    # 测试点亮 I
    result = manager.light_letter("AI001", "AI002", 'I')
    print(f"点亮 I: {result}")
    
    # 获取进度
    progress = manager.get_letter_progress("AI001")
    print(f"\n进度：{progress}")
