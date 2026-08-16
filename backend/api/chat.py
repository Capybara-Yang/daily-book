"""对话追问 API"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from services.deepseek import chat_about_book
from services.database import get_conn, get_cached_chat, save_chat_cache
import json

router = APIRouter()


class ChatRequest(BaseModel):
    book_id: str
    question: str
    history: Optional[List[dict]] = None  # [{"role":"user","content":"..."},...]


@router.post("/ask")
async def ask(req: ChatRequest):
    """针对某本书提问（带问答缓存）"""
    # 获取书摘要
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT title, one_liner, concepts, quotes FROM books WHERE id=?", (req.book_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"answer": "找不到这本书的信息"}

    # 1. 先查缓存（无 history 时才缓存，有 history 说明是连续对话）
    if not req.history:
        cached = get_cached_chat(req.book_id, req.question)
        if cached:
            print(f"[Chat] 命中缓存: book={req.book_id}")
            return {"answer": cached, "cached": True}

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

    # 2. 缓存回答（仅无 history 时）
    if not req.history and answer:
        save_chat_cache(req.book_id, req.question, answer)

    return {"answer": answer}
