"""对话追问 API"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from services.deepseek import chat_about_book
from services.database import get_conn, get_cached_chat, save_chat_cache
import json

router = APIRouter()

# ---- 本地问题过滤（零 token）：跟书无关的问题直接挡下，不调 API ----

# 明显跟书相关的信号词：命中就直接放行
_BOOK_SIGNALS = (
    "书", "作者", "内容", "章节", "观点", "概念", "金句", "主角", "人物",
    "情节", "主角", "读后感", "书名", "结尾", "序", "译本", "版本",
    "这本书", "书中", "讲的", "论述", "案例", "理论", "方法论", "书评",
)

# 明显跟书无关的请求：命中就直接拒绝（零成本）
_OFF_TOPIC_PATTERNS = (
    "写代码", "写脚本", "编程", "python", "java", "c++", "javascript",
    "写作文", "写作", "写周报", "写报告", "写邮件", "写文案", "写诗", "写小说",
    "帮我写", "帮我做", "帮我算", "帮我查", "帮我订", "帮我买", "帮我规划",
    "翻译成", "翻译一下", "翻译这段",
    "天气", "股票", "基金", "彩票", "比赛结果", "新闻",
    "数学题", "作业", "高考", "考试答案",
    "笑话", "讲个故事", "说个段子",
    "你是谁", "你叫什么", "你是ai", "你是AI", "你是什么模型",
    "菜谱", "怎么做菜", "旅游攻略", "下载", "网盘",
)


def _is_off_topic(question: str) -> bool:
    """本地判断问题是否与书无关。宁可放行 ambiguous 的问题（有缓存兜底），只挡明显的。"""
    q = question.lower().strip()
    if not q:
        return True
    # 1. 有书相关信号词 → 一定放行（如"这本书翻译得好吗"不应被"翻译"误伤）
    for s in _BOOK_SIGNALS:
        if s in question:
            return False
    # 2. 命中无关请求 → 挡下，零 API 成本
    for p in _OFF_TOPIC_PATTERNS:
        if p in q:
            return True
    return False


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

    # 0. 本地关卡：明显与书无关的问题，直接拒绝，不花一次 API（也不写缓存）
    if _is_off_topic(req.question):
        return {
            "answer": f"这个问题和《{row['title']}》没有关系哦～我专门负责聊这本书。"
                      f"可以问我书里的观点、概念、金句，或者这本书能怎么用到生活里。",
            "blocked": True,
        }

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
