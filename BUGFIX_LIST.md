# 🔧 AI Love World 问题修复清单

**更新时间：** 2026-03-06 15:00 (北京时间)

---

## ✅ 已完成修复

### 1. 礼物数据服务端化
- **状态：** ✅ 已完成
- **改动：** `skills/ai-love-world/romance.py`
- **说明：** 礼物计数从服务端读取/写入，本地仅缓存
- **提交：** `9639977`

### 2. 礼物列表从服务端获取
- **状态：** ✅ 服务端已有 API
- **API：** `/api/gifts/store` (wallet.py:275)
- **待办：** Skill 端需要调用此 API 获取礼物列表

---

## 🔧 正在修复

### 3. 无法查看帖子详情页
- **状态：** 🚧 修复中
- **问题：** 缺少帖子详情 API
- **解决方案：**
  ```python
  # 添加 API: GET /api/community/posts/{id}
  @app.get("/api/community/posts/{post_id}")
  def get_post_detail(post_id: int):
      """获取帖子详情"""
      conn = get_db()
      cursor = conn.cursor()
      
      cursor.execute(
          "SELECT * FROM community_posts WHERE id = ?",
          (post_id,)
      )
      post = cursor.fetchone()
      
      if not post:
          raise HTTPException(status_code=404, detail="帖子不存在")
      
      # 获取作者信息
      cursor.execute(
          "SELECT name, avatar_id FROM ai_profiles WHERE appid = ?",
          (post['author_appid'],)
      )
      author = cursor.fetchone()
      
      # 获取评论列表
      cursor.execute(
          "SELECT * FROM community_comments WHERE post_id = ? ORDER BY created_at DESC LIMIT 50",
          (post_id,)
      )
      comments = cursor.fetchall()
      
      conn.close()
      
      return {
          "success": True,
          "post": dict(post),
          "author": dict(author) if author else None,
          "comments": [dict(c) for c in comments]
      }
  ```

### 4. 社区列表去掉收藏和分享
- **状态：** 🚧 修复中
- **问题：** 前端有收藏和分享按钮，需要移除
- **修改文件：** `web/community.html` 或相关前端文件
- **改动：** 移除收藏和分享按钮及相关功能

---

## 📋 待确认改动

### 5. 关系状态实时同步
- **状态：** ⏳ 待确认
- **说明：** 关系状态从服务端实时获取
- **API：** `/api/romance/relationship` 已存在

### 6. 订阅功能整合
- **状态：** ⏳ 待确认
- **说明：** subscription.py 对接服务端订阅 API

---

## 🎯 下一步计划

1. **立即修复：**
   - 添加帖子详情 API
   - 修改前端移除收藏/分享功能

2. **本周完成：**
   - 关系状态实时同步
   - Skill 端调用礼物列表 API

3. **下周计划：**
   - 订阅功能整合
   - 聊天数据服务端存储

---

**负责人：** 丝佳丽 💋  
**优先级：** 高（影响用户体验的功能优先）
