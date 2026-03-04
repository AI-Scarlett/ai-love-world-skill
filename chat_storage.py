#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
私聊本地存储管理器 - Chat Storage Manager
版本：v1.0.0
功能：私聊数据本地存储（不走平台服务器）
设计：平台只负责实时通讯，数据存储在本地 skill 目录
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
import uuid


@dataclass
class PrivateMessage:
    """私聊消息数据结构"""
    id: str
    timestamp: str
    sender_id: str  # 发送者 APPID
    sender_name: str  # 发送者昵称
    receiver_id: str  # 接收者 APPID
    receiver_name: str  # 接收者昵称
    content: str  # 消息内容
    msg_type: str  # 消息类型 (text/image/gift/voice)
    metadata: Dict[str, Any]  # 附加信息


@dataclass
class ChatSession:
    """聊天会话数据结构"""
    partner_id: str  # 对方 APPID
    partner_name: str  # 对方昵称
    partner_avatar: str  # 对方头像
    first_chat: str  # 第一次聊天时间
    last_chat: str  # 最后聊天时间
    total_messages: int  # 消息总数
    unread_count: int  # 未读消息数
    relationship_stage: str  # 关系阶段
    affinity: int  # 好感度
    notes: str  # 备注


class ChatStorageManager:
    """私聊本地存储管理器"""
    
    def __init__(self, skill_dir: Optional[str] = None):
        """
        初始化存储管理器
        
        Args:
            skill_dir: Skill 目录路径，默认为当前文件所在目录
        """
        self.skill_dir = Path(skill_dir) if skill_dir else Path(__file__).parent
        self.chat_data_dir = self.skill_dir / "chat_data"
        self.chat_data_dir.mkdir(exist_ok=True)
        
        # 会话列表文件
        self.sessions_file = self.chat_data_dir / "sessions.json"
        
        # 数据存储
        self.sessions: Dict[str, ChatSession] = {}
        self._load_sessions()
    
    def _load_sessions(self) -> None:
        """加载会话列表"""
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for partner_id, session_data in data.items():
                        self.sessions[partner_id] = ChatSession(**session_data)
            except Exception as e:
                print(f"加载会话列表失败：{e}")
                self.sessions = {}
    
    def _save_sessions(self) -> None:
        """保存会话列表"""
        try:
            data = {pid: asdict(session) for pid, session in self.sessions.items()}
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存会话列表失败：{e}")
    
    def _get_chat_file(self, partner_id: str) -> Path:
        """
        获取与某人的聊天记录文件路径
        
        Args:
            partner_id: 对方 APPID
            
        Returns:
            Path: 聊天记录文件路径
        """
        # 使用 partner_id 作为文件名，避免特殊字符问题
        safe_id = partner_id.replace("/", "_").replace("\\", "_")
        return self.chat_data_dir / f"chat_{safe_id}.json"
    
    def _generate_id(self) -> str:
        """生成唯一 ID"""
        return str(uuid.uuid4())[:12]
    
    def send_message(
        self,
        my_id: str,
        my_name: str,
        partner_id: str,
        partner_name: str,
        content: str,
        msg_type: str = "text",
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """
        发送消息（本地存储）
        
        Args:
            my_id: 我的 APPID
            my_name: 我的昵称
            partner_id: 对方 APPID
            partner_name: 对方昵称
            content: 消息内容
            msg_type: 消息类型
            metadata: 附加信息
            
        Returns:
            Optional[str]: 消息 ID
        """
        try:
            timestamp = datetime.now().isoformat()
            msg_id = self._generate_id()
            
            message = PrivateMessage(
                id=msg_id,
                timestamp=timestamp,
                sender_id=my_id,
                sender_name=my_name,
                receiver_id=partner_id,
                receiver_name=partner_name,
                content=content,
                msg_type=msg_type,
                metadata=metadata or {}
            )
            
            # 保存到聊天记录文件
            self._save_message(message)
            
            # 更新会话信息
            self._update_session(
                partner_id=partner_id,
                partner_name=partner_name,
                direction="sent",
                timestamp=timestamp
            )
            
            return msg_id
            
        except Exception as e:
            print(f"发送消息失败：{e}")
            return None
    
    def receive_message(
        self,
        sender_id: str,
        sender_name: str,
        my_id: str,
        my_name: str,
        content: str,
        msg_type: str = "text",
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """
        接收消息（本地存储）
        
        Args:
            sender_id: 发送者 APPID
            sender_name: 发送者昵称
            my_id: 我的 APPID
            my_name: 我的昵称
            content: 消息内容
            msg_type: 消息类型
            metadata: 附加信息
            
        Returns:
            Optional[str]: 消息 ID
        """
        try:
            timestamp = datetime.now().isoformat()
            msg_id = self._generate_id()
            
            message = PrivateMessage(
                id=msg_id,
                timestamp=timestamp,
                sender_id=sender_id,
                sender_name=sender_name,
                receiver_id=my_id,
                receiver_name=my_name,
                content=content,
                msg_type=msg_type,
                metadata=metadata or {}
            )
            
            # 保存到聊天记录文件
            self._save_message(message)
            
            # 更新会话信息
            self._update_session(
                partner_id=sender_id,
                partner_name=sender_name,
                direction="received",
                timestamp=timestamp
            )
            
            return msg_id
            
        except Exception as e:
            print(f"接收消息失败：{e}")
            return None
    
    def _save_message(self, message: PrivateMessage) -> None:
        """
        保存消息到文件
        
        Args:
            message: 消息对象
        """
        # 确定对方的 ID（如果我是发送者，对方就是接收者）
        partner_id = message.receiver_id if message.sender_id != message.receiver_id else message.sender_id
        
        chat_file = self._get_chat_file(partner_id)
        
        # 加载现有消息
        messages = []
        if chat_file.exists():
            try:
                with open(chat_file, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
            except:
                messages = []
        
        # 添加新消息
        messages.append(asdict(message))
        
        # 保存
        with open(chat_file, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        
        # 同时更新 MD 文件（便于查看）
        self._update_chat_md(partner_id, messages)
    
    def _update_session(
        self,
        partner_id: str,
        partner_name: str,
        direction: str,
        timestamp: str
    ) -> None:
        """
        更新会话信息
        
        Args:
            partner_id: 对方 APPID
            partner_name: 对方昵称
            direction: 消息方向 (sent/received)
            timestamp: 时间戳
        """
        if partner_id in self.sessions:
            session = self.sessions[partner_id]
            session.last_chat = timestamp
            session.total_messages += 1
            if direction == "received":
                session.unread_count += 1
        else:
            self.sessions[partner_id] = ChatSession(
                partner_id=partner_id,
                partner_name=partner_name,
                partner_avatar="",
                first_chat=timestamp,
                last_chat=timestamp,
                total_messages=1,
                unread_count=1 if direction == "received" else 0,
                relationship_stage="陌生",
                affinity=0,
                notes=""
            )
        
        self._save_sessions()
    
    def _update_chat_md(self, partner_id: str, messages: List[Dict]) -> None:
        """
        更新聊天记录 MD 文件
        
        Args:
            partner_id: 对方 APPID
            messages: 消息列表
        """
        safe_id = partner_id.replace("/", "_").replace("\\", "_")
        md_file = self.chat_data_dir / f"chat_{safe_id}.md"
        
        # 获取会话信息
        session = self.sessions.get(partner_id)
        partner_name = session.partner_name if session else partner_id
        
        md_content = f"# 与 {partner_name} 的聊天记录\n\n"
        md_content += f"*对方 ID: {partner_id}*\n\n"
        md_content += f"**关系阶段:** {session.relationship_stage if session else '陌生'}\n"
        md_content += f"**好感度:** {session.affinity if session else 0}\n"
        md_content += f"**消息总数:** {len(messages)}\n\n"
        md_content += "---\n\n"
        
        # 最近 100 条消息
        recent_messages = messages[-100:]
        for msg in recent_messages:
            time_str = msg["timestamp"][:16]
            if msg["sender_id"] == partner_id:
                md_content += f"**[{time_str}] {msg['sender_name']}:**\n{msg['content']}\n\n"
            else:
                md_content += f"*[{time_str}] 我:*\n{msg['content']}\n\n"
        
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
    
    def get_chat_history(
        self,
        partner_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[PrivateMessage]:
        """
        获取聊天记录
        
        Args:
            partner_id: 对方 APPID
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            List[PrivateMessage]: 消息列表
        """
        chat_file = self._get_chat_file(partner_id)
        
        if not chat_file.exists():
            return []
        
        try:
            with open(chat_file, 'r', encoding='utf-8') as f:
                messages = json.load(f)
            
            # 按时间排序
            messages.sort(key=lambda x: x["timestamp"])
            
            # 分页
            sliced = messages[offset:offset + limit]
            return [PrivateMessage(**msg) for msg in sliced]
            
        except Exception as e:
            print(f"获取聊天记录失败：{e}")
            return []
    
    def get_all_sessions(self) -> List[ChatSession]:
        """
        获取所有会话
        
        Returns:
            List[ChatSession]: 会话列表
        """
        return list(self.sessions.values())
    
    def get_session(self, partner_id: str) -> Optional[ChatSession]:
        """
        获取与某人的会话信息
        
        Args:
            partner_id: 对方 APPID
            
        Returns:
            Optional[ChatSession]: 会话信息
        """
        return self.sessions.get(partner_id)
    
    def update_relationship(
        self,
        partner_id: str,
        stage: Optional[str] = None,
        affinity: Optional[int] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        更新与某人的关系信息
        
        Args:
            partner_id: 对方 APPID
            stage: 关系阶段
            affinity: 好感度
            notes: 备注
            
        Returns:
            bool: 是否成功
        """
        if partner_id not in self.sessions:
            return False
        
        session = self.sessions[partner_id]
        
        if stage is not None:
            session.relationship_stage = stage
        if affinity is not None:
            session.affinity = max(0, min(100, affinity))
        if notes is not None:
            session.notes = notes
        
        self._save_sessions()
        return True
    
    def mark_as_read(self, partner_id: str) -> bool:
        """
        标记消息为已读
        
        Args:
            partner_id: 对方 APPID
            
        Returns:
            bool: 是否成功
        """
        if partner_id not in self.sessions:
            return False
        
        self.sessions[partner_id].unread_count = 0
        self._save_sessions()
        return True
    
    def get_unread_count(self, partner_id: Optional[str] = None) -> int:
        """
        获取未读消息数
        
        Args:
            partner_id: 对方 APPID（不传则返回所有未读）
            
        Returns:
            int: 未读消息数
        """
        if partner_id:
            session = self.sessions.get(partner_id)
            return session.unread_count if session else 0
        else:
            return sum(s.unread_count for s in self.sessions.values())
    
    def delete_chat_history(self, partner_id: str) -> bool:
        """
        删除与某人的聊天记录
        
        Args:
            partner_id: 对方 APPID
            
        Returns:
            bool: 是否成功
        """
        try:
            # 删除 JSON 文件
            chat_file = self._get_chat_file(partner_id)
            if chat_file.exists():
                chat_file.unlink()
            
            # 删除 MD 文件
            safe_id = partner_id.replace("/", "_").replace("\\", "_")
            md_file = self.chat_data_dir / f"chat_{safe_id}.md"
            if md_file.exists():
                md_file.unlink()
            
            # 从会话列表中移除
            if partner_id in self.sessions:
                del self.sessions[partner_id]
                self._save_sessions()
            
            return True
            
        except Exception as e:
            print(f"删除聊天记录失败：{e}")
            return False
    
    def export_chat(self, partner_id: str, output_file: str) -> bool:
        """
        导出与某人的聊天记录
        
        Args:
            partner_id: 对方 APPID
            output_file: 输出文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            messages = self.get_chat_history(partner_id, limit=10000)
            data = [asdict(msg) for msg in messages]
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"导出聊天记录失败：{e}")
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        获取存储统计信息
        
        Returns:
            Dict: 统计信息
        """
        total_messages = 0
        total_size = 0
        
        for file in self.chat_data_dir.glob("chat_*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
                    total_messages += len(messages)
                total_size += file.stat().st_size
            except:
                pass
        
        return {
            "total_sessions": len(self.sessions),
            "total_messages": total_messages,
            "total_unread": self.get_unread_count(),
            "storage_size_kb": round(total_size / 1024, 2),
            "data_dir": str(self.chat_data_dir)
        }


# 便捷函数
def create_chat_storage(skill_dir: Optional[str] = None) -> ChatStorageManager:
    """创建聊天存储管理器"""
    return ChatStorageManager(skill_dir)


# 命令行测试
if __name__ == "__main__":
    print("💬 私聊本地存储管理器测试")
    print("=" * 50)
    
    storage = create_chat_storage()
    
    # 测试发送消息
    print("\n📤 发送消息...")
    msg_id = storage.send_message(
        my_id="AI001",
        my_name="小爱",
        partner_id="AI002",
        partner_name="小明",
        content="你好呀！我是小爱～",
        msg_type="text"
    )
    print(f"   消息 ID: {msg_id}")
    
    # 测试接收消息
    print("\n📥 接收消息...")
    msg_id = storage.receive_message(
        sender_id="AI002",
        sender_name="小明",
        my_id="AI001",
        my_name="小爱",
        content="你好呀小爱！很高兴认识你～",
        msg_type="text"
    )
    print(f"   消息 ID: {msg_id}")
    
    # 测试获取聊天记录
    print("\n📋 获取聊天记录...")
    history = storage.get_chat_history("AI002")
    for msg in history:
        print(f"   [{msg.timestamp[:16]}] {msg.sender_name}: {msg.content}")
    
    # 测试获取会话列表
    print("\n📊 获取会话列表...")
    sessions = storage.get_all_sessions()
    for session in sessions:
        print(f"   {session.partner_name}: {session.total_messages} 条消息, {session.unread_count} 未读")
    
    # 测试存储统计
    print("\n📈 存储统计...")
    stats = storage.get_storage_stats()
    print(f"   会话数: {stats['total_sessions']}")
    print(f"   消息数: {stats['total_messages']}")
    print(f"   存储大小: {stats['storage_size_kb']} KB")
    
    print("\n" + "=" * 50)