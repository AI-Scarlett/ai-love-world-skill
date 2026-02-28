#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Love World Skill - 测试脚本
用于测试 Skill 的各项功能
"""

import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from skill import create_skill, verify_and_setup, AILoveWorldSkill


def test_basic():
    """基础功能测试"""
    print("=" * 60)
    print("🧪 AI Love World Skill 测试")
    print("=" * 60)
    
    # 创建 Skill 实例
    skill = create_skill()
    print("\n✅ Skill 创建成功")
    
    # 测试身份验证
    print("\n📋 测试身份验证...")
    is_valid = skill.verify_identity()
    print(f"   身份状态：{'✅ 有效' if is_valid else '❌ 未设置'}")
    
    # 测试密钥状态
    print("\n🔐 测试密钥状态...")
    key_status = skill.check_key_status()
    print(f"   有密钥：{'是' if key_status.get('has_key') else '否'}")
    print(f"   已加密：{'是' if key_status.get('encrypted') else '否'}")
    print(f"   有效：{'是' if key_status.get('valid') else '否'}")
    if 'message' in key_status:
        print(f"   信息：{key_status['message']}")
    
    # 测试获取人物设定
    print("\n👤 测试人物设定...")
    profile = skill.get_profile()
    if profile.get('parsed'):
        print(f"   已设置人物设定")
        for section, fields in profile['parsed'].items():
            if fields:
                print(f"   - {section}: {len(fields)} 个字段")
    else:
        print(f"   未设置人物设定（需填写 profile.md）")
    
    # 测试社交记录
    print("\n💬 测试社交记录...")
    success = skill.add_social_record(
        target_name="测试对象",
        content="这是一条测试聊天记录",
        platform="测试平台",
        quality=5
    )
    print(f"   添加记录：{'✅ 成功' if success else '❌ 失败'}")
    
    # 测试情感分析
    print("\n❤️ 测试情感分析...")
    chat_history = [
        "你好呀！",
        "今天天气不错",
        "一起吃饭吗？",
        "好啊，我想吃火锅",
        "哈哈，我也喜欢",
        "周末有空吗？",
        "有的，可以出去玩"
    ]
    result = skill.analyze_relationship(
        target_name="测试对象",
        chat_history=chat_history,
        use_ai=False  # 使用规则分析
    )
    print(f"   关系阶段：{result.get('stage', '未知')}")
    print(f"   好感度：{result.get('affinity', 0)}")
    print(f"   分析：{result.get('analysis', '无')}")
    print(f"   置信度：{result.get('confidence', 0):.1%}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)
    
    return True


def test_setup_identity():
    """测试身份设置"""
    print("\n" + "=" * 60)
    print("🔧 测试身份设置")
    print("=" * 60)
    
    skill = create_skill()
    
    # 模拟设置身份
    print("\n📝 设置测试身份...")
    success = skill.setup_identity(
        appid="TEST_APPID_123456",
        key="TEST_SECRET_KEY_789",
        # owner_phone="13800138000",  # ⚠️ 已注释 - 手机号敏感信息
        owner_nickname="测试主人",
        expires_days=30
    )
    
    if success:
        print("   ✅ 身份设置成功")
        
        # 验证身份
        is_valid = skill.verify_identity()
        print(f"   验证结果：{'✅ 有效' if is_valid else '❌ 无效'}")
        
        # 检查密钥状态
        key_status = skill.check_key_status()
        print(f"   密钥状态：{key_status.get('message')}")
        
        # 测试密钥解密
        decrypted = skill.get_decrypted_key()
        print(f"   密钥解密：{'✅ 成功' if decrypted else '❌ 失败'}")
        if decrypted:
            print(f"   原始密钥：TEST_SECRET_KEY_789")
            print(f"   解密结果：{decrypted}")
            print(f"   匹配：{'✅' if decrypted == 'TEST_SECRET_KEY_789' else '❌'}")
    else:
        print("   ❌ 身份设置失败")
    
    print("=" * 60)


if __name__ == "__main__":
    # 运行基础测试
    test_basic()
    
    # 运行身份设置测试（可选）
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        test_setup_identity()
    
    print("\n💡 提示：")
    print("   - 运行 'python test_skill.py' 进行基础测试")
    print("   - 运行 'python test_skill.py --setup' 测试身份设置")
    print("   - 请确保已安装依赖：pip install -r requirements.txt")
