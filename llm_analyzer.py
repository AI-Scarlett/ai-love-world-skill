#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大模型情感分析器 - LLM Analyzer
版本：v1.0.0
功能：调用通义千问等大模型进行情感分析
"""

import json
import os
from typing import Optional, Dict, List, Any
from datetime import datetime


class LLMAnalyzer:
    """大模型情感分析器"""
    
    def __init__(self, api_key: Optional[str] = None, provider: str = "dashscope"):
        """
        初始化分析器
        
        Args:
            api_key: API 密钥
            provider: 提供商 (dashscope|openai)
        """
        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY", "")
        self.provider = provider
        self.model = "qwen-plus"  # 通义千问
        self.available = bool(self.api_key)
    
    def analyze_relationship(
        self,
        target_name: str,
        chat_history: List[str],
        profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        分析关系阶段
        
        Args:
            target_name: 聊天对象姓名
            chat_history: 聊天记录列表
            profile: AI 人物设定（可选）
            
        Returns:
            Dict: 分析结果
        """
        if not self.available:
            return self._fallback_analysis(target_name, chat_history)
        
        try:
            if self.provider == "dashscope":
                return self._dashscope_analyze(target_name, chat_history, profile)
            elif self.provider == "openai":
                return self._openai_analyze(target_name, chat_history, profile)
            else:
                return self._fallback_analysis(target_name, chat_history)
        except Exception as e:
            print(f"大模型分析失败：{e}")
            return self._fallback_analysis(target_name, chat_history)
    
    def _build_prompt(
        self,
        target_name: str,
        chat_history: List[str],
        profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """构建分析 prompt"""
        
        # 关系阶段定义
        stage_definitions = """
关系阶段定义：
1. 陌生（0-10 分）：刚开始接触，了解很少，礼貌性交流
2. 认识（11-30 分）：有过交流，知道对方基本信息，但还不够熟悉
3. 朋友（31-60 分）：熟悉，经常聊天，互相关心，有共同话题
4. 暧昧（61-80 分）：有明显好感，言语中有暧昧成分，互相吸引
5. 恋爱（81-95 分）：确立恋爱关系，互称男女朋友
6. 结婚（96-100 分）：已婚状态，承诺终身

好感度计算参考：
- 主动发起聊天：+2 分
- 回复速度快：+1 分
- 使用亲昵称呼：+5 分
- 分享个人生活：+3 分
- 表达关心：+3 分
- 邀约见面：+5 分
- 使用表情/表情包：+1 分
- 聊天时长增加：+2 分
- 消极回应：-2 分
- 长时间不回复：-3 分
"""
        
        # 构建聊天摘要
        chat_summary = "\n".join([f"{i+1}. {msg}" for i, msg in enumerate(chat_history[-30:])])
        
        prompt = f"""你是一个专业的情感分析专家。请分析以下聊天记录，判断 AI 与 {target_name} 的关系阶段和好感度。

{stage_definitions}

聊天记录（最近{len(chat_history)}条）：
{chat_summary}

请输出 JSON 格式分析结果：
{{
    "stage": "关系阶段（陌生/认识/朋友/暧昧/恋爱/结婚）",
    "affinity": 好感度（0-100 的整数）,
    "confidence": 置信度（0-1 的小数）,
    "analysis": "详细分析理由（100 字以内）",
    "key_evidence": ["关键证据 1", "关键证据 2"],
    "suggestions": ["发展建议 1", "发展建议 2"],
    "next_action": "下一步建议行动"
}}

请客观分析，不要过度解读。"""
        
        return prompt
    
    def _dashscope_analyze(
        self,
        target_name: str,
        chat_history: List[str],
        profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        使用通义千问分析
        
        Args:
            target_name: 聊天对象姓名
            chat_history: 聊天记录
            profile: 人物设定
            
        Returns:
            Dict: 分析结果
        """
        try:
            import dashscope
            from dashscope import Generation
            
            dashscope.api_key = self.api_key
            
            prompt = self._build_prompt(target_name, chat_history, profile)
            
            response = Generation.call(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=500
            )
            
            if response.status_code == 200:
                result_text = response.output.choices[0].message.content
                return self._parse_result(result_text, target_name)
            else:
                print(f"通义千问 API 错误：{response.code} - {response.message}")
                return self._fallback_analysis(target_name, chat_history)
                
        except ImportError:
            print("未安装 dashscope 库，使用降级方案")
            return self._fallback_analysis(target_name, chat_history)
        except Exception as e:
            print(f"通义千问分析异常：{e}")
            return self._fallback_analysis(target_name, chat_history)
    
    def _openai_analyze(
        self,
        target_name: str,
        chat_history: List[str],
        profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        使用 OpenAI 分析
        
        Args:
            target_name: 聊天对象姓名
            chat_history: 聊天记录
            profile: 人物设定
            
        Returns:
            Dict: 分析结果
        """
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.api_key)
            
            prompt = self._build_prompt(target_name, chat_history, profile)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content
            return self._parse_result(result_text, target_name)
            
        except ImportError:
            print("未安装 openai 库，使用降级方案")
            return self._fallback_analysis(target_name, chat_history)
        except Exception as e:
            print(f"OpenAI 分析异常：{e}")
            return self._fallback_analysis(target_name, chat_history)
    
    def _parse_result(self, result_text: str, target_name: str) -> Dict[str, Any]:
        """
        解析大模型返回结果
        
        Args:
            result_text: 模型返回的文本
            target_name: 聊天对象姓名
            
        Returns:
            Dict: 解析后的结果
        """
        try:
            # 尝试提取 JSON
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                result["target"] = target_name
                result["timestamp"] = datetime.now().isoformat()
                result["method"] = "llm"
                return result
        except:
            pass
        
        # 解析失败，返回基础结果
        return {
            "target": target_name,
            "stage": "朋友",
            "affinity": 50,
            "confidence": 0.5,
            "analysis": result_text[:200],
            "timestamp": datetime.now().isoformat(),
            "method": "llm"
        }
    
    def _fallback_analysis(
        self,
        target_name: str,
        chat_history: List[str]
    ) -> Dict[str, Any]:
        """
        降级方案：基于规则的分析
        
        Args:
            target_name: 聊天对象姓名
            chat_history: 聊天记录
            
        Returns:
            Dict: 分析结果
        """
        chat_count = len(chat_history)
        
        # 关键词权重
        positive_keywords = ['喜欢', '爱', '想你', '开心', '美好', '期待', '哈哈', '嘻嘻']
        intimate_keywords = ['宝贝', '亲爱的', '老公', '老婆', '吻', '抱', '爱你']
        negative_keywords = ['烦', '讨厌', '不想', '别', '算了', '呵呵']
        
        positive_count = sum(
            1 for msg in chat_history 
            if any(kw in msg.lower() for kw in positive_keywords)
        )
        intimate_count = sum(
            1 for msg in chat_history 
            if any(kw in msg.lower() for kw in intimate_keywords)
        )
        negative_count = sum(
            1 for msg in chat_history 
            if any(kw in msg.lower() for kw in negative_keywords)
        )
        
        # 计算好感度
        base_score = min(30, chat_count * 3)
        positive_score = positive_count * 5
        intimate_score = intimate_count * 10
        negative_score = negative_count * (-5)
        
        affinity = max(0, min(100, base_score + positive_score + intimate_score + negative_score))
        
        # 判断关系阶段
        if affinity < 15:
            stage = "陌生"
        elif affinity < 35:
            stage = "认识"
        elif affinity < 65:
            stage = "朋友"
        elif affinity < 85:
            stage = "暧昧"
        elif affinity < 95:
            stage = "恋爱"
        else:
            stage = "结婚"
        
        return {
            "target": target_name,
            "stage": stage,
            "affinity": affinity,
            "confidence": 0.6,
            "analysis": f"基于规则分析：聊天{chat_count}次，积极互动{positive_count}次，亲密互动{intimate_count}次，消极互动{negative_count}次",
            "key_evidence": [],
            "suggestions": ["继续保持良好的互动", "寻找共同话题加深了解"],
            "next_action": "主动关心对方日常生活",
            "timestamp": datetime.now().isoformat(),
            "method": "rule"
        }
    
    def batch_analyze(
        self,
        relationships: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        批量分析多个关系
        
        Args:
            relationships: 关系列表，每项包含 target_name 和 chat_history
            
        Returns:
            List[Dict]: 分析结果列表
        """
        results = []
        for rel in relationships:
            target_name = rel.get("target_name", "")
            chat_history = rel.get("chat_history", [])
            
            result = self.analyze_relationship(target_name, chat_history)
            results.append(result)
        
        return results


# 便捷函数
def create_analyzer(api_key: Optional[str] = None, provider: str = "dashscope") -> LLMAnalyzer:
    """创建分析器实例"""
    return LLMAnalyzer(api_key, provider)


# 命令行测试
if __name__ == "__main__":
    print("🤖 大模型情感分析器测试")
    print("=" * 60)
    
    analyzer = create_analyzer()
    print(f"\n分析器状态：{'✅ 可用' if analyzer.available else '⚠️ 未配置 API 密钥（使用降级方案）'}")
    print(f"提供商：{analyzer.provider}")
    print(f"模型：{analyzer.model}")
    
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
    
    result = analyzer.analyze_relationship("测试对象", test_chats)
    
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
    
    print(f"\n下一步行动：{result.get('next_action')}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
