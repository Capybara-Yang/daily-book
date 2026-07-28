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

    # 加载初始书库（或更新现有书籍的完整数据）
    with open(BOOKS_JSON, "r", encoding="utf-8") as f:
        books = json.load(f)
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
