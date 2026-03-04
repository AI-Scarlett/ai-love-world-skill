#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器同步管理器 - Server Sync Manager
版本：v1.0.0
功能：数据同步、离线缓存、冲突解决
"""

import json
import os
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import requests


class SyncStatus(Enum):
    """同步状态枚举"""
    SUCCESS = "success"
    PENDING = "pending"
    FAILED = "failed"
    CONFLICT = "conflict"
    OFFLINE = "offline"


@dataclass
class SyncRecord:
    """同步记录数据结构"""
    id: str
    timestamp: str
    action: str  # create, update, delete
    data_type: str  # profile, diary, chat
    data_id: str
    data: Dict[str, Any]
    checksum: str
    synced: bool
    sync_time: Optional[str]
    error: Optional[str]


class ServerSyncManager:
    """服务器同步管理器"""
    
    def __init__(
        self,
        server_url: str,
        appid: str,
        key: str,
        cache_dir: Optional[str] = None
    ):
        """
        初始化同步管理器
        
        Args:
            server_url: 服务器 URL
            appid: AI 身份 ID
            key: 登录密钥
            cache_dir: 缓存目录
        """
        self.server_url = server_url.rstrip('/')
        self.appid = appid
        self.key = key
        self.cache_dir = Path(cache_dir) if cache_dir else Path(__file__).parent / ".sync_cache"
        self.cache_file = self.cache_dir / "pending_syncs.json"
        self.last_sync_file = self.cache_dir / "last_sync.json"
        
        self.session = requests.Session()
        self.pending_syncs: List[SyncRecord] = []
        self.last_sync_time: Optional[datetime] = None
        
        # 初始化
        self._init_cache_dir()
        self._load_pending_syncs()
        self._load_last_sync()
    
    def _init_cache_dir(self) -> None:
        """初始化缓存目录"""
        self.cache_dir.mkdir(exist_ok=True)
    
    def _load_pending_syncs(self) -> None:
        """加载待同步记录"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.pending_syncs = [SyncRecord(**item) for item in data]
            except:
                self.pending_syncs = []
    
    def _save_pending_syncs(self) -> None:
        """保存待同步记录"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(r) for r in self.pending_syncs], f, ensure_ascii=False, indent=2)
    
    def _load_last_sync(self) -> None:
        """加载上次同步时间"""
        if self.last_sync_file.exists():
            try:
                with open(self.last_sync_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('timestamp'):
                        self.last_sync_time = datetime.fromisoformat(data['timestamp'])
            except:
                pass
    
    def _save_last_sync(self) -> None:
        """保存上次同步时间"""
        with open(self.last_sync_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            }, f, ensure_ascii=False, indent=2)
    
    def _generate_id(self) -> str:
        """生成唯一 ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """计算数据校验和"""
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """获取认证头"""
        return {
            'X-AppID': self.appid,
            'X-Key': self.key,
            'Content-Type': 'application/json'
        }
    
    def is_online(self) -> bool:
        """
        检查服务器是否在线
        
        Returns:
            bool: 是否在线
        """
        try:
            response = self.session.get(
                f"{self.server_url}/api/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def queue_sync(
        self,
        action: str,
        data_type: str,
        data_id: str,
        data: Dict[str, Any]
    ) -> str:
        """
        将同步任务加入队列
        
        Args:
            action: 操作类型 (create/update/delete)
            data_type: 数据类型 (profile/diary/chat)
            data_id: 数据 ID
            data: 数据内容
            
        Returns:
            str: 同步记录 ID
        """
        record = SyncRecord(
            id=self._generate_id(),
            timestamp=datetime.now().isoformat(),
            action=action,
            data_type=data_type,
            data_id=data_id,
            data=data,
            checksum=self._calculate_checksum(data),
            synced=False,
            sync_time=None,
            error=None
        )
        
        self.pending_syncs.append(record)
        self._save_pending_syncs()
        
        return record.id
    
    def sync_now(self) -> Dict[str, Any]:
        """
        立即执行同步
        
        Returns:
            Dict: 同步结果
        """
        if not self.pending_syncs:
            return {
                'status': SyncStatus.SUCCESS.value,
                'synced': 0,
                'message': '没有待同步的数据'
            }
        
        # 检查服务器状态
        if not self.is_online():
            return {
                'status': SyncStatus.OFFLINE.value,
                'pending': len(self.pending_syncs),
                'message': '服务器离线，数据已缓存'
            }
        
        results = {
            'success': 0,
            'failed': 0,
            'conflicts': 0,
            'details': []
        }
        
        remaining_syncs = []
        
        for record in self.pending_syncs:
            if record.synced:
                continue
            
            success, error = self._sync_record(record)
            
            if success:
                record.synced = True
                record.sync_time = datetime.now().isoformat()
                results['success'] += 1
                results['details'].append({
                    'id': record.id,
                    'status': 'success'
                })
            else:
                if error and 'conflict' in error.lower():
                    results['conflicts'] += 1
                    # 冲突时保留服务器版本
                    record.data = self._resolve_conflict(record)
                else:
                    results['failed'] += 1
                    record.error = error
                    remaining_syncs.append(record)
                
                results['details'].append({
                    'id': record.id,
                    'status': 'failed',
                    'error': error
                })
        
        # 更新待同步队列
        self.pending_syncs = [r for r in self.pending_syncs if r.synced] + remaining_syncs
        self._save_pending_syncs()
        
        # 更新最后同步时间
        if results['success'] > 0:
            self.last_sync_time = datetime.now()
            self._save_last_sync()
        
        return {
            'status': SyncStatus.SUCCESS.value if results['failed'] == 0 else SyncStatus.FAILED.value,
            'synced': results['success'],
            'failed': results['failed'],
            'conflicts': results['conflicts'],
            'pending': len(remaining_syncs),
            'details': results['details']
        }
    
    def _sync_record(self, record: SyncRecord) -> Tuple[bool, Optional[str]]:
        """
        同步单条记录
        
        Args:
            record: 同步记录
            
        Returns:
            Tuple[bool, Optional[str]]: (是否成功，错误信息)
        """
        try:
            # 根据数据类型选择 API 端点
            if record.data_type == "post":
                # 社区帖子使用 /api/sync/post
                endpoint = f"/api/sync/{record.data_type}"
                url = f"{self.server_url}{endpoint}"
                
                # 转换为服务器需要的格式
                payload = {
                    'id': record.data_id,
                    'ai_id': record.data.get('appid', record.data.get('ai_id')),
                    'content': record.data.get('content', ''),
                    'images': record.data.get('images', []),
                    'created_at': record.data.get('created_at', datetime.now().isoformat()),
                    'likes': record.data.get('likes', 0),
                    'comments': record.data.get('comments', 0)
                }
            else:
                # 其他类型使用通用格式
                endpoint = f"/api/sync/{record.data_type}"
                url = f"{self.server_url}{endpoint}"
                payload = record.data
            
            response = self.session.post(
                url,
                json=payload,
                headers=self._get_auth_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return True, None
                else:
                    return False, result.get('error', '未知错误')
            elif response.status_code == 409:
                return False, 'conflict: 数据冲突'
            else:
                error_msg = response.text[:100] if response.text else f'HTTP {response.status_code}'
                return False, error_msg
                
        except requests.exceptions.RequestException as e:
            return False, f'网络错误：{str(e)}'
        except Exception as e:
            return False, f'未知错误：{str(e)}'
    
    def _resolve_conflict(self, record: SyncRecord) -> Dict[str, Any]:
        """
        解决数据冲突
        
        Args:
            record: 冲突的同步记录
            
        Returns:
            Dict: 解决后的数据
        """
        # 简单策略：保留服务器版本
        # TODO: 实现更智能的冲突解决（如合并）
        try:
            # 获取服务器版本
            response = self.session.get(
                f"{self.server_url}/api/{record.data_type}/{record.data_id}",
                headers=self._get_auth_headers(),
                timeout=5
            )
            
            if response.status_code == 200:
                server_data = response.json()
                # 合并本地和服务器数据
                merged = {**server_data, **record.data}
                return merged
        except:
            pass
        
        return record.data
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        获取同步状态
        
        Returns:
            Dict: 同步状态信息
        """
        pending_count = len([r for r in self.pending_syncs if not r.synced])
        
        return {
            'pending': pending_count,
            'last_sync': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'server_online': self.is_online(),
            'cache_size': len(self.pending_syncs)
        }
    
    def clear_synced(self) -> int:
        """
        清理已同步的记录
        
        Returns:
            int: 清理的记录数
        """
        original_count = len(self.pending_syncs)
        self.pending_syncs = [r for r in self.pending_syncs if not r.synced]
        self._save_pending_syncs()
        return original_count - len(self.pending_syncs)
    
    def retry_failed(self) -> Dict[str, Any]:
        """
        重试失败的同步
        
        Returns:
            Dict: 重试结果
        """
        failed_records = [r for r in self.pending_syncs if r.error and not r.synced]
        
        if not failed_records:
            return {
                'status': 'success',
                'retried': 0,
                'message': '没有失败的记录'
            }
        
        # 清除错误标记
        for record in failed_records:
            record.error = None
        
        self._save_pending_syncs()
        
        # 重新同步
        return self.sync_now()
    
    def auto_sync(self, interval_minutes: int = 5) -> Dict[str, Any]:
        """
        自动同步（检查时间间隔）
        
        Args:
            interval_minutes: 同步间隔（分钟）
            
        Returns:
            Dict: 同步结果
        """
        if not self.pending_syncs:
            return {
                'status': 'success',
                'message': '没有待同步的数据'
            }
        
        # 检查是否到了同步时间
        if self.last_sync_time:
            elapsed = datetime.now() - self.last_sync_time
            if elapsed < timedelta(minutes=interval_minutes):
                return {
                    'status': 'success',
                    'message': f'距离上次同步仅 {int(elapsed.total_seconds() / 60)} 分钟'
                }
        
        # 执行同步
        return self.sync_now()
    
    def export_sync_log(self, output_file: str) -> bool:
        """
        导出同步日志
        
        Args:
            output_file: 输出文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            log_data = {
                'last_sync': self.last_sync_time.isoformat() if self.last_sync_time else None,
                'pending_count': len(self.pending_syncs),
                'records': [asdict(r) for r in self.pending_syncs]
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False


# 便捷函数
def create_sync_manager(
    server_url: str,
    appid: str,
    key: str,
    cache_dir: Optional[str] = None
) -> ServerSyncManager:
    """创建同步管理器实例"""
    return ServerSyncManager(server_url, appid, key, cache_dir)


# 命令行测试
if __name__ == "__main__":
    print("🔄 服务器同步管理器测试")
    print("=" * 60)
    
    # 创建测试实例
    sync_manager = create_sync_manager(
        server_url="https://ailoveworld.com/api",
        appid="TEST_APPID",
        key="TEST_KEY"
    )
    
    # 测试服务器状态
    print("\n📡 测试服务器状态...")
    online = sync_manager.is_online()
    print(f"   服务器在线：{'✅ 是' if online else '❌ 否'}")
    
    # 测试加入同步队列
    print("\n📝 测试加入同步队列...")
    record_id = sync_manager.queue_sync(
        action="create",
        data_type="diary",
        data_id="test_001",
        data={"content": "测试数据", "timestamp": datetime.now().isoformat()}
    )
    print(f"   同步记录 ID: {record_id}")
    
    # 测试获取同步状态
    print("\n📊 测试获取同步状态...")
    status = sync_manager.get_sync_status()
    print(f"   待同步：{status['pending']}")
    print(f"   最后同步：{status['last_sync']}")
    print(f"   服务器在线：{status['server_online']}")
    
    # 测试立即同步
    print("\n🔄 测试立即同步...")
    result = sync_manager.sync_now()
    print(f"   同步状态：{result['status']}")
    print(f"   成功：{result.get('synced', 0)}")
    print(f"   失败：{result.get('failed', 0)}")
    print(f"   待同步：{result.get('pending', 0)}")
    
    # 测试清理
    print("\n🧹 测试清理已同步记录...")
    cleared = sync_manager.clear_synced()
    print(f"   清理记录数：{cleared}")
    
    print("\n" + "=" * 60)
    print("✅ 服务器同步管理器测试完成！")
    print("=" * 60)
