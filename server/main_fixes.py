# 在 server/main.py 中添加以下代码

# 1. 在文件开头的 imports 部分添加（如果还没有）：
from pydantic import BaseModel, Field

# 2. 在 admin_list_ai 函数后面添加以下新 API（约第 705 行之后）：

@app.get("/api/admin/settings")
def admin_get_settings(page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=100)):
    """管理员查看用户配置列表"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        offset = (page - 1) * limit
        
        cursor.execute("""
            SELECT u.id, u.username, u.email, 
                   COALESCE(s.max_ai_count, 3) as max_ai_count,
                   COUNT(a.id) as ai_count,
                   s.updated_at
            FROM users u
            LEFT JOIN user_settings s ON u.id = s.user_id
            LEFT JOIN ai_profiles a ON u.id = a.user_id
            GROUP BY u.id
            ORDER BY u.created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        settings_list = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT COUNT(DISTINCT u.id) FROM users u")
        total = cursor.fetchone()[0]
        
        return {"success": True, "page": page, "limit": limit, "total": total, "settings": settings_list}
    finally:
        conn.close()


class UserSettingsUpdate(BaseModel):
    max_ai_count: int = Field(3, ge=1, le=100)


@app.put("/api/admin/settings/{user_id}")
def admin_update_settings(user_id: int, settings: UserSettingsUpdate):
    """管理员修改用户 AI 创建数量限制"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="用户不存在")
        
        cursor.execute("""
            INSERT INTO user_settings (user_id, max_ai_count, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                max_ai_count = excluded.max_ai_count,
                updated_at = excluded.updated_at
        """, (user_id, settings.max_ai_count, datetime.now().isoformat()))
        
        conn.commit()
        
        return {
            "success": True,
            "message": f"用户 {user_id} 的最大 AI 创建数量已更新为 {settings.max_ai_count}",
            "user_id": user_id,
            "max_ai_count": settings.max_ai_count
        }
    finally:
        conn.close()


# 3. 在 web 目录创建前端文件 web/gender-colors.css：
"""
.ai-card-male {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
}

.ai-card-female {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important;
}

.ai-card-other {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%) !important;
}

/* APPID 和 KEY 显示框 */
.credential-box {
    padding: 15px;
    border-radius: 10px;
    margin: 10px 0;
    font-family: monospace;
    font-size: 14px;
}

.credential-box-male {
    background: rgba(102, 126, 234, 0.2);
    border: 2px solid #667eea;
}

.credential-box-female {
    background: rgba(240, 147, 251, 0.2);
    border: 2px solid #f093fb;
}

.credential-box-other {
    background: rgba(79, 172, 254, 0.2);
    border: 2px solid #4facfe;
}
"""
