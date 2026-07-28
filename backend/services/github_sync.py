"""GitHub API 工具：把新生成的书持久化到 books.json"""
import os
import json
import base64
import httpx
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = "Capybara-Yang/daily-book"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/contents/backend/data/books.json"


def save_book_to_github(book_data: dict):
    """把新书追加到 GitHub 上的 books.json"""
    try:
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }

        # 1. 获取当前 books.json
        resp = httpx.get(GITHUB_API, headers=headers, timeout=30, verify=False)
        if resp.status_code != 200:
            print(f"[GitHub] 获取books.json失败: {resp.status_code}")
            return False

        file_info = resp.json()
        sha = file_info["sha"]
        content = base64.b64decode(file_info["content"]).decode("utf-8")
        books = json.loads(content)

        # 2. 追加新书
        # 检查是否已存在
        existing_ids = [b["id"] for b in books]
        if book_data["id"] in existing_ids:
            return True  # 已存在，跳过

        books.append(book_data)

        # 3. 提交更新
        new_content = json.dumps(books, ensure_ascii=False, indent=2)
        update_data = {
            "message": f"data: 新增《{book_data['title']}》",
            "content": base64.b64encode(new_content.encode("utf-8")).decode("utf-8"),
            "sha": sha,
        }

        resp = httpx.put(GITHUB_API, headers=headers, json=update_data, timeout=30, verify=False)
        if resp.status_code in (200, 201):
            print(f"[GitHub] 《{book_data['title']}》已持久化到仓库")
            return True
        else:
            print(f"[GitHub] 提交失败: {resp.status_code} {resp.text[:200]}")
            return False

    except Exception as e:
        print(f"[GitHub] 持久化失败: {e}")
        return False
