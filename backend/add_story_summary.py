"""给小说类书籍添加 story_summary 字段"""
import json
from pathlib import Path

BOOKS_JSON = Path(__file__).parent / "data" / "books.json"
STORY_JSON = Path(__file__).parent / "data" / "story_summaries.json"

with open(STORY_JSON, "r", encoding="utf-8") as f:
    story_summaries = json.load(f)

with open(BOOKS_JSON, "r", encoding="utf-8") as f:
    books = json.load(f)

for book in books:
    if book["id"] in story_summaries:
        book["story_summary"] = story_summaries[book["id"]]
        print(f"已添加: {book['title']}")

with open(BOOKS_JSON, "w", encoding="utf-8") as f:
    json.dump(books, f, ensure_ascii=False, indent=2)

print(f"完成，共更新 {len(story_summaries)} 本小说")
