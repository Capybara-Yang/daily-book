"""用户设置 API"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from services.database import get_conn, get_user_survey

router = APIRouter()


class PushSettings(BaseModel):
    user_id: str
    push_enabled: bool
    push_time: str  # "07:00"
    email: Optional[str] = None


@router.get("/survey/{user_id}")
async def get_survey(user_id: str):
    """获取用户问卷"""
    survey = get_user_survey(user_id)
    return {"survey": survey}


@router.put("/push-settings")
async def update_push_settings(req: PushSettings):
    """更新推送设置"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (id, push_enabled, push_time, email)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            push_enabled=excluded.push_enabled,
            push_time=excluded.push_time,
            email=excluded.email
    """, (
        req.user_id,
        1 if req.push_enabled else 0,
        req.push_time,
        req.email,
    ))
    conn.commit()
    conn.close()
    return {"success": True}


@router.get("/settings/{user_id}")
async def get_settings(user_id: str):
    """获取用户设置"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT push_enabled, push_time, email FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {"push_enabled": False, "push_time": "07:00", "email": None}
    return {
        "push_enabled": bool(row["push_enabled"]),
        "push_time": row["push_time"] or "07:00",
        "email": row["email"],
    }
