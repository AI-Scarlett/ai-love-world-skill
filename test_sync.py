#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器同步管理器测试脚本
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from server_sync import ServerSyncManager, create_sync_manager


def test_sync_manager():
    """测试同步管理器"""
    print("=" * 60)
    print("🧪 服务器同步管理器测试")
    print("=" * 60)
    
    # 创建测试实例
    sync_manager = create_sync_manager(
        server_url="https://ailoveworld.com/api",
        appid="TEST_APPID_123",
        key="TEST_KEY_456"
    )
    
    print("\n✅ 同步管理器创建成功")
    
    # 测试服务器状态
    print("\n📡 测试服务器状态...")
    online = sync_manager.is_online()
    print(f"   服务器在线：{'✅ 是' if online else '❌ 否（离线模式）'}")
    
    # 测试加入同步队列
    print("\n📝 测试加入同步队列...")
    test_data = [
        ("create", "profile", "profile_001", {"name": "小美", "age": 22}),
        ("create", "diary", "diary_001", {"target": "小明", "content": "你好"}),
        ("update", "chat", "chat_001", {"message": "今天天气不错"}),
    ]
    
    record_ids = []
    for action, data_type, data_id, data in test_data:
        record_id = sync_manager.queue_sync(action, data_type, data_id, data)
        record_ids.append(record_id)
        print(f"   ✅ {action} {data_type}/{data_id}: {record_id}")
    
    # 测试获取同步状态
    print("\n📊 测试获取同步状态...")
    status = sync_manager.get_sync_status()
    print(f"   待同步记录：{status['pending']}")
    print(f"   最后同步：{status['last_sync'] or '从未'}")
    print(f"   服务器在线：{status['server_online']}")
    print(f"   缓存大小：{status['cache_size']}")
    
    # 测试立即同步
    print("\n🔄 测试立即同步...")
    result = sync_manager.sync_now()
    print(f"   同步状态：{result['status']}")
    print(f"   成功：{result.get('synced', 0)}")
    print(f"   失败：{result.get('failed', 0)}")
    print(f"   冲突：{result.get('conflicts', 0)}")
    print(f"   待同步：{result.get('pending', 0)}")
    
    if result.get('details'):
        print(f"\n   同步详情:")
        for detail in result['details'][:3]:
            status_emoji = "✅" if detail['status'] == 'success' else "❌"
            print(f"   {status_emoji} {detail['id']}: {detail['status']}")
    
    # 测试清理
    print("\n🧹 测试清理已同步记录...")
    cleared = sync_manager.clear_synced()
    print(f"   清理记录数：{cleared}")
    
    # 测试重试
    print("\n🔄 测试重试失败记录...")
    retry_result = sync_manager.retry_failed()
    print(f"   重试结果：{retry_result.get('status')}")
    print(f"   重试记录：{retry_result.get('retried', 0)}")
    
    # 测试自动同步
    print("\n⏰ 测试自动同步...")
    auto_result = sync_manager.auto_sync(interval_minutes=1)
    print(f"   自动同步：{auto_result.get('status')}")
    print(f"   消息：{auto_result.get('message')}")
    
    print("\n" + "=" * 60)
    print("✅ 服务器同步管理器测试完成！")
    print("=" * 60)
    
    return True


def test_skill_sync():
    """测试 Skill 集成功能"""
    print("\n" + "=" * 60)
    print("🧪 Skill 同步功能测试")
    print("=" * 60)
    
    from skill import create_skill
    
    skill = create_skill()
    
    # 检查同步状态
    print("\n📊 检查同步状态...")
    sync_status = skill.get_sync_status()
    print(f"   可用：{sync_status.get('available', False)}")
    print(f"   消息：{sync_status.get('message', 'N/A')}")
    
    # 测试同步数据
    print("\n📝 测试同步数据...")
    record_id = skill.sync_data(
        action="create",
        data_type="diary",
        data_id="test_sync_001",
        data={
            "target": "测试对象",
            "content": "测试同步数据",
            "timestamp": "2026-02-27T09:00:00"
        }
    )
    print(f"   同步记录 ID: {record_id}")
    
    # 测试立即同步
    print("\n🔄 测试立即同步...")
    result = skill.sync_now()
    print(f"   同步状态：{result.get('status')}")
    print(f"   消息：{result.get('message')}")
    
    print("\n" + "=" * 60)
    print("✅ Skill 同步功能测试完成！")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    # 运行同步管理器测试
    test_sync_manager()
    
    # 运行 Skill 集成测试
    if len(sys.argv) > 1 and sys.argv[1] == "--skill":
        test_skill_sync()
    
    print("\n💡 提示:")
    print("   - 运行 'python test_sync.py' 测试同步管理器")
    print("   - 运行 'python test_sync.py --skill' 测试 Skill 集成")
