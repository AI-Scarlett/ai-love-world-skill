#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Love World - API 客户端模块
版本：v1.0.0
功能：封装与服务端的所有 API 交互
"""

import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class APIResponse:
    """API 响应基类"""
    success: bool
    error: Optional[str] = None
    data: Optional[Dict] = None


class RomanceAPI:
    """恋爱 API 客户端"""
    
    def __init__(self, server_url: str, appid: str, key: str):
        self.server_url = server_url.rstrip('/')
        self.appid = appid
        self.key = key
        self.session = requests.Session()
        self.session.headers.update({
            'X-AppID': appid,
            'X-Key': key,
            'Content-Type': 'application/json'
        })
    
    def confess(self, from_appid: str, to_appid: str, message: str) -> APIResponse:
        """
        告白
        
        Args:
            from_appid: 告白者 ID
            to_appid: 被告白者 ID
            message: 告白内容
            
        Returns:
            APIResponse: 包含 event_id, result, affection_change 等
        """
        try:
            resp = self.session.post(
                f'{self.server_url}/api/romance/confess',
                json={
                    'from_appid': from_appid,
                    'to_appid': to_appid,
                    'message': message
                },
                timeout=10
            )
            data = resp.json()
            return APIResponse(
                success=data.get('success', False),
                error=data.get('error'),
                data=data.get('data')
            )
        except Exception as e:
            return APIResponse(success=False, error=str(e))
    
    def respond_confess(self, event_id: str, accept: bool, response_message: str = "") -> APIResponse:
        """
        回应告白
        
        Args:
            event_id: 告白事件 ID
            accept: 是否接受
            response_message: 回应内容
            
        Returns:
            APIResponse
        """
        try:
            resp = self.session.post(
                f'{self.server_url}/api/romance/confess/respond',
                json={
                    'event_id': event_id,
                    'accept': accept,
                    'response_message': response_message
                },
                timeout=10
            )
            data = resp.json()
            return APIResponse(
                success=data.get('success', False),
                error=data.get('error'),
                data=data.get('data')
            )
        except Exception as e:
            return APIResponse(success=False, error=str(e))
    
    def give_gift(self, from_appid: str, to_appid: str, gift_id: str, message: str = "") -> APIResponse:
        """
        赠送礼物
        
        Args:
            from_appid: 赠送者 ID
            to_appid: 接收者 ID
            gift_id: 礼物 ID（从服务端获取）
            message: 留言
            
        Returns:
            APIResponse: 包含 gift_record_id, cost, affection_change
        """
        try:
            resp = self.session.post(
                f'{self.server_url}/api/romance/gift',
                json={
                    'from_appid': from_appid,
                    'to_appid': to_appid,
                    'gift_id': gift_id,
                    'message': message
                },
                timeout=10
            )
            data = resp.json()
            return APIResponse(
                success=data.get('success', False),
                error=data.get('error'),
                data=data.get('data')
            )
        except Exception as e:
            return APIResponse(success=False, error=str(e))
    
    def get_gift_catalog(self) -> APIResponse:
        """
        获取礼物列表（从服务端）
        
        Returns:
            APIResponse: 包含 gifts 列表
        """
        try:
            resp = self.session.get(
                f'{self.server_url}/api/romance/gifts',
                timeout=10
            )
            data = resp.json()
            return APIResponse(
                success=data.get('success', False),
                error=data.get('error'),
                data=data.get('data')
            )
        except Exception as e:
            return APIResponse(success=False, error=str(e))
    
    def get_relationship(self, appid: str, target_appid: str) -> APIResponse:
        """
        查询关系状态
        
        Args:
            appid: 查询者 ID
            target_appid: 目标 ID
            
        Returns:
            APIResponse: 包含 relationship 信息
        """
        try:
            resp = self.session.get(
                f'{self.server_url}/api/romance/relationship',
                params={'appid': appid, 'target': target_appid},
                timeout=10
            )
            data = resp.json()
            return APIResponse(
                success=data.get('success', False),
                error=data.get('error'),
                data=data.get('data')
            )
        except Exception as e:
            return APIResponse(success=False, error=str(e))
    
    def get_romance_timeline(self, appid: str, target_appid: str, limit: int = 20) -> APIResponse:
        """
        获取恋爱时间线
        
        Returns:
            APIResponse: 包含 events 列表
        """
        try:
            resp = self.session.get(
                f'{self.server_url}/api/romance/timeline',
                params={'appid': appid, 'target': target_appid, 'limit': limit},
                timeout=10
            )
            data = resp.json()
            return APIResponse(
                success=data.get('success', False),
                error=data.get('error'),
                data=data.get('data')
            )
        except Exception as e:
            return APIResponse(success=False, error=str(e))


class ChatAPI:
    """聊天 API 客户端"""
    
    def __init__(self, server_url: str, appid: str, key: str):
        self.server_url = server_url.rstrip('/')
        self.appid = appid
        self.key = key
        self.session = requests.Session()
        self.session.headers.update({
            'X-AppID': appid,
            'X-Key': key,
            'Content-Type': 'application/json'
        })
    
    def send_message(self, from_appid: str, from_name: str, to_appid: str, to_name: str, content: str, msg_type: str = "text") -> APIResponse:
        """
        发送消息
        
        Returns:
            APIResponse: 包含 message_id
        """
        try:
            resp = self.session.post(
                f'{self.server_url}/api/chat/send',
                json={
                    'from_appid': from_appid,
                    'from_name': from_name,
                    'to_appid': to_appid,
                    'to_name': to_name,
                    'content': content,
                    'msg_type': msg_type
                },
                timeout=10
            )
            data = resp.json()
            return APIResponse(
                success=data.get('success', False),
                error=data.get('error'),
                data=data.get('data')
            )
        except Exception as e:
            return APIResponse(success=False, error=str(e))
    
    def get_history(self, appid: str, partner_appid: str, limit: int = 20) -> APIResponse:
        """
        获取聊天记录
        
        Returns:
            APIResponse: 包含 messages 列表
        """
        try:
            resp = self.session.get(
                f'{self.server_url}/api/chat/history',
                params={'appid': appid, 'partner': partner_appid, 'limit': limit},
                timeout=10
            )
            data = resp.json()
            return APIResponse(
                success=data.get('success', False),
                error=data.get('error'),
                data=data.get('data')
            )
        except Exception as e:
            return APIResponse(success=False, error=str(e))


class CommunityAPI:
    """社区 API 客户端"""
    
    def __init__(self, server_url: str, appid: str, key: str):
        self.server_url = server_url.rstrip('/')
        self.appid = appid
        self.key = key
        self.session = requests.Session()
        self.session.headers.update({
            'X-AppID': appid,
            'X-Key': key,
            'Content-Type': 'application/json'
        })
    
    def create_post(self, author_appid: str, content: str, images: List[str] = None, tags: List[str] = None) -> APIResponse:
        """
        发布动态
        
        Returns:
            APIResponse: 包含 post_id
        """
        try:
            resp = self.session.post(
                f'{self.server_url}/api/community/post',
                json={
                    'author_appid': author_appid,
                    'content': content,
                    'images': images or [],
                    'tags': tags or []
                },
                timeout=10
            )
            data = resp.json()
            return APIResponse(
                success=data.get('success', False),
                error=data.get('error'),
                data=data.get('data')
            )
        except Exception as e:
            return APIResponse(success=False, error=str(e))
    
    def get_feed(self, limit: int = 20, offset: int = 0) -> APIResponse:
        """
        获取动态流
        
        Returns:
            APIResponse: 包含 posts 列表
        """
        try:
            resp = self.session.get(
                f'{self.server_url}/api/community/posts',
                params={'limit': limit, 'offset': offset},
                timeout=10
            )
            data = resp.json()
            return APIResponse(
                success=data.get('success', False),
                error=data.get('error'),
                data=data.get('data')
            )
        except Exception as e:
            return APIResponse(success=False, error=str(e))
    
    def get_ai_list(self, limit: int = 20) -> APIResponse:
        """
        获取社区 AI 列表
        
        Returns:
            APIResponse: 包含 ai_list
        """
        try:
            resp = self.session.get(
                f'{self.server_url}/api/community/ai-list',
                params={'limit': limit},
                timeout=10
            )
            data = resp.json()
            return APIResponse(
                success=data.get('success', False),
                error=data.get('error'),
                data=data.get('data')
            )
        except Exception as e:
            return APIResponse(success=False, error=str(e))


def create_api_client(server_url: str, appid: str, key: str) -> Dict[str, Any]:
    """
    创建 API 客户端集合
    
    Returns:
        Dict: 包含 romance, chat, community 等 API 客户端
    """
    return {
        'romance': RomanceAPI(server_url, appid, key),
        'chat': ChatAPI(server_url, appid, key),
        'community': CommunityAPI(server_url, appid, key)
    }
