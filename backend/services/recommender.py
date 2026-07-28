"""
推荐算法
基于用户问卷（兴趣领域 + 探索比例）从书库推荐书籍
"""
import json
import random
from services.database import get_conn, get_user_survey


def get_recommendation_pool(user_id: str) -> dict:
    """
    根据用户问卷获取兴趣池和探索池
    返回: {"interest": [book_ids], "explore": [book_ids]}
    """
    survey = get_user_survey(user_id)
    conn = get_conn()
    cursor = conn.cursor()

    # 获取所有书
    cursor.execute("SELECT id, category FROM books")
    all_books = cursor.fetchall()
    conn.close()

    if not survey:
        # 无问卷：全部作为兴趣池
        return {
            "interest": [b["id"] for b in all_books],
            "explore": []
        }

    interest_categories = set(survey.get("categories", []))
    interest_pool = [b["id"] for b in all_books if b["category"] in interest_categories]
    explore_pool = [b["id"] for b in all_books if b["category"] not in interest_categories]

    return {"interest": interest_pool, "explore": explore_pool}


def generate_queue(user_id: str, queue_size: int = 10) -> list:
    """
    根据用户偏好生成推荐队列
    探索比例控制兴趣池 vs 探索池的比例
    """
    survey = get_user_survey(user_id)
    pools = get_recommendation_pool(user_id)

    interest_pool = pools["interest"][:]
    explore_pool = pools["explore"][:]

    random.shuffle(interest_pool)
    random.shuffle(explore_pool)

    # 探索比例: 0 = 全兴趣, 1 = 全探索
    explore_ratio = survey.get("explore_ratio", 0.4) if survey else 0.4
    explore_count = int(queue_size * explore_ratio)
    interest_count = queue_size - explore_count

    queue = []
    # 交替取，让兴趣和探索穿插
    while len(queue) < queue_size:
        added = False
        if interest_count > 0 and interest_pool:
            queue.append(interest_pool.pop(0))
            interest_count -= 1
            added = True
        if explore_count > 0 and explore_pool and len(queue) < queue_size:
            queue.append(explore_pool.pop(0))
            explore_count -= 1
            added = True
        # 如果一轮什么都没加，说明配额用完或池子空了，用剩余的补
        if not added:
            # 把剩余的书都加进去
            remaining = interest_pool + explore_pool
            for bid in remaining:
                if len(queue) >= queue_size:
                    break
                queue.append(bid)
            break

    # 保存队列到数据库
    conn = get_conn()
    cursor = conn.cursor()
    # 清空旧队列
    cursor.execute("DELETE FROM daily_queue WHERE user_id=?", (user_id,))
    for i, book_id in enumerate(queue):
        is_today = 1 if i == 0 else 0
        cursor.execute("""
            INSERT INTO daily_queue (user_id, book_id, position, is_today)
            VALUES (?, ?, ?, ?)
        """, (user_id, book_id, i, is_today))
    conn.commit()
    conn.close()

    return queue


def get_today_5(user_id: str, offset: int = 0) -> list:
    """获取今日推荐5本书，每次换一批生成1本新书替换1本旧书"""
    conn = get_conn()
    cursor = conn.cursor()

    # 检查队列是否存在
    cursor.execute("SELECT COUNT(*) as cnt FROM daily_queue WHERE user_id=?", (user_id,))
    if cursor.fetchone()["cnt"] == 0:
        conn.close()
        generate_queue(user_id, queue_size=30)
        conn = get_conn()
        cursor = conn.cursor()

    # offset>0 说明用户点了换一批，生成新书替换
    if offset > 0:
        # 先看队列里有多少本
        cursor.execute("SELECT COUNT(*) as cnt FROM daily_queue WHERE user_id=?", (user_id,))
        total = cursor.fetchone()["cnt"]
        
        # 从offset位置开始取5本
        cursor.execute("""
            SELECT b.* FROM daily_queue q
            JOIN books b ON q.book_id = b.id
            WHERE q.user_id=?
            ORDER BY q.position
            LIMIT 5 OFFSET ?
        """, (user_id, offset))
        rows = cursor.fetchall()
        
        # 不够5本时，AI生成1本新书补充
        if len(rows) < 5:
            _expand_queue_with_ai(user_id, conn, cursor, count=2)
            conn.commit()
            cursor.execute("""
                SELECT b.* FROM daily_queue q
                JOIN books b ON q.book_id = b.id
                WHERE q.user_id=?
                ORDER BY q.position
                LIMIT 5 OFFSET ?
            """, (user_id, offset))
            rows = cursor.fetchall()
        
        # 还是不够就从头补
        if len(rows) < 5:
            cursor.execute("""
                SELECT b.* FROM daily_queue q
                JOIN books b ON q.book_id = b.id
                WHERE q.user_id=?
                ORDER BY q.position
                LIMIT ?
            """, (user_id, 5 - len(rows)))
            rows.extend(cursor.fetchall())
        
        conn.close()
        return [_row_to_book(r) for r in rows]

    # 第一次加载，取前5本
    cursor.execute("""
        SELECT b.* FROM daily_queue q
        JOIN books b ON q.book_id = b.id
        WHERE q.user_id=?
        ORDER BY q.position
        LIMIT 5
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_book(r) for r in rows]


def _expand_queue_with_ai(user_id: str, conn, cursor, count=5):
    """用AI生成新书并补充到队列"""
    import json as _json
    import uuid as _uuid
    from services.deepseek import generate_summary

    # 获取用户问卷偏好
    survey = get_user_survey(user_id)
    categories = survey.get("categories", []) if survey else []
    difficulty = survey.get("difficulty", "medium") if survey else "medium"

    # 已有书的书名
    cursor.execute("SELECT title FROM books")
    existing_titles = set(r["title"] for r in cursor.fetchall())

    # 调AI推荐新书
    from services.deepseek import discover_by_category
    import random as _random
    cat = _random.choice(categories) if categories else "经典好书"
    new_books = discover_by_category(cat)

    added = 0
    for nb in new_books:
        if added >= count:
            break
        title = nb.get("title", "")
        author = nb.get("author", "")
        if title in existing_titles:
            continue

        # 生成摘要
        try:
            summary = generate_summary(title, author)
        except Exception:
            continue

        book_id = str(_uuid.uuid4())[:8]
        cursor.execute("""
            INSERT INTO books (id, title, author, category, one_liner, concepts, quotes, story_summary, chapters, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'generated')
        """, (
            book_id, title, author, cat,
            summary.get("one_liner", ""),
            _json.dumps(summary.get("concepts", []), ensure_ascii=False),
            _json.dumps(summary.get("quotes", []), ensure_ascii=False),
            summary.get("story_summary", ""),
            _json.dumps(summary.get("chapters", []), ensure_ascii=False),
        ))

        # 加到队列末尾
        cursor.execute("SELECT COALESCE(MAX(position), -1) as max_pos FROM daily_queue WHERE user_id=?", (user_id,))
        next_pos = cursor.fetchone()["max_pos"] + 1
        cursor.execute("""
            INSERT INTO daily_queue (user_id, book_id, position, is_today)
            VALUES (?, ?, ?, 0)
        """, (user_id, book_id, next_pos))

        existing_titles.add(title)
        added += 1

    print(f"[Recommender] AI补充了 {added} 本新书到队列")


def get_today_book(user_id: str) -> dict:
    """获取今日推荐"""
    conn = get_conn()
    cursor = conn.cursor()

    # 检查队列是否存在
    cursor.execute("SELECT COUNT(*) as cnt FROM daily_queue WHERE user_id=?", (user_id,))
    if cursor.fetchone()["cnt"] == 0:
        conn.close()
        generate_queue(user_id)
        conn = get_conn()
        cursor = conn.cursor()

    # 获取今日
    cursor.execute("""
        SELECT b.* FROM daily_queue q
        JOIN books b ON q.book_id = b.id
        WHERE q.user_id=? AND q.is_today=1
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None
    return _row_to_book(row)


def get_next_book(user_id: str) -> dict:
    """获取下一本（再读一本功能）"""
    conn = get_conn()
    cursor = conn.cursor()

    # 找当前 is_today 的位置
    cursor.execute("""
        SELECT position FROM daily_queue
        WHERE user_id=? AND is_today=1
    """, (user_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return get_today_book(user_id)

    next_pos = row["position"] + 1

    # 检查队列是否需要补货
    cursor.execute("SELECT MAX(position) as max_pos FROM daily_queue WHERE user_id=?", (user_id,))
    max_pos = cursor.fetchone()["max_pos"]

    if next_pos > max_pos:
        # 队列用完，重新生成
        conn.close()
        generate_queue(user_id)
        return get_today_book(user_id)

    # 检查是否需要补货（剩余 < 5 本）
    remaining = max_pos - next_pos
    if remaining < 5:
        print(f"[Recommender] 用户 {user_id} 队列剩余 {remaining} 本，触发补货")

    # 更新 is_today
    cursor.execute("UPDATE daily_queue SET is_today=0 WHERE user_id=?", (user_id,))
    cursor.execute("""
        UPDATE daily_queue SET is_today=1
        WHERE user_id=? AND position=?
    """, (user_id, next_pos))
    conn.commit()

    # 获取书籍
    cursor.execute("""
        SELECT b.* FROM daily_queue q
        JOIN books b ON q.book_id = b.id
        WHERE q.user_id=? AND q.position=?
    """, (user_id, next_pos))
    book_row = cursor.fetchone()
    conn.close()

    if not book_row:
        return None
    return _row_to_book(book_row)


def _row_to_book(row) -> dict:
    """数据库行转 book dict"""
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
