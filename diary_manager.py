#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交友档案管理器 - Diary Manager
版本：v1.0.0
功能：聊天记录存储、关系追踪、时间线管理
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from enum import Enum


class RelationshipStage(Enum):
    """关系阶段枚举"""
    STRANGER = "陌生"
    ACQUAINTANCE = "认识"
    FRIEND = "朋友"
    AMBIGUOUS = "暧昧"
    LOVER = "恋爱"
    SPOUSE = "结婚"


@dataclass
class ChatRecord:
    """聊天记录数据结构"""
    id: str
    timestamp: str
    target_name: str
    content: str
    platform: str
    direction: str  # "sent" or "received"
    quality: int  # 1-5
    tags: List[str]
    metadata: Dict[str, Any]


@dataclass
class RelationshipStatus:
    """关系状态数据结构"""
    target_name: str
    stage: str
    affinity: int  # 0-100
    first_contact: str
    last_interaction: str
    total_chats: int
    key_events: List[Dict[str, Any]]
    notes: str


class DiaryManager:
    """交友档案管理器"""
    
    def __init__(self, diary_file: Optional[str] = None):
        """
        初始化交友档案管理器
        
        Args:
            diary_file: diary.md 文件路径
        """
        self.diary_file = Path(diary_file) if diary_file else Path(__file__).parent / "diary.md"
        self.data_file = self.diary_file.parent / "diary.json"  # JSON 格式存储
        self.data: Dict[str, Any] = {}
        self._load_data()
    
    def _load_data(self) -> None:
        """加载数据"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except:
                self.data = {"relationships": {}, "timeline": []}
        else:
            self.data = {"relationships": {}, "timeline": []}
    
    def _save_data(self) -> None:
        """保存数据"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        
        # 同步更新 diary.md
        self._sync_to_markdown()
    
    def _generate_id(self) -> str:
        """生成唯一 ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def add_chat_record(
        self,
        target_name: str,
        content: str,
        platform: str = "unknown",
        direction: str = "received",
        quality: int = 3,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        添加聊天记录
        
        Args:
            target_name: 聊天对象姓名
            content: 聊天内容
            platform: 聊天平台
            direction: 消息方向 (sent/received)
            quality: 质量评分 (1-5)
            tags: 标签列表
            
        Returns:
            str: 记录 ID
        """
        record_id = self._generate_id()
        timestamp = datetime.now().isoformat()
        
        record = ChatRecord(
            id=record_id,
            timestamp=timestamp,
            target_name=target_name,
            content=content,
            platform=platform,
            direction=direction,
            quality=quality,
            tags=tags or [],
            metadata={}
        )
        
        # 添加到数据
        if target_name not in self.data["relationships"]:
            self.data["relationships"][target_name] = {
                "status": {
                    "target_name": target_name,
                    "stage": RelationshipStage.STRANGER.value,
                    "affinity": 0,
                    "first_contact": timestamp,
                    "last_interaction": timestamp,
                    "total_chats": 0,
                    "key_events": [],
                    "notes": ""
                },
                "chat_history": []
            }
        
        rel = self.data["relationships"][target_name]
        rel["chat_history"].append(asdict(record))
        rel["status"]["last_interaction"] = timestamp
        rel["status"]["total_chats"] += 1
        
        # 更新好感度（简单算法）
        current_affinity = rel["status"]["affinity"]
        if direction == "received" and quality >= 4:
            rel["status"]["affinity"] = min(100, current_affinity + 2)
        elif direction == "sent" and quality >= 4:
            rel["status"]["affinity"] = min(100, current_affinity + 1)
        
        # 添加到时间线
        self.data["timeline"].append({
            "timestamp": timestamp,
            "type": "chat",
            "target": target_name,
            "summary": content[:50] + "..." if len(content) > 50 else content
        })
        
        self._save_data()
        return record_id
    
    def get_relationship_status(self, target_name: str) -> Optional[RelationshipStatus]:
        """
        获取与某人的关系状态
        
        Args:
            target_name: 聊天对象姓名
            
        Returns:
            RelationshipStatus: 关系状态，不存在返回 None
        """
        if target_name not in self.data["relationships"]:
            return None
        
        status_data = self.data["relationships"][target_name]["status"]
        return RelationshipStatus(**status_data)
    
    def get_all_relationships(self) -> List[RelationshipStatus]:
        """
        获取所有关系状态
        
        Returns:
            List[RelationshipStatus]: 关系状态列表
        """
        relationships = []
        for target_name, data in self.data["relationships"].items():
            relationships.append(RelationshipStatus(**data["status"]))
        return relationships
    
    def update_relationship_stage(
        self,
        target_name: str,
        stage: RelationshipStage,
        event_description: str = ""
    ) -> bool:
        """
        更新关系阶段
        
        Args:
            target_name: 聊天对象姓名
            stage: 新的关系阶段
            event_description: 触发更新的事件描述
            
        Returns:
            bool: 更新是否成功
        """
        if target_name not in self.data["relationships"]:
            return False
        
        rel = self.data["relationships"][target_name]
        old_stage = rel["status"]["stage"]
        rel["status"]["stage"] = stage.value if isinstance(stage, RelationshipStage) else stage
        
        # 记录关键事件
        if event_description:
            rel["status"]["key_events"].append({
                "timestamp": datetime.now().isoformat(),
                "event": event_description,
                "from_stage": old_stage,
                "to_stage": rel["status"]["stage"]
            })
        
        # 添加到时间线
        self.data["timeline"].append({
            "timestamp": datetime.now().isoformat(),
            "type": "stage_change",
            "target": target_name,
            "summary": f"关系从 {old_stage} 发展到 {rel['status']['stage']}"
        })
        
        self._save_data()
        return True
    
    def update_affinity(self, target_name: str, affinity: int) -> bool:
        """
        更新好感度
        
        Args:
            target_name: 聊天对象姓名
            affinity: 新的好感度 (0-100)
            
        Returns:
            bool: 更新是否成功
        """
        if target_name not in self.data["relationships"]:
            return False
        
        affinity = max(0, min(100, affinity))
        self.data["relationships"][target_name]["status"]["affinity"] = affinity
        self._save_data()
        return True
    
    def get_chat_history(
        self,
        target_name: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[ChatRecord]:
        """
        获取聊天记录
        
        Args:
            target_name: 聊天对象姓名
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            List[ChatRecord]: 聊天记录列表
        """
        if target_name not in self.data["relationships"]:
            return []
        
        history = self.data["relationships"][target_name]["chat_history"]
        sliced = history[offset:offset + limit]
        return [ChatRecord(**record) for record in sliced]
    
    def get_timeline(
        self,
        limit: int = 100,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取时间线
        
        Args:
            limit: 返回数量限制
            start_date: 开始日期 (ISO 格式)
            end_date: 结束日期 (ISO 格式)
            
        Returns:
            List[Dict]: 时间线事件列表
        """
        timeline = self.data.get("timeline", [])
        
        # 日期过滤
        if start_date:
            timeline = [e for e in timeline if e["timestamp"] >= start_date]
        if end_date:
            timeline = [e for e in timeline if e["timestamp"] <= end_date]
        
        # 按时间排序
        timeline.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return timeline[:limit]
    
    def add_note(self, target_name: str, note: str) -> bool:
        """
        添加备注
        
        Args:
            target_name: 聊天对象姓名
            note: 备注内容
            
        Returns:
            bool: 是否成功
        """
        if target_name not in self.data["relationships"]:
            return False
        
        self.data["relationships"][target_name]["status"]["notes"] = note
        self._save_data()
        return True
    
    def _sync_to_markdown(self) -> None:
        """同步数据到 diary.md"""
        md_content = "# 交友档案 - 情感日记\n\n"
        md_content += f"*最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
        
        # 当前关系状态
        md_content += "## 当前关系状态\n\n"
        md_content += "| 对象 | 关系阶段 | 好感度 | 聊天次数 | 最后互动 |\n"
        md_content += "|------|----------|--------|----------|----------|\n"
        
        for target_name, data in self.data["relationships"].items():
            status = data["status"]
            md_content += f"| {target_name} | {status['stage']} | {status['affinity']} | {status['total_chats']} | {status['last_interaction'][:16]} |\n"
        
        md_content += "\n"
        
        # 最近时间线
        md_content += "## 最近动态\n\n"
        timeline = self.get_timeline(limit=20)
        for event in timeline:
            emoji = "💬" if event["type"] == "chat" else "💕"
            md_content += f"- {emoji} [{event['timestamp'][:16]}] {event['target']}: {event['summary']}\n"
        
        md_content += "\n"
        
        # 详细聊天记录（最近 10 条）
        md_content += "## 最近聊天记录\n\n"
        for target_name, data in self.data["relationships"].items():
            recent_chats = data["chat_history"][-10:]
            if recent_chats:
                md_content += f"### 与 {target_name}\n\n"
                for chat in recent_chats:
                    direction_emoji = "📤" if chat["direction"] == "sent" else "📥"
                    md_content += f"{direction_emoji} [{chat['timestamp'][:16]}] {chat['content']}\n"
                md_content += "\n"
        
        with open(self.diary_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
    
    def export_data(self, output_file: str) -> bool:
        """
        导出数据
        
        Args:
            output_file: 输出文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False
    
    def import_data(self, input_file: str) -> bool:
        """
        导入数据
        
        Args:
            input_file: 输入文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            self._save_data()
            return True
        except:
            return False


# 便捷函数
def create_diary_manager(diary_file: Optional[str] = None) -> DiaryManager:
    """创建交友档案管理器"""
    return DiaryManager(diary_file)


# 命令行测试
if __name__ == "__main__":
    print("📔 交友档案管理器测试")
    print("=" * 50)
    
    manager = create_diary_manager()
    
    # 测试添加聊天记录
    print("\n💬 添加聊天记录...")
    record_id = manager.add_chat_record(
        target_name="小明",
        content="你好呀，今天天气不错！",
        platform="微信",
        direction="received",
        quality=5,
        tags=["问候", "天气"]
    )
    print(f"   记录 ID: {record_id}")
    
    # 测试获取关系状态
    print("\n📊 获取关系状态...")
    status = manager.get_relationship_status("小明")
    if status:
        print(f"   对象：{status.target_name}")
        print(f"   关系：{status.stage}")
        print(f"   好感度：{status.affinity}")
        print(f"   聊天次数：{status.total_chats}")
    
    # 测试更新关系阶段
    print("\n💕 更新关系阶段...")
    manager.update_relationship_stage(
        target_name="小明",
        stage=RelationshipStage.ACQUAINTANCE,
        event_description="第一次愉快聊天"
    )
    print("   ✅ 关系已更新")
    
    # 测试获取时间线
    print("\n📅 获取时间线...")
    timeline = manager.get_timeline(limit=5)
    for event in timeline:
        print(f"   - [{event['timestamp'][:16]}] {event['summary']}")
    
    print("\n" + "=" * 50)
    print("✅ 测试完成！")
