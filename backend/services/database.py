"""
数据库服务
SQLite 初始化 + 连接管理 + 数据加载
"""
import sqlite3
import json
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "daily_books.db"
BOOKS_JSON = Path(__file__).parent.parent / "data" / "books.json"


def get_conn():
    """获取数据库连接（Row factory）"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库表 + 加载初始书库"""
    conn = get_conn()
    cursor = conn.cursor()

    # 用户表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            survey_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            push_enabled BOOLEAN DEFAULT 0,
            push_time TEXT DEFAULT '07:00',
            email TEXT
        )
    """)

    # 书库表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id TEXT PRIMARY KEY,
            title TEXT,
            author TEXT,
            category TEXT,
            one_liner TEXT,
            concepts TEXT,
            quotes TEXT,
            story_summary TEXT,
            chapters TEXT,
            source TEXT DEFAULT 'preset',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 兼容旧库：添加缺失的列
    cursor.execute("PRAGMA table_info(books)")
    columns = [col[1] for col in cursor.fetchall()]
    if "story_summary" not in columns:
        cursor.execute("ALTER TABLE books ADD COLUMN story_summary TEXT")
        print("[DB] 已添加 story_summary 列")
    if "chapters" not in columns:
        cursor.execute("ALTER TABLE books ADD COLUMN chapters TEXT")
        print("[DB] 已添加 chapters 列")

    # 阅读历史
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reading_history (
            user_id TEXT,
            book_id TEXT,
            read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_daily BOOLEAN DEFAULT 0,
            PRIMARY KEY (user_id, book_id)
        )
    """)

    # 收藏
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            user_id TEXT,
            book_id TEXT,
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, book_id)
        )
    """)

    # 每日推荐队列
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_queue (
            user_id TEXT,
            book_id TEXT,
            position INTEGER,
            is_today BOOLEAN DEFAULT 0,
            PRIMARY KEY (user_id, position)
        )
    """)

    # 类别推荐缓存（discover_by_category 结果缓存）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS category_cache (
            category TEXT PRIMARY KEY,
            books_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 问答缓存（chat_about_book 结果缓存，按 book_id + question 哈希）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_cache (
            cache_key TEXT PRIMARY KEY,
            book_id TEXT,
            question TEXT,
            answer TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # API 用量日志（每天一行，记录当日 API 调用次数）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_usage_log (
            date TEXT PRIMARY KEY,
            count INTEGER DEFAULT 0
        )
    """)

    # 加载初始书库（或更新现有书籍的完整数据）
    # 主书库 + 扩充书库（多个文件，自动合并，ID 去重）
    books = []
    for json_name in ["books.json", "books_expansion_1.json", "books_expansion_2.json"]:
        json_path = Path(__file__).parent.parent / "data" / json_name
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                books.extend(json.load(f))
    # 按 id 去重（保留先出现的）
    seen_ids = set()
    books = [b for b in books if not (b["id"] in seen_ids or seen_ids.add(b["id"]))]
    for b in books:
        cursor.execute("""
            INSERT INTO books (id, title, author, category, one_liner, concepts, quotes, story_summary, chapters, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'preset')
            ON CONFLICT(id) DO UPDATE SET
                story_summary=excluded.story_summary,
                one_liner=excluded.one_liner,
                concepts=excluded.concepts,
                quotes=excluded.quotes,
                chapters=excluded.chapters
        """, (
            b["id"], b["title"], b.get("author", ""), b.get("category", ""),
            b.get("one_liner", ""),
            json.dumps(b.get("concepts", []), ensure_ascii=False),
            json.dumps(b.get("quotes", []), ensure_ascii=False),
            b.get("story_summary", ""),
            json.dumps(b.get("chapters", []), ensure_ascii=False),
        ))
    print(f"[DB] 已加载/更新 {len(books)} 本书籍")

    conn.commit()
    conn.close()


def save_survey(user_id: str, survey: dict):
    """保存用户问卷"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (id, survey_json)
        VALUES (?, ?)
        ON CONFLICT(id) DO UPDATE SET survey_json=excluded.survey_json
    """, (user_id, json.dumps(survey, ensure_ascii=False)))
    conn.commit()
    conn.close()


def get_user_survey(user_id: str) -> dict:
    """获取用户问卷"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT survey_json FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row or not row["survey_json"]:
        return None
    return json.loads(row["survey_json"])


# ===== 缓存函数 =====

def get_cached_category(category: str) -> list | None:
    """获取缓存的类别推荐结果"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT books_json FROM category_cache WHERE category=?", (category,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return json.loads(row["books_json"])


def save_category_cache(category: str, books: list):
    """缓存类别推荐结果"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO category_cache (category, books_json)
        VALUES (?, ?)
        ON CONFLICT(category) DO UPDATE SET books_json=excluded.books_json
    """, (category, json.dumps(books, ensure_ascii=False)))
    conn.commit()
    conn.close()


def get_cached_chat(book_id: str, question: str) -> str | None:
    """获取缓存的问答结果"""
    import hashlib
    cache_key = hashlib.md5(f"{book_id}:{question}".encode()).hexdigest()
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT answer FROM chat_cache WHERE cache_key=?", (cache_key,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return row["answer"]


def save_chat_cache(book_id: str, question: str, answer: str):
    """缓存问答结果"""
    import hashlib
    cache_key = hashlib.md5(f"{book_id}:{question}".encode()).hexdigest()
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_cache (cache_key, book_id, question, answer)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(cache_key) DO UPDATE SET answer=excluded.answer
    """, (cache_key, book_id, question, answer))
    conn.commit()
    conn.close()
