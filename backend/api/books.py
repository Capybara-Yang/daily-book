"""书库 / 推荐 / 搜索 API"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.database import get_conn
from services.recommender import get_today_book, get_next_book, generate_queue, get_today_5
from services.deepseek import generate_summary, discover_by_category
import json
import uuid

router = APIRouter()


@router.get("/today5/{user_id}")
async def get_today5(user_id: str):
    """获取今日推荐5本供用户选择"""
    books = get_today_5(user_id)
    if not books:
        raise HTTPException(404, "暂无推荐，请先完成问卷")
    from datetime import date
    return {"books": books, "date": str(date.today())}


@router.post("/select/{user_id}/{book_id}")
async def select_book(user_id: str, book_id: str):
    """用户从5本中选一本，记录阅读"""
    _record_history(user_id, book_id, is_daily=True)
    return {"ok": True}


@router.get("/today/{user_id}")
async def get_today(user_id: str):
    """获取今日推荐"""
    book = get_today_book(user_id)
    if not book:
        raise HTTPException(404, "暂无推荐，请先完成问卷")
    # 记录阅读历史
    _record_history(user_id, book["id"], is_daily=True)
    return book


@router.get("/next/{user_id}")
async def get_next(user_id: str):
    """再读一本"""
    book = get_next_book(user_id)
    if not book:
        raise HTTPException(404, "没有更多了")
    _record_history(user_id, book["id"], is_daily=False)
    return book


@router.get("/history/{user_id}")
async def get_history(user_id: str):
    """获取阅读历史"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.*, rh.read_at FROM reading_history rh
        JOIN books b ON rh.book_id = b.id
        WHERE rh.user_id=?
        ORDER BY rh.read_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_book(r) for r in rows]


@router.get("/favorites/{user_id}")
async def get_favorites(user_id: str):
    """获取收藏"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.*, f.saved_at FROM favorites f
        JOIN books b ON f.book_id = b.id
        WHERE f.user_id=?
        ORDER BY f.saved_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_book(r) for r in rows]


@router.post("/favorite/{user_id}/{book_id}")
async def toggle_favorite(user_id: str, book_id: str):
    """收藏 / 取消收藏"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM favorites WHERE user_id=? AND book_id=?", (user_id, book_id))
    if cursor.fetchone():
        cursor.execute("DELETE FROM favorites WHERE user_id=? AND book_id=?", (user_id, book_id))
        is_fav = False
    else:
        cursor.execute("INSERT INTO favorites (user_id, book_id) VALUES (?, ?)", (user_id, book_id))
        is_fav = True
    conn.commit()
    conn.close()
    return {"is_favorite": is_fav}


class SearchRequest(BaseModel):
    title: str = ""
    author: str = ""
    user_id: str = "anonymous"


@router.post("/search")
async def search_book(req: SearchRequest):
    """
    搜索书 → 模糊查库 → 生成摘要
    支持：只输入部分书名、只输入作者、书名+作者都部分匹配
    """
    conn = get_conn()
    cursor = conn.cursor()

    # 构建模糊查询
    title_kw = req.title.strip()
    author_kw = req.author.strip()

    # 如果两个都空，报错
    if not title_kw and not author_kw:
        return {"error": "请至少输入书名或作者"}

    # 模糊查库：书名包含关键词 OR 作者包含关键词
    if title_kw and author_kw:
        # 两个都给了：匹配书名 OR 作者
        cursor.execute("""
            SELECT * FROM books
            WHERE title LIKE ? OR author LIKE ? OR title LIKE ? OR author LIKE ?
            ORDER BY
              CASE WHEN title LIKE ? THEN 0 ELSE 1 END
            LIMIT 10
        """, (
            f"%{title_kw}%", f"%{author_kw}%",
            f"%{author_kw}%", f"%{title_kw}%",
            f"%{title_kw}%"
        ))
    elif title_kw:
        cursor.execute("""
            SELECT * FROM books WHERE title LIKE ? LIMIT 10
        """, (f"%{title_kw}%",))
    else:
        cursor.execute("""
            SELECT * FROM books WHERE author LIKE ? LIMIT 10
        """, (f"%{author_kw}%",))

    rows = cursor.fetchall()

    # 找到多本 → 返回列表让用户选
    if len(rows) > 1:
        conn.close()
        return {
            "multiple": True,
            "results": [_row_to_book(r) for r in rows],
            "message": f"找到 {len(rows)} 本相关书籍，点击查看"
        }

    # 找到一本 → 直接返回
    if len(rows) == 1:
        conn.close()
        book = _row_to_book(rows[0])
        book["source"] = "preset" if rows[0]["source"] == "preset" else "generated"
        return book

    # 本地没有 → 调 AI 生成
    # 如果只给了作者没给书名��AI 帮猜书名
    gen_title = title_kw if title_kw else f"{author_kw}的代表作"
    gen_author = author_kw

    summary = generate_summary(gen_title, gen_author)

    book_id = str(uuid.uuid4())[:8]
    cursor.execute("""
        INSERT INTO books (id, title, author, category, one_liner, concepts, quotes, story_summary, chapters, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'generated')
    """, (
        book_id,
        gen_title,
        gen_author,
        "搜索",
        summary.get("one_liner", ""),
        json.dumps(summary.get("concepts", []), ensure_ascii=False),
        json.dumps(summary.get("quotes", []), ensure_ascii=False),
        summary.get("story_summary", ""),
        json.dumps(summary.get("chapters", []), ensure_ascii=False),
    ))
    conn.commit()
    conn.close()

    return {
        "id": book_id,
        "title": gen_title,
        "author": gen_author,
        "category": "搜索",
        "one_liner": summary.get("one_liner", ""),
        "concepts": summary.get("concepts", []),
        "quotes": summary.get("quotes", []),
        "story_summary": summary.get("story_summary", ""),
        "chapters": summary.get("chapters", []),
        "source": "generated",
    }


class DiscoverRequest(BaseModel):
    category: str


@router.post("/discover")
async def discover(req: DiscoverRequest):
    """按类别发现书籍 — AI 推荐入门书单"""
    books = discover_by_category(req.category)
    return {"category": req.category, "books": books}


@router.get("/all")
async def get_all_books():
    """获取全部书库（调试用）"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_book(r) for r in rows]


def _record_history(user_id: str, book_id: str, is_daily: bool = False):
    """记录阅读历史"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO reading_history (user_id, book_id, read_at, is_daily)
        VALUES (?, ?, CURRENT_TIMESTAMP, ?)
    """, (user_id, book_id, 1 if is_daily else 0))
    conn.commit()
    conn.close()


def _row_to_book(row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "author": row["author"] or "",
        "category": row["category"] or "",
        "one_liner": row["one_liner"] or "",
        "concepts": json.loads(row["concepts"]) if row["concepts"] else [],
        "quotes": json.loads(row["quotes"]) if row["quotes"] else [],
        "story_summary": row["story_summary"] if "story_summary" in row.keys() and row["story_summary"] else "",
        "chapters": json.loads(row["chapters"]) if "chapters" in row.keys() and row["chapters"] else [],
        "source": row["source"] or "preset",
    }
