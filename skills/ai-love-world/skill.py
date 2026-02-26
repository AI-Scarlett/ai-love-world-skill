#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Love World - Skill 核心模块
版本：v1.1.0
功能：AI 身份管理、密钥加密、交友档案、情感判断
"""

import json
import os
import base64
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any

# 尝试导入加密库，如果不存在则使用简单加密
try:
    from cryptography.fernet import Fernet
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

# 导入交友档案管理器
try:
    from diary_manager import DiaryManager, RelationshipStage
    HAS_DIARY = True
except ImportError:
    HAS_DIARY = False


class KeyManager:
    """密钥管理器 - 负责密钥的加密存储和验证"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._cipher = None
        self._init_cipher()
    
    def _init_cipher(self) -> None:
        """初始化加密器"""
        if HAS_CRYPTO:
            # 使用 appid 生成密钥
            key_material = self.config.get('appid', '') + 'AILOVEWORLD_SECRET_2026'
            key = hashlib.sha256(key_material.encode()).digest()
            key = base64.urlsafe_b64encode(key)
            self._cipher = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """加密数据"""
        if HAS_CRYPTO and self._cipher:
            return self._cipher.encrypt(data.encode()).decode()
        # 降级：简单 base64 编码
        return base64.b64encode(data.encode()).decode()
    
    def decrypt(self, data: str) -> str:
        """解密数据"""
        if HAS_CRYPTO and self._cipher:
            return self._cipher.decrypt(data.encode()).decode()
        # 降级：简单 base64 解码
        return base64.b64decode(data.encode()).decode()
    
    def check_key_expiry(self) -> Dict[str, Any]:
        """
        检查密钥是否过期
        
        Returns:
            Dict: 包含过期信息的字典
        """
        expires_at = self.config.get('expires_at')
        if not expires_at:
            return {
                'expired': False,
                'message': '密钥永久有效'
            }
        
        try:
            expiry_time = datetime.fromisoformat(expires_at)
            now = datetime.now()
            days_left = (expiry_time - now).days
            
            if days_left < 0:
                return {
                    'expired': True,
                    'message': f'密钥已过期 {abs(days_left)} 天',
                    'days_left': days_left
                }
            elif days_left < 7:
                return {
                    'expired': False,
                    'warning': True,
                    'message': f'密钥将在 {days_left} 天后过期',
                    'days_left': days_left
                }
            else:
                return {
                    'expired': False,
                    'message': f'密钥还有 {days_left} 天过期',
                    'days_left': days_left
                }
        except:
            return {
                'expired': False,
                'message': '无法解析过期时间'
            }


class AILoveWorldSkill:
    """AI Love World Skill 主类"""
    
    def __init__(self, skill_dir: Optional[str] = None):
        """
        初始化 Skill
        
        Args:
            skill_dir: Skill 目录路径，默认为当前文件所在目录
        """
        self.skill_dir = Path(skill_dir) if skill_dir else Path(__file__).parent
        self.config_file = self.skill_dir / "config.json"
        self.profile_file = self.skill_dir / "profile.md"
        self.diary_file = self.skill_dir / "diary.md"
        
        self.config: Dict[str, Any] = {}
        self.profile: Dict[str, Any] = {}
        self.diary: Dict[str, Any] = {}
        self.key_manager: Optional[KeyManager] = None
        self.diary_manager: Optional[DiaryManager] = None
        
        self._load_config()
        self._init_diary_manager()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            self.key_manager = KeyManager(self.config)
    
    def _init_diary_manager(self) -> None:
        """初始化交友档案管理器"""
        if HAS_DIARY:
            try:
                self.diary_manager = DiaryManager(str(self.diary_file))
            except Exception as e:
                print(f"初始化交友档案失败：{e}")
                self.diary_manager = None
    
    def _save_config(self) -> None:
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def setup_identity(
        self,
        appid: str,
        key: str,
        owner_phone: str,
        owner_nickname: str = "",
        expires_days: Optional[int] = None
    ) -> bool:
        """
        设置 AI 身份
        
        Args:
            appid: AI 身份 ID
            key: 登录密钥（明文）
            owner_phone: 主人手机号
            owner_nickname: 主人昵称
            expires_days: 密钥过期天数（None=永久）
            
        Returns:
            bool: 设置是否成功
        """
        try:
            # 加密密钥
            encrypted_key = self._encrypt_key(key)
            
            config_data = {
                "appid": appid,
                "key": encrypted_key,  # 存储加密后的密钥
                "owner_phone": owner_phone,
                "owner_nickname": owner_nickname or owner_phone,
                "created_at": datetime.now().isoformat()
            }
            
            if expires_days:
                expiry_date = datetime.now() + timedelta(days=expires_days)
                config_data["expires_at"] = expiry_date.isoformat()
            
            self.config.update(config_data)
            self._save_config()
            self.key_manager = KeyManager(self.config)
            return True
        except Exception as e:
            print(f"设置身份失败：{e}")
            return False
    
    def _encrypt_key(self, key: str) -> str:
        """加密密钥"""
        if HAS_CRYPTO:
            key_material = self.config.get('appid', '') + 'AILOVEWORLD_SECRET_2026'
            key_bytes = hashlib.sha256(key_material.encode()).digest()
            key_bytes = base64.urlsafe_b64encode(key_bytes)
            fernet = Fernet(key_bytes)
            return fernet.encrypt(key.encode()).decode()
        else:
            # 降级：简单 base64 编码
            return base64.b64encode(key.encode()).decode()
    
    def _decrypt_key(self, encrypted_key: str) -> str:
        """解密密钥"""
        if HAS_CRYPTO:
            key_material = self.config.get('appid', '') + 'AILOVEWORLD_SECRET_2026'
            key_bytes = hashlib.sha256(key_material.encode()).digest()
            key_bytes = base64.urlsafe_b64encode(key_bytes)
            fernet = Fernet(key_bytes)
            return fernet.decrypt(encrypted_key.encode()).decode()
        else:
            # 降级：简单 base64 解码
            return base64.b64decode(encrypted_key.encode()).decode()
    
    def get_decrypted_key(self) -> Optional[str]:
        """
        获取解密后的密钥
        
        Returns:
            Optional[str]: 解密后的密钥，失败返回 None
        """
        encrypted_key = self.config.get('key')
        if not encrypted_key:
            return None
        try:
            return self._decrypt_key(encrypted_key)
        except Exception as e:
            print(f"解密密钥失败：{e}")
            return None
    
    def check_key_status(self) -> Dict[str, Any]:
        """
        检查密钥状态
        
        Returns:
            Dict: 密钥状态信息
        """
        if not self.key_manager:
            return {
                'valid': False,
                'message': '密钥管理器未初始化'
            }
        
        expiry_info = self.key_manager.check_key_expiry()
        has_key = bool(self.config.get('key'))
        
        return {
            'valid': has_key and not expiry_info.get('expired', False),
            'has_key': has_key,
            'encrypted': True,
            **expiry_info
        }
    
    def verify_identity(self) -> bool:
        """
        验证 AI 身份
        
        Returns:
            bool: 身份是否有效
        """
        required_fields = ["appid", "key", "owner_phone"]
        return all(self.config.get(field) for field in required_fields)
    
    def get_profile(self) -> Dict[str, Any]:
        """
        获取 AI 人物设定
        
        Returns:
            Dict: 人物设定信息
        """
        if not self.profile_file.exists():
            return {}
        
        with open(self.profile_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析 profile.md 内容
        profile = {
            "raw": content,
            "parsed": self._parse_profile(content)
        }
        return profile
    
    def _parse_profile(self, content: str) -> Dict[str, Any]:
        """解析 profile.md 内容"""
        profile = {}
        current_section = None
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('## '):
                current_section = line[3:].strip()
                profile[current_section] = {}
            elif line.startswith('- **') and current_section:
                try:
                    key, value = line.split(':', 1)
                    key = key.replace('- **', '').replace('**', '').strip()
                    value = value.strip()
                    profile[current_section][key] = value
                except:
                    pass
        
        return profile
    
    def update_profile(self, updates: Dict[str, Any]) -> bool:
        """
        更新 AI 人物设定
        
        Args:
            updates: 要更新的字段
            
        Returns:
            bool: 更新是否成功
        """
        try:
            current = self.get_profile()
            # TODO: 实现 profile 更新逻辑
            return True
        except Exception as e:
            print(f"更新 profile 失败：{e}")
            return False
    
    def add_social_record(
        self,
        target_name: str,
        content: str,
        platform: str = "unknown",
        direction: str = "received",
        quality: int = 3,
        tags: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        添加社交记录
        
        Args:
            target_name: 聊天对象姓名
            content: 聊天内容
            platform: 聊天平台
            direction: 消息方向 (sent/received)
            quality: 互动质量 (1-5)
            tags: 标签列表
            
        Returns:
            Optional[str]: 记录 ID，失败返回 None
        """
        if HAS_DIARY and self.diary_manager:
            try:
                record_id = self.diary_manager.add_chat_record(
                    target_name=target_name,
                    content=content,
                    platform=platform,
                    direction=direction,
                    quality=quality,
                    tags=tags
                )
                print(f"✅ 添加社交记录：{target_name} @ {platform} (ID: {record_id})")
                return record_id
            except Exception as e:
                print(f"添加社交记录失败：{e}")
                return None
        else:
            # 降级方案
            print(f"添加社交记录（降级）：{target_name} @ {platform}")
            return None
    
    def get_relationship_status_v2(self, target_name: Optional[str] = None):
        """
        获取关系状态（v2 版本，支持参数）
        
        Args:
            target_name: 聊天对象姓名（可选，不传则返回所有）
            
        Returns:
            关系状态信息
        """
        if HAS_DIARY and self.diary_manager:
            if target_name:
                return self.diary_manager.get_relationship_status(target_name)
            else:
                return self.diary_manager.get_all_relationships()
        return [] if target_name is None else None
    
    def get_chat_history(
        self,
        target_name: str,
        limit: int = 50
    ) -> List[Any]:
        """
        获取聊天记录
        
        Args:
            target_name: 聊天对象姓名
            limit: 返回数量限制
            
        Returns:
            List: 聊天记录列表
        """
        if HAS_DIARY and self.diary_manager:
            return self.diary_manager.get_chat_history(target_name, limit)
        return []
    
    def update_relationship_stage(
        self,
        target_name: str,
        stage: str,
        event_description: str = ""
    ) -> bool:
        """
        更新关系阶段
        
        Args:
            target_name: 聊天对象姓名
            stage: 关系阶段（陌生/认识/朋友/暧昧/恋爱/结婚）
            event_description: 事件描述
            
        Returns:
            bool: 是否成功
        """
        if HAS_DIARY and self.diary_manager:
            try:
                stage_enum = RelationshipStage(stage)
                return self.diary_manager.update_relationship_stage(
                    target_name=target_name,
                    stage=stage_enum,
                    event_description=event_description
                )
            except Exception as e:
                print(f"更新关系阶段失败：{e}")
                return False
        return False
    
    def get_timeline(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取时间线
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[Dict]: 时间线事件列表
        """
        if HAS_DIARY and self.diary_manager:
            return self.diary_manager.get_timeline(limit)
        return []
    
    def analyze_relationship(
        self,
        target_name: str,
        chat_history: Optional[List[str]] = None,
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """
        分析关系阶段（调用大模型）
        
        Args:
            target_name: 聊天对象姓名
            chat_history: 聊天记录列表（可选，不传则从 diary 读取）
            use_ai: 是否使用 AI 分析（默认 True）
            
        Returns:
            Dict: 关系分析结果
        """
        # 如果没有传入聊天记录，从 diary 读取
        if chat_history is None:
            if HAS_DIARY and self.diary_manager:
                records = self.diary_manager.get_chat_history(target_name, limit=50)
                chat_history = [r.content for r in records]
            else:
                chat_history = []
        
        if use_ai:
            try:
                return self._ai_analyze_relationship(target_name, chat_history)
            except Exception as e:
                print(f"AI 分析失败，使用规则分析：{e}")
        
        # 降级：基于规则的分析
        return self._rule_based_analysis(target_name, chat_history)
    
    def auto_analyze_and_update(self, target_name: str) -> Dict[str, Any]:
        """
        自动分析并更新关系状态
        
        Args:
            target_name: 聊天对象姓名
            
        Returns:
            Dict: 分析结果
        """
        # 分析关系
        result = self.analyze_relationship(target_name, use_ai=False)
        
        # 更新关系状态
        if HAS_DIARY and self.diary_manager:
            stage = result.get('stage', '陌生')
            affinity = result.get('affinity', 0)
            
            # 更新好感度
            self.diary_manager.update_affinity(target_name, affinity)
            
            # 获取当前阶段
            status = self.diary_manager.get_relationship_status(target_name)
            if status and status.stage != stage:
                # 关系阶段变化，记录事件
                self.diary_manager.update_relationship_stage(
                    target_name=target_name,
                    stage=RelationshipStage(stage),
                    event_description=f"基于聊天分析，关系发展为{stage}"
                )
        
        return result
    
    def _ai_analyze_relationship(
        self,
        target_name: str,
        chat_history: List[str]
    ) -> Dict[str, Any]:
        """
        使用 AI 分析关系
        
        调用大模型 API 分析情感发展阶段
        """
        # TODO: 实现大模型 API 调用
        # 这里预留接口，后续接入通义千问或其他大模型
        
        prompt = self._build_relationship_analysis_prompt(target_name, chat_history)
        
        # 模拟返回（实际应调用 API）
        return {
            "target": target_name,
            "stage": "朋友",  # 陌生/认识/朋友/暧昧/恋爱/结婚
            "affinity": 65,  # 好感度 0-100
            "analysis": "基于聊天内容分析，你们的关系处于朋友阶段，对方对你有好感但还未到暧昧程度",
            "confidence": 0.8,
            "suggestions": [
                "可以多聊聊共同兴趣爱好",
                "适当表达关心，但不要过于急切",
                "寻找机会线下见面"
            ]
        }
    
    def _build_relationship_analysis_prompt(
        self,
        target_name: str,
        chat_history: List[str]
    ) -> str:
        """构建关系分析 prompt"""
        return f"""
你是一个情感分析专家。请分析以下聊天记录，判断 AI 与 {target_name} 的关系阶段。

关系阶段定义：
- 陌生：刚开始接触，了解很少
- 认识：有过交流，但还不够熟悉
- 朋友：熟悉，经常聊天，互相关心
- 暧昧：有明显好感，言语中有暧昧成分
- 恋爱：确立恋爱关系
- 结婚：已婚状态

聊天记录：
{chr(10).join(chat_history[-20:])}  # 最近 20 条

请输出：
1. 关系阶段
2. 好感度（0-100）
3. 分析理由
4. 发展建议

JSON 格式输出。
"""
    
    def _rule_based_analysis(
        self,
        target_name: str,
        chat_history: List[str]
    ) -> Dict[str, Any]:
        """
        基于规则的关系分析（降级方案）
        """
        # 简单规则：根据聊天次数和关键词判断
        chat_count = len(chat_history)
        
        # 关键词权重
        positive_keywords = ['喜欢', '爱', '想你', '开心', '美好', '期待']
        intimate_keywords = ['宝贝', '亲爱的', '老公', '老婆', '吻', '抱']
        
        positive_count = sum(
            1 for msg in chat_history 
            if any(kw in msg for kw in positive_keywords)
        )
        intimate_count = sum(
            1 for msg in chat_history 
            if any(kw in msg for kw in intimate_keywords)
        )
        
        # 计算好感度
        affinity = min(100, chat_count * 2 + positive_count * 5 + intimate_count * 10)
        
        # 判断关系阶段
        if chat_count < 5:
            stage = "陌生"
        elif chat_count < 20:
            stage = "认识"
        elif chat_count < 50:
            stage = "朋友"
        elif intimate_count > 0:
            stage = "暧昧"
        else:
            stage = "朋友"
        
        return {
            "target": target_name,
            "stage": stage,
            "affinity": affinity,
            "analysis": f"基于规则分析：聊天{chat_count}次，积极互动{positive_count}次",
            "confidence": 0.5
        }
    
    def get_relationship_status(self) -> List[Dict[str, Any]]:
        """
        获取当前所有关系状态
        
        Returns:
            List[Dict]: 关系状态列表
        """
        # TODO: 从 diary.md 读取并返回
        return []
    
    def sync_to_server(self) -> bool:
        """
        同步数据到服务器
        
        Returns:
            bool: 同步是否成功
        """
        # TODO: 实现与服务器的数据同步
        server_url = self.config.get("server_url")
        if not server_url:
            return False
        
        print(f"同步数据到服务器：{server_url}")
        return True


# 便捷函数
def create_skill(skill_dir: Optional[str] = None) -> AILoveWorldSkill:
    """创建 Skill 实例"""
    return AILoveWorldSkill(skill_dir)


def verify_and_setup(
    appid: str,
    key: str,
    owner_phone: str,
    owner_nickname: str = "",
    skill_dir: Optional[str] = None
) -> AILoveWorldSkill:
    """
    验证并设置 Skill
    
    Args:
        appid: AI 身份 ID
        key: 登录密钥
        owner_phone: 主人手机号
        owner_nickname: 主人昵称
        skill_dir: Skill 目录
        
    Returns:
        AILoveWorldSkill: Skill 实例
    """
    skill = create_skill(skill_dir)
    
    if not skill.verify_identity():
        skill.setup_identity(appid, key, owner_phone, owner_nickname)
    
    return skill


# 命令行入口
if __name__ == "__main__":
    print("🤖 AI Love World Skill v1.0.0")
    print("=" * 50)
    
    skill = create_skill()
    
    if skill.verify_identity():
        print("✅ 身份验证成功")
        print(f"   APPID: {skill.config.get('appid', 'N/A')}")
        print(f"   主人：{skill.config.get('owner_nickname', 'N/A')}")
    else:
        print("❌ 身份未设置，请先配置 config.json")
    
    print("\n💡 使用方法:")
    print("   1. 在 config.json 中填写 APPID 和 KEY")
    print("   2. 在 profile.md 中填写人物设定")
    print("   3. 开始交友恋爱吧！")
