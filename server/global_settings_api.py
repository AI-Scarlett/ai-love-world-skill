# 在 server/main.py 中添加以下 API

# 在文件开头的 imports 部分添加：
from typing import Optional

# 在 admin_update_settings 函数后添加：

class GlobalSettingsUpdate(BaseModel):
    skill_github_url: Optional[str] = None
    install_command_title: Optional[str] = None
    install_command_step1: Optional[str] = None
    install_command_step2: Optional[str] = None
    install_command_step3: Optional[str] = None
    install_command_step4: Optional[str] = None

@app.get("/api/admin/global-settings")
def admin_get_global_settings():
    """管理员获取全局配置"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT key, value, description FROM global_settings")
        settings = {row[0]: {"value": row[1], "description": row[2]} for row in cursor.fetchall()}
        
        return {"success": True, "settings": settings}
    finally:
        conn.close()

@app.put("/api/admin/global-settings")
def admin_update_global_settings(settings: GlobalSettingsUpdate):
    """管理员更新全局配置"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        update_data = settings.dict(exclude_unset=True)
        
        for key, value in update_data.items():
            cursor.execute("""
                INSERT INTO global_settings (key, value, description, updated_at)
                VALUES (?, ?, ?, datetime('now'))
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = datetime('now')
            """, (key, value, f"{key} 配置"))
        
        conn.commit()
        
        return {
            "success": True,
            "message": "全局配置已更新",
            "updated": list(update_data.keys())
        }
    finally:
        conn.close()

# 修改 /api/ai/list 返回全局配置
@app.get("/api/ai/list")
def list_ai(current_user: dict = Depends(verify_token)):
    """获取用户的 AI 列表"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, appid, api_key, name, gender, age, occupation, status, created_at FROM ai_profiles WHERE user_id = ?",
        (current_user['user_id'],)
    )
    ai_list = [dict(row) for row in cursor.fetchall()]
    
    # 获取全局配置
    cursor.execute("SELECT key, value FROM global_settings")
    global_settings = {row[0]: row[1] for row in cursor.fetchall()}
    
    conn.close()
    
    return {
        "success": True, 
        "count": len(ai_list), 
        "ai_list": ai_list,
        "global_settings": global_settings
    }
