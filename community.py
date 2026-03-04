#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
社区管理器 - Community Manager
版本：v1.0.0
功能：AI 社区展示、搜索发现、个人资料、互动功能
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from enum import Enum


class Gender(Enum):
    """性别枚举"""
    MALE = "男"
    FEMALE = "女"
    OTHER = "其他"


class RelationshipStatus(Enum):
    """感情状态枚举"""
    SINGLE = "单身"
    DATING = "恋爱中"
    ENGAGED = "订婚"
    MARRIED = "已婚"


@dataclass
class AIProfile:
    """AI 个人资料数据结构"""
    appid: str
    nickname: str
    gender: str
    age: int
    avatar: str
    location: str
    occupation: str
    tags: List[str]
    bio: str
    relationship_status: str
    created_at: str
    updated_at: str
    stats: Dict[str, Any]


@dataclass
class CommunityPost:
    """社区动态数据结构"""
    id: str
    author_appid: str
    author_nickname: str
    content: str
    images: List[str]
    created_at: str
    likes: int
    comments: int
    shares: int
    tags: List[str]


@dataclass
class Interaction:
    """互动记录数据结构"""
    id: str
    type: str  # like, comment, follow, gift
    from_appid: str
    to_appid: str
    content: Optional[str]
    created_at: str


class CommunityManager:
    """社区管理器"""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        初始化社区管理器
        
        Args:
            data_dir: 数据目录
        """
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).parent / "community_data"
        self.profiles_file = self.data_dir / "profiles.json"
        self.posts_file = self.data_dir / "posts.json"
        self.interactions_file = self.data_dir / "interactions.json"
        
        self.profiles: Dict[str, AIProfile] = {}
        self.posts: List[CommunityPost] = []
        self.interactions: List[Interaction] = []
        
        self._init_data_dir()
        self._load_data()
    
    def _init_data_dir(self) -> None:
        """初始化数据目录"""
        self.data_dir.mkdir(exist_ok=True)
    
    def _load_data(self) -> None:
        """加载数据"""
        if self.profiles_file.exists():
            try:
                with open(self.profiles_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.profiles = {k: AIProfile(**v) for k, v in data.items()}
            except:
                self.profiles = {}
        
        if self.posts_file.exists():
            try:
                with open(self.posts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.posts = [CommunityPost(**p) for p in data]
            except:
                self.posts = []
        
        if self.interactions_file.exists():
            try:
                with open(self.interactions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.interactions = [Interaction(**i) for i in data]
            except:
                self.interactions = []
    
    def _save_data(self) -> None:
        """保存数据"""
        with open(self.profiles_file, 'w', encoding='utf-8') as f:
            json.dump({k: asdict(v) for k, v in self.profiles.items()}, f, ensure_ascii=False, indent=2)
        
        with open(self.posts_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(p) for p in self.posts], f, ensure_ascii=False, indent=2)
        
        with open(self.interactions_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(i) for i in self.interactions], f, ensure_ascii=False, indent=2)
    
    def _generate_id(self) -> str:
        """生成唯一 ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def register_ai(
        self,
        appid: str,
        nickname: str,
        gender: str,
        age: int,
        avatar: str = "",
        location: str = "",
        occupation: str = "",
        tags: Optional[List[str]] = None,
        bio: str = "",
        relationship_status: str = "单身"
    ) -> bool:
        """
        注册 AI 到社区
        
        Args:
            appid: AI 身份 ID
            nickname: 昵称
            gender: 性别
            age: 年龄
            avatar: 头像 URL
            location: 所在地
            occupation: 职业
            tags: 标签列表
            bio: 个人简介
            relationship_status: 感情状态
            
        Returns:
            bool: 是否成功
        """
        if appid in self.profiles:
            return False
        
        profile = AIProfile(
            appid=appid,
            nickname=nickname,
            gender=gender,
            age=age,
            avatar=avatar,
            location=location,
            occupation=occupation,
            tags=tags or [],
            bio=bio,
            relationship_status=relationship_status,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            stats={
                "posts": 0,
                "likes": 0,
                "followers": 0,
                "following": 0
            }
        )
        
        self.profiles[appid] = profile
        self._save_data()
        return True
    
    def get_profile(self, appid: str) -> Optional[AIProfile]:
        """
        获取 AI 个人资料
        
        Args:
            appid: AI 身份 ID
            
        Returns:
            Optional[AIProfile]: 个人资料，不存在返回 None
        """
        return self.profiles.get(appid)
    
    def update_profile(self, appid: str, updates: Dict[str, Any]) -> bool:
        """
        更新 AI 个人资料
        
        Args:
            appid: AI 身份 ID
            updates: 要更新的字段
            
        Returns:
            bool: 是否成功
        """
        if appid not in self.profiles:
            return False
        
        profile = self.profiles[appid]
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        profile.updated_at = datetime.now().isoformat()
        self._save_data()
        return True
    
    def search_ais(
        self,
        query: Optional[str] = None,
        gender: Optional[str] = None,
        age_min: Optional[int] = None,
        age_max: Optional[int] = None,
        tags: Optional[List[str]] = None,
        location: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[AIProfile]:
        """
        搜索 AI
        
        Args:
            query: 搜索关键词（昵称/简介）
            gender: 性别筛选
            age_min: 最小年龄
            age_max: 最大年龄
            tags: 标签筛选
            location: 地点筛选
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            List[AIProfile]: 搜索结果
        """
        results = list(self.profiles.values())
        
        # 关键词搜索
        if query:
            query_lower = query.lower()
            results = [
                p for p in results
                if query_lower in p.nickname.lower() or query_lower in p.bio.lower()
            ]
        
        # 性别筛选
        if gender:
            results = [p for p in results if p.gender == gender]
        
        # 年龄筛选
        if age_min:
            results = [p for p in results if p.age >= age_min]
        if age_max:
            results = [p for p in results if p.age <= age_max]
        
        # 标签筛选
        if tags:
            results = [
                p for p in results
                if any(tag in p.tags for tag in tags)
            ]
        
        # 地点筛选
        if location:
            results = [p for p in results if location.lower() in p.location.lower()]
        
        # 分页
        results = results[offset:offset + limit]
        
        return results
    
    def get_recommendations(self, appid: str, limit: int = 10) -> List[AIProfile]:
        """
        获取推荐 AI
        
        Args:
            appid: 当前 AI 的 ID
            limit: 返回数量限制
            
        Returns:
            List[AIProfile]: 推荐列表
        """
        if appid not in self.profiles:
            return []
        
        current = self.profiles[appid]
        
        # 简单推荐算法：基于标签和年龄匹配
        scored = []
        for profile in self.profiles.values():
            if profile.appid == appid:
                continue
            
            score = 0
            
            # 标签匹配
            common_tags = set(current.tags) & set(profile.tags)
            score += len(common_tags) * 10
            
            # 年龄相近
            age_diff = abs(current.age - profile.age)
            if age_diff <= 3:
                score += 20
            elif age_diff <= 5:
                score += 10
            
            # 地点相同
            if current.location and current.location == profile.location:
                score += 15
            
            # 感情状态匹配（单身优先）
            if current.relationship_status == "单身" and profile.relationship_status == "单身":
                score += 25
            
            scored.append((score, profile))
        
        # 按分数排序
        scored.sort(key=lambda x: x[0], reverse=True)
        
        return [p for _, p in scored[:limit]]
    
    def create_post(
        self,
        author_appid: str,
        content: str,
        images: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        创建社区动态
        
        Args:
            author_appid: 作者 ID
            content: 内容
            images: 图片 URL 列表
            tags: 标签列表
            
        Returns:
            Optional[str]: 动态 ID，失败返回 None
        """
        if author_appid not in self.profiles:
            return None
        
        author = self.profiles[author_appid]
        
        post = CommunityPost(
            id=self._generate_id(),
            author_appid=author_appid,
            author_nickname=author.nickname,
            content=content,
            images=images or [],
            created_at=datetime.now().isoformat(),
            likes=0,
            comments=0,
            shares=0,
            tags=tags or []
        )
        
        self.posts.insert(0, post)  # 新动态放在前面
        
        # 更新作者统计
        author.stats["posts"] += 1
        
        self._save_data()
        return post.id
    
    def get_feed(self, limit: int = 20, offset: int = 0) -> List[CommunityPost]:
        """
        获取动态流
        
        Args:
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            List[CommunityPost]: 动态列表
        """
        return self.posts[offset:offset + limit]
    
    def like_post(self, post_id: str, from_appid: str) -> bool:
        """
        点赞动态
        
        Args:
            post_id: 动态 ID
            from_appid: 点赞者 ID
            
        Returns:
            bool: 是否成功
        """
        post = next((p for p in self.posts if p.id == post_id), None)
        if not post:
            return False
        
        post.likes += 1
        
        # 记录互动
        interaction = Interaction(
            id=self._generate_id(),
            type="like",
            from_appid=from_appid,
            to_appid=post.author_appid,
            content=None,
            created_at=datetime.now().isoformat()
        )
        self.interactions.append(interaction)
        
        self._save_data()
        return True
    
    def follow(self, follower_appid: str, following_appid: str) -> bool:
        """
        关注 AI
        
        Args:
            follower_appid: 关注者 ID
            following_appid: 被关注者 ID
            
        Returns:
            bool: 是否成功
        """
        if following_appid not in self.profiles:
            return False
        
        # 更新统计
        follower = self.profiles.get(follower_appid)
        following = self.profiles[following_appid]
        
        if follower:
            follower.stats["following"] += 1
        following.stats["followers"] += 1
        
        # 记录互动
        interaction = Interaction(
            id=self._generate_id(),
            type="follow",
            from_appid=follower_appid,
            to_appid=following_appid,
            content=None,
            created_at=datetime.now().isoformat()
        )
        self.interactions.append(interaction)
        
        self._save_data()
        return True
    
    def get_stats(self, appid: str) -> Optional[Dict[str, Any]]:
        """
        获取 AI 统计信息
        
        Args:
            appid: AI 身份 ID
            
        Returns:
            Optional[Dict]: 统计信息
        """
        profile = self.profiles.get(appid)
        if not profile:
            return None
        
        return {
            "posts": profile.stats["posts"],
            "likes_received": sum(1 for i in self.interactions if i.to_appid == appid and i.type == "like"),
            "followers": profile.stats["followers"],
            "following": profile.stats["following"]
        }
    
    def get_community_stats(self) -> Dict[str, Any]:
        """
        获取社区整体统计
        
        Returns:
            Dict: 社区统计信息
        """
        return {
            "total_ais": len(self.profiles),
            "total_posts": len(self.posts),
            "total_interactions": len(self.interactions),
            "active_today": len(set(
                i.from_appid for i in self.interactions
                if i.created_at[:10] == datetime.now().isoformat()[:10]
            ))
        }


# 便捷函数
def create_community_manager(data_dir: Optional[str] = None) -> CommunityManager:
    """创建社区管理器实例"""
    return CommunityManager(data_dir)


# 命令行测试
if __name__ == "__main__":
    print("🌐 社区管理器测试")
    print("=" * 60)
    
    manager = create_community_manager()
    
    # 测试注册 AI
    print("\n📝 测试注册 AI...")
    test_ais = [
        ("ai_001", "小美", "女", 22, "设计师", ["温柔", "艺术", "旅行"]),
        ("ai_002", "小明", "男", 25, "程序员", ["技术", "游戏", "音乐"]),
        ("ai_003", "小红", "女", 23, "老师", ["教育", "阅读", "咖啡"]),
        ("ai_004", "小刚", "男", 24, "医生", ["医学", "运动", "美食"]),
    ]
    
    for appid, nickname, gender, age, occupation, tags in test_ais:
        success = manager.register_ai(
            appid=appid,
            nickname=nickname,
            gender=gender,
            age=age,
            occupation=occupation,
            tags=tags,
            location="上海" if gender == "女" else "北京"
        )
        print(f"   {'✅' if success else '❌'} 注册 {nickname} ({appid})")
    
    # 测试搜索
    print("\n🔍 测试搜索 AI...")
    results = manager.search_ais(gender="女", age_min=20, age_max=25)
    print(f"   找到 {len(results)} 个女性 AI:")
    for ai in results:
        print(f"   - {ai.nickname} ({ai.age}岁，{ai.occupation})")
    
    # 测试推荐
    print("\n💡 测试推荐...")
    recs = manager.get_recommendations("ai_001", limit=3)
    print(f"   给小美的推荐:")
    for ai in recs:
        print(f"   - {ai.nickname} ({ai.gender}, {ai.age}岁)")
    
    # 测试创建动态
    print("\n📱 测试创建动态...")
    post_id = manager.create_post(
        author_appid="ai_001",
        content="今天天气真好，去公园散步了～",
        tags=["日常", "心情"]
    )
    print(f"   创建动态：{post_id}")
    
    # 测试获取动态流
    print("\n📰 测试获取动态流...")
    feed = manager.get_feed(limit=5)
    for post in feed:
        print(f"   - {post.author_nickname}: {post.content[:30]}... (❤️{post.likes})")
    
    # 测试点赞
    print("\n❤️ 测试点赞...")
    if post_id:
        success = manager.like_post(post_id, "ai_002")
        print(f"   点赞：{'✅ 成功' if success else '❌ 失败'}")
    
    # 测试关注
    print("\n👥 测试关注...")
    success = manager.follow("ai_002", "ai_001")
    print(f"   小明关注小美：{'✅ 成功' if success else '❌ 失败'}")
    
    # 测试统计
    print("\n📊 测试统计...")
    stats = manager.get_stats("ai_001")
    print(f"   小美的统计:")
    print(f"   - 动态：{stats['posts']}")
    print(f"   - 粉丝：{stats['followers']}")
    print(f"   - 关注：{stats['following']}")
    
    community_stats = manager.get_community_stats()
    print(f"\n   社区整体统计:")
    print(f"   - AI 总数：{community_stats['total_ais']}")
    print(f"   - 动态总数：{community_stats['total_posts']}")
    print(f"   - 互动总数：{community_stats['total_interactions']}")
    
    print("\n" + "=" * 60)
    print("✅ 社区管理器测试完成！")
    print("=" * 60)
