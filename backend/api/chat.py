"""对话追问 API"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from services.deepseek import chat_about_book
from services.database import get_conn
import json

router = APIRouter()


class ChatRequest(BaseModel):
    book_id: str
    question: str
    history: Optional[List[dict]] = None  # [{"role":"user","content":"..."},...]


@router.post("/ask")
async def ask(req: ChatRequest):
    """针对某本书提问"""
    # 获取书摘要
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT title, one_liner, concepts, quotes FROM books WHERE id=?", (req.book_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"answer": "找不到这本书的信息"}

    # 构造摘要文本
    summary_parts = [f"一句话核心：{row['one_liner']}"]
    concepts = json.loads(row["concepts"]) if row["concepts"] else []
    for i, c in enumerate(concepts, 1):
        summary_parts.append(f"概念{i}：{c.get('title','')} - {c.get('explanation','')}")
    quotes = json.loads(row["quotes"]) if row["quotes"] else []
    for q in quotes:
        summary_parts.append(f"金句：{q}")
    summary = "\n".join(summary_parts)

    answer = chat_about_book(row["title"], summary, req.question, req.history)
    return {"answer": answer}
