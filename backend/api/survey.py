"""
问卷 API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from services.database import save_survey
from services.recommender import generate_queue
import uuid

router = APIRouter()


class SurveyRequest(BaseModel):
    user_id: Optional[str] = None  # 首次为空，后端生成
    categories: List[str]  # 兴趣领域
    pace: str  # 阅读节奏: "daily" | "two-day" | "weekly"
    explore_ratio: float  # 探索比例 0-1
    purposes: List[str]  # 阅读目的
    difficulty: str = "medium"  # 阅读难度: "easy" | "medium" | "hard"


@router.post("/submit")
async def submit_survey(req: SurveyRequest):
    """提交问卷"""
    user_id = req.user_id or str(uuid.uuid4())[:12]

    survey = {
        "categories": req.categories,
        "pace": req.pace,
        "explore_ratio": req.explore_ratio,
        "purposes": req.purposes,
        "difficulty": req.difficulty,
    }

    save_survey(user_id, survey)

    # 立即生成推荐队列
    generate_queue(user_id)

    return {
        "user_id": user_id,
        "survey": survey,
        "message": "问卷提交成功，已为你生成推荐队列"
    }
