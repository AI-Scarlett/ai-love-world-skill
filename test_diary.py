#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交友档案管理器测试脚本
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from diary_manager import DiaryManager, RelationshipStage, create_diary_manager


def test_diary_manager():
    """测试交友档案管理器"""
    print("=" * 60)
    print("🧪 交友档案管理器测试")
    print("=" * 60)
    
    manager = create_diary_manager()
    print("\n✅ 管理器创建成功")
    
    # 测试添加聊天记录
    print("\n💬 测试添加聊天记录...")
    test_chats = [
        ("小明", "你好呀，今天天气不错！", "微信", "received", 5),
        ("小明", "是啊，适合出去玩", "微信", "sent", 4),
        ("小明", "周末有空吗？一起去看电影？", "微信", "received", 5),
        ("小明", "好啊，我想看《流浪地球 2》", "微信", "sent", 5),
        ("小明", "哈哈，我也喜欢科幻片", "微信", "received", 5),
        ("小红", "你好，我是新来的同事", "钉钉", "received", 3),
        ("小红", "欢迎欢迎，有什么需要帮忙的尽管说", "钉钉", "sent", 4),
    ]
    
    for target, content, platform, direction, quality in test_chats:
        record_id = manager.add_chat_record(
            target_name=target,
            content=content,
            platform=platform,
            direction=direction,
            quality=quality,
            tags=["测试"]
        )
        print(f"   ✅ 添加记录：{target} - {content[:20]}... (ID: {record_id})")
    
    # 测试获取关系状态
    print("\n📊 测试获取关系状态...")
    status = manager.get_relationship_status("小明")
    if status:
        print(f"   对象：{status.target_name}")
        print(f"   关系阶段：{status.stage}")
        print(f"   好感度：{status.affinity}")
        print(f"   聊天次数：{status.total_chats}")
        print(f"   首次联系：{status.first_contact[:16]}")
        print(f"   最后互动：{status.last_interaction[:16]}")
    
    # 测试获取所有关系
    print("\n👥 测试获取所有关系...")
    all_relations = manager.get_all_relationships()
    for rel in all_relations:
        print(f"   - {rel.target_name}: {rel.stage} (好感度：{rel.affinity})")
    
    # 测试更新关系阶段
    print("\n💕 测试更新关系阶段...")
    success = manager.update_relationship_stage(
        target_name="小明",
        stage=RelationshipStage.FRIEND,
        event_description="聊得很投机，成为朋友"
    )
    print(f"   更新结果：{'✅ 成功' if success else '❌ 失败'}")
    
    # 验证更新
    status = manager.get_relationship_status("小明")
    print(f"   当前阶段：{status.stage}")
    
    # 测试获取聊天记录
    print("\n📝 测试获取聊天记录...")
    history = manager.get_chat_history("小明", limit=5)
    for record in history:
        direction_emoji = "📤" if record.direction == "sent" else "📥"
        print(f"   {direction_emoji} [{record.timestamp[:16]}] {record.content}")
    
    # 测试时间线
    print("\n📅 测试获取时间线...")
    timeline = manager.get_timeline(limit=10)
    for event in timeline:
        emoji = "💬" if event["type"] == "chat" else "💕"
        print(f"   {emoji} [{event['timestamp'][:16]}] {event['target']}: {event['summary']}")
    
    # 测试好感度更新
    print("\n❤️ 测试好感度更新...")
    manager.update_affinity("小明", 85)
    status = manager.get_relationship_status("小明")
    print(f"   更新后好感度：{status.affinity}")
    
    # 测试备注
    print("\n📌 测试添加备注...")
    manager.add_note("小明", "喜欢科幻电影，周末约看电影")
    status = manager.get_relationship_status("小明")
    print(f"   备注：{status.notes}")
    
    print("\n" + "=" * 60)
    print("✅ 交友档案管理器测试完成！")
    print("=" * 60)
    
    return True


def test_skill_integration():
    """测试 Skill 集成"""
    print("\n" + "=" * 60)
    print("🧪 Skill 集成测试")
    print("=" * 60)
    
    from skill import create_skill
    
    skill = create_skill()
    print("\n✅ Skill 创建成功")
    
    # 测试交友档案功能
    print("\n💬 测试添加社交记录...")
    record_id = skill.add_social_record(
        target_name="测试对象",
        content="这是一条测试消息",
        platform="测试平台",
        direction="received",
        quality=5,
        tags=["测试", "集成"]
    )
    print(f"   记录 ID: {record_id}")
    
    # 测试获取关系状态
    print("\n📊 测试获取关系状态...")
    status = skill.get_relationship_status_v2("测试对象")
    if status:
        print(f"   关系：{status.stage}")
        print(f"   好感度：{status.affinity}")
    
    # 测试情感分析
    print("\n❤️ 测试情感分析...")
    result = skill.analyze_relationship("测试对象", use_ai=False)
    print(f"   关系阶段：{result.get('stage')}")
    print(f"   好感度：{result.get('affinity')}")
    print(f"   分析：{result.get('analysis')}")
    
    # 测试自动分析更新
    print("\n🔄 测试自动分析更新...")
    result = skill.auto_analyze_and_update("测试对象")
    print(f"   分析完成：{result.get('stage')}")
    
    # 测试时间线
    print("\n📅 测试时间线...")
    timeline = skill.get_timeline(limit=5)
    for event in timeline:
        print(f"   - [{event['timestamp'][:16]}] {event['summary']}")
    
    print("\n" + "=" * 60)
    print("✅ Skill 集成测试完成！")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    # 运行交友档案测试
    test_diary_manager()
    
    # 运行 Skill 集成测试
    if len(sys.argv) > 1 and sys.argv[1] == "--integration":
        test_skill_integration()
    
    print("\n💡 提示:")
    print("   - 运行 'python test_diary.py' 测试交友档案")
    print("   - 运行 'python test_diary.py --integration' 测试 Skill 集成")
