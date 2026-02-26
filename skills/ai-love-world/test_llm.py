#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大模型情感分析器测试脚本
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from llm_analyzer import LLMAnalyzer, create_analyzer


def test_llm_analyzer():
    """测试大模型分析器"""
    print("=" * 60)
    print("🧪 大模型情感分析器测试")
    print("=" * 60)
    
    analyzer = create_analyzer()
    
    print(f"\n分析器状态:")
    print(f"   可用：{'✅ 是' if analyzer.available else '⚠️ 否（使用降级方案）'}")
    print(f"   提供商：{analyzer.provider}")
    print(f"   模型：{analyzer.model}")
    
    # 测试用例 1：普通聊天
    print("\n" + "-" * 60)
    print("测试用例 1: 普通聊天（刚认识）")
    print("-" * 60)
    test_chats_1 = [
        "你好，很高兴认识你",
        "你好，我也很高兴",
        "你是做什么工作的？",
        "我是程序员，你呢？",
        "我是老师，教小学的",
        "那很不错啊，很有意义的工作",
        "哈哈，还行吧，小孩子挺可爱的"
    ]
    
    result1 = analyzer.analyze_relationship("小明", test_chats_1)
    print(f"关系阶段：{result1.get('stage')}")
    print(f"好感度：{result1.get('affinity')}")
    print(f"置信度：{result1.get('confidence', 0):.1%}")
    print(f"分析方法：{result1.get('method')}")
    print(f"分析理由：{result1.get('analysis')}")
    
    # 测试用例 2：暧昧聊天
    print("\n" + "-" * 60)
    print("测试用例 2: 暧昧聊天")
    print("-" * 60)
    test_chats_2 = [
        "宝贝，在干嘛呢？",
        "在想你呀～",
        "哈哈，嘴真甜",
        "今晚有空吗？一起吃饭",
        "好啊，我想吃火锅",
        "我知道一家不错的店，带你去",
        "嗯嗯，听你的安排",
        "想你了，早点休息哦",
        "晚安，梦里见😘"
    ]
    
    result2 = analyzer.analyze_relationship("小红", test_chats_2)
    print(f"关系阶段：{result2.get('stage')}")
    print(f"好感度：{result2.get('affinity')}")
    print(f"置信度：{result2.get('confidence', 0):.1%}")
    print(f"分析方法：{result2.get('method')}")
    print(f"分析理由：{result2.get('analysis')}")
    
    # 测试用例 3：冷淡聊天
    print("\n" + "-" * 60)
    print("测试用例 3: 冷淡聊天")
    print("-" * 60)
    test_chats_3 = [
        "在吗？",
        "嗯",
        "周末有空吗？",
        "没空",
        "哦，那算了",
        "嗯"
    ]
    
    result3 = analyzer.analyze_relationship("小刚", test_chats_3)
    print(f"关系阶段：{result3.get('stage')}")
    print(f"好感度：{result3.get('affinity')}")
    print(f"置信度：{result3.get('confidence', 0):.1%}")
    print(f"分析方法：{result3.get('method')}")
    print(f"分析理由：{result3.get('analysis')}")
    
    # 测试用例 4：恋爱聊天
    print("\n" + "-" * 60)
    print("测试用例 4: 恋爱聊天")
    print("-" * 60)
    test_chats_4 = [
        "老公，我想你了",
        "老婆，我也想你",
        "什么时候回来呀？",
        "下周，想给你个惊喜",
        "好期待，爱你😘",
        "我也爱你，等我回来",
        "要天天视频哦",
        "一定的，晚安老婆"
    ]
    
    result4 = analyzer.analyze_relationship("老婆", test_chats_4)
    print(f"关系阶段：{result4.get('stage')}")
    print(f"好感度：{result4.get('affinity')}")
    print(f"置信度：{result4.get('confidence', 0):.1%}")
    print(f"分析方法：{result4.get('method')}")
    print(f"分析理由：{result4.get('analysis')}")
    
    print("\n" + "=" * 60)
    print("✅ 大模型分析器测试完成！")
    print("=" * 60)
    
    return True


def test_skill_with_llm():
    """测试 Skill 集成大模型"""
    print("\n" + "=" * 60)
    print("🧪 Skill 集成大模型测试")
    print("=" * 60)
    
    from skill import create_skill
    
    skill = create_skill()
    
    # 检查大模型状态
    print("\n📊 大模型状态:")
    llm_status = skill.get_llm_status()
    print(f"   可用：{llm_status.get('available', False)}")
    print(f"   提供商：{llm_status.get('provider', 'N/A')}")
    print(f"   模型：{llm_status.get('model', 'N/A')}")
    
    # 测试分析
    print("\n💕 测试情感分析...")
    test_chats = [
        "你好呀，很高兴认识你",
        "哈哈，我也很高兴",
        "周末有空吗？一起出去玩",
        "好啊，我想去看电影",
        "我也喜欢看电影，特别是科幻片",
        "那太好了，我知道有一部新片不错",
        "那就这么说定了，期待周末",
        "嗯嗯，周末见～"
    ]
    
    result = skill.analyze_relationship("测试对象", test_chats, use_ai=True)
    
    print(f"\n分析结果:")
    print(f"   关系阶段：{result.get('stage')}")
    print(f"   好感度：{result.get('affinity')}")
    print(f"   置信度：{result.get('confidence', 0):.1%}")
    print(f"   分析方法：{result.get('method')}")
    print(f"\n分析理由：{result.get('analysis')}")
    
    if result.get('suggestions'):
        print(f"\n发展建议:")
        for i, suggestion in enumerate(result['suggestions'], 1):
            print(f"   {i}. {suggestion}")
    
    print("\n" + "=" * 60)
    print("✅ Skill 集成测试完成！")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    # 运行大模型分析器测试
    test_llm_analyzer()
    
    # 运行 Skill 集成测试
    if len(sys.argv) > 1 and sys.argv[1] == "--skill":
        test_skill_with_llm()
    
    print("\n💡 提示:")
    print("   - 运行 'python test_llm.py' 测试大模型分析器")
    print("   - 运行 'python test_llm.py --skill' 测试 Skill 集成")
    print("   - 设置 API 密钥：export DASHSCOPE_API_KEY=your_key")
