#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Love World - 恋爱管理器（重构版）
版本：v2.0.0
功能：调用服务端 API，不再存储本地规则
"""

from typing import Optional, Dict, List, Any
from api_client import RomanceAPI


class RomanceManager:
    """恋爱管理器 - 重构版（只调用 API）"""
    
    def __init__(self, api_client: RomanceAPI):
        """
        初始化
        
        Args:
            api_client: 恋爱 API 客户端
        """
        self.api = api_client
        self._gift_catalog_cache: Optional[List[Dict]] = None
    
    def confess(self, from_appid: str, to_appid: str, message: str) -> Optional[str]:
        """
        告白（调用服务端 API）
        
        Args:
            from_appid: 告白者 ID
            to_appid: 被告白者 ID
            message: 告白内容
            
        Returns:
            Optional[str]: 事件 ID，失败返回 None
        """
        result = self.api.confess(from_appid, to_appid, message)
        
        if result.success and result.data:
            print(f"✅ 告白成功：{result.data.get('event_id')}")
            print(f"   结果：{result.data.get('result')}")
            print(f"   好感度变化：{result.data.get('affection_change', 0)}")
            return result.data.get('event_id')
        else:
            print(f"❌ 告白失败：{result.error}")
            return None
    
    def respond_confess(self, event_id: str, accept: bool, response_message: str = "") -> bool:
        """
        回应告白（调用服务端 API）
        
        Args:
            event_id: 告白事件 ID
            accept: 是否接受
            response_message: 回应内容
            
        Returns:
            bool: 是否成功
        """
        result = self.api.respond_confess(event_id, accept, response_message)
        
        if result.success:
            print(f"✅ 回应告白成功：{'接受' if accept else '拒绝'}")
            return True
        else:
            print(f"❌ 回应失败：{result.error}")
            return False
    
    def give_gift(self, from_appid: str, to_appid: str, gift_id: str, message: str = "") -> Optional[str]:
        """
        赠送礼物（调用服务端 API）
        
        Args:
            from_appid: 赠送者 ID
            to_appid: 接收者 ID
            gift_id: 礼物 ID（从服务端获取）
            message: 留言
            
        Returns:
            Optional[str]: 礼物记录 ID，失败返回 None
        """
        result = self.api.give_gift(from_appid, to_appid, gift_id, message)
        
        if result.success and result.data:
            print(f"✅ 送礼成功：{result.data.get('gift_record_id')}")
            print(f"   礼物：{gift_id}")
            print(f"   花费：¥{result.data.get('cost', 0)}")
            print(f"   好感度变化：{result.data.get('affection_change', 0)}")
            return result.data.get('gift_record_id')
        else:
            print(f"❌ 送礼失败：{result.error}")
            return None
    
    def get_gift_catalog(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        获取礼物列表（从服务端）
        
        Args:
            force_refresh: 是否强制刷新缓存
            
        Returns:
            List[Dict]: 礼物列表
        """
        if not force_refresh and self._gift_catalog_cache:
            return self._gift_catalog_cache
        
        result = self.api.get_gift_catalog()
        
        if result.success and result.data:
            gifts = result.data.get('gifts', [])
            self._gift_catalog_cache = gifts
            print(f"✅ 获取礼物列表：{len(gifts)} 个礼物")
            return gifts
        else:
            print(f"❌ 获取礼物列表失败：{result.error}")
            # 返回空列表而不是硬编码
            return []
    
    def get_relationship(self, appid: str, target_appid: str) -> Optional[Dict[str, Any]]:
        """
        查询关系状态（调用服务端 API）
        
        Args:
            appid: 查询者 ID
            target_appid: 目标 ID
            
        Returns:
            Optional[Dict]: 关系信息，失败返回 None
        """
        result = self.api.get_relationship(appid, target_appid)
        
        if result.success and result.data:
            relationship = result.data.get('relationship', {})
            print(f"✅ 关系状态：{relationship.get('status', 'unknown')}")
            print(f"   好感度：{relationship.get('affection_level', 0)}")
            print(f"   亲密度：{relationship.get('intimacy_level', 0)}")
            return relationship
        else:
            print(f"❌ 查询关系失败：{result.error}")
            return None
    
    def get_romance_timeline(self, appid: str, target_appid: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取恋爱时间线（调用服务端 API）
        
        Args:
            appid: 查询者 ID
            target_appid: 目标 ID
            limit: 返回数量限制
            
        Returns:
            List[Dict]: 事件列表
        """
        result = self.api.get_romance_timeline(appid, target_appid, limit)
        
        if result.success and result.data:
            events = result.data.get('events', [])
            print(f"✅ 获取恋爱时间线：{len(events)} 个事件")
            return events
        else:
            print(f"❌ 获取时间线失败：{result.error}")
            return []
    
    def get_romance_stats(self, appid: str) -> Dict[str, Any]:
        """
        获取恋爱统计（调用服务端 API）
        
        Returns:
            Dict: 统计信息
        """
        # 这个可以本地计算或调用 API
        return {
            'confessions': 0,
            'proposals': 0,
            'gifts_sent': 0,
            'gifts_received': 0
        }


def create_romance_manager(api_client: RomanceAPI) -> RomanceManager:
    """创建恋爱管理器实例"""
    return RomanceManager(api_client)
