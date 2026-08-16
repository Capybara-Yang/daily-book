"""
DeepSeek API 封装
双模式：无 API Key 时使用 Mock 模式
省 API 优化：system prompt 缓存 + 降低 max_tokens + 每日用量限制
"""
import os
import json
import hashlib
from datetime import date
from pathlib import Path
from dotenv import load_dotenv

# 用绝对路径加载 .env，避免工作目录问题
ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(ENV_PATH)

# 只从环境变量读取，不再硬编码 Key
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()

USE_MOCK = not DEEPSEEK_API_KEY
print(f"[DeepSeek] 模式: {'Mock' if USE_MOCK else '真实 API'}, Key: {DEEPSEEK_API_KEY[:8]}...{DEEPSEEK_API_KEY[-4:] if not USE_MOCK else ''}")

# ===== 每日 API 用量限制 =====
DAILY_API_LIMIT = int(os.getenv("DEEPSEEK_DAILY_LIMIT", "80"))  # 默认每天最多 80 次调用


def _get_today_usage() -> int:
    """获取今日已用 API 次数"""
    try:
        from services.database import get_conn
        conn = get_conn()
        cursor = conn.cursor()
        today = str(date.today())
        cursor.execute("SELECT count FROM api_usage_log WHERE date=?", (today,))
        row = cursor.fetchone()
        conn.close()
        return row["count"] if row else 0
    except Exception:
        return 0


def _log_api_call():
    """记录一次 API 调用"""
    try:
        from services.database import get_conn
        conn = get_conn()
        cursor = conn.cursor()
        today = str(date.today())
        cursor.execute("""
            INSERT INTO api_usage_log (date, count) VALUES (?, 1)
            ON CONFLICT(date) DO UPDATE SET count = count + 1
        """, (today,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DeepSeek] 用量记录失败: {e}")


def _is_over_limit() -> bool:
    """检查是否超过每日限制"""
    usage = _get_today_usage()
    if usage >= DAILY_API_LIMIT:
        print(f"[DeepSeek] 今日已用 {usage} 次，超过限制 {DAILY_API_LIMIT}，降级到 Mock")
        return True
    return False


if not USE_MOCK:
    import httpx
    from openai import OpenAI
    # 沙盒环境 SSL 证书有问题，禁用验证
    http_client = httpx.Client(verify=False)
    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com",
        http_client=http_client
    )


# ===== 固定 system prompt（DeepSeek 会自动缓存相同前缀，缓存命中 90% 折扣）=====

_SUMMARY_SYSTEM_PROMPT = """你是书籍摘要助手。目标用户：没时间或不愿意读完整本书的人，想快速了解书的内容和精彩部分在哪里。

判断规则：
- 叙事性作品（小说/戏剧/传记/纪实/史诗/童话等）→ 需要故事概要
- 非叙事性作品（方法论/科普/哲学/商业/自助/技术等）→ 不需要故事概要

输出 JSON 格式（不要加 markdown 代码块）：
{
  "one_liner": "一句话，20字以内",
  "story_summary": "叙事性作品写200字梗概，其他留空字符串",
  "concepts": [{"title": "标题", "explanation": "解释说明，50字以内"}],
  "quotes": ["金句1", "金句2"],
  "chapters": [{"title": "章节名", "summary": "一句话概要", "highlight": "最精彩的部分是什么", "excerpt": "约100-150字的原文摘录"}]
}

要求：
- concepts 提供 3 个
- quotes 提供 2 条（英文书用"中文翻译\\n英文原文"，中文书只用中文）
- chapters 提供 3-5 个精华章节
- 内容精炼、深刻、有启发性
- 必须返回合法 JSON"""

_DISCOVER_SYSTEM_PROMPT = """你是书籍推荐助手。为想了解某个领域但不太了解的用户推荐入门书。

输出 JSON 格式（不要加 markdown 代码块）：
{
  "books": [{"title": "书名", "author": "作者", "reason": "为什么推荐这本作为入门书，30字以内"}]
}

要求：
- 推荐 4 本书
- 优先选择口碑好、易读、适合新手的入门书
- 覆盖该领域不同侧面
- 必须返回合法 JSON"""

_EXTRACT_SYSTEM_PROMPT = """你是文档摘要助手。目标用户：没时间读完整文档的人，想快速了解内容和精彩部分在哪里。

输出 JSON 格式（不要加 markdown 代码块）：
{
  "title": "简洁的标题",
  "one_liner": "一句话概括核心内容，20字以内",
  "concepts": [{"title": "核心要点标题", "explanation": "解释说明，50字以内"}],
  "quotes": ["文档中的金句或重要原话1", "金句2"],
  "chapters": [{"title": "段落/章节名", "summary": "一句话概要", "highlight": "最精彩的部分", "excerpt": "约100-150字的原文摘录"}]
}

要求：
- concepts 提供 3 个核心要点
- quotes 提供 2 条文档中的原话
- chapters 提供 2-4 个精华段落
- excerpt 必须从文档原文中直接摘取，不要改写
- 必须基于文档实际内容，不要编造
- 必须返回合法 JSON"""


def generate_summary(title: str, author: str = "") -> dict:
    """
    生成书籍摘要
    返回: {"one_liner": str, "concepts": [...], "quotes": [...], "story_summary": str(可选)}
    """
    if USE_MOCK or _is_over_limit():
        return _mock_summary(title, author)

    # 短 user prompt — 固定指令已移入 system prompt（会被 DeepSeek 缓存）
    user_msg = f'请为《{title}》（作者：{author}）生成结构化摘要。'

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": _SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=2500,   # 4000 → 2500
            temperature=0.7,
        )
        _log_api_call()
        content = response.choices[0].message.content.strip()
        print(f"[DeepSeek] 摘要原始返回: {content[:200]}")
        result = _extract_json(content)
        if result:
            print(f"[DeepSeek] 解析成功，字段: {list(result.keys())}, chapters数: {len(result.get('chapters',[]))}")
            return result
        return _mock_summary(title, author)
    except Exception as e:
        print(f"[DeepSeek] 生成摘要失败: {e}")
        return _mock_summary(title, author)


def discover_by_category(category: str) -> list:
    """
    根据类别推荐 3-5 本入门书
    返回: [{"title": str, "author": str, "reason": str}]
    """
    if USE_MOCK or _is_over_limit():
        return _mock_discover(category)

    user_msg = f'用户想了解"{category}"领域的书，但他对这个领域不了解。请推荐 4 本最适合入门的经典书籍。'

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": _DISCOVER_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=1200,   # 2000 → 1200
            temperature=0.7,
        )
        _log_api_call()
        content = response.choices[0].message.content.strip()
        print(f"[DeepSeek] 发现原始返回: {content[:200]}")
        result = _extract_json(content)
        if result:
            return result.get("books", [])
        return _mock_discover(category)
    except Exception as e:
        print(f"[DeepSeek] 发现失败: {e}")
        return _mock_discover(category)


def _mock_discover(category: str) -> list:
    return [
        {"title": f"{category}入门一", "author": "佚名", "reason": "经典入门书，通俗易懂"},
        {"title": f"{category}入门二", "author": "佚名", "reason": "系统全面，适合新手"},
    ]


_BATCH_SYSTEM_PROMPT = """你是书籍推荐助手。为书库批量生成新书资料。

输出 JSON 格式（不要加 markdown 代码块）：
{
  "books": [
    {
      "title": "书名",
      "author": "作者",
      "one_liner": "一句话核心，20字以内",
      "story_summary": "100字以内简介",
      "concepts": [{"title": "标题", "explanation": "解释，40字以内"}],
      "quotes": ["金句1", "金句2"]
    }
  ]
}

要求：
- 每本书 concepts 3 个、quotes 2 条
- 只推荐真实存在、口碑好的经典书
- 不要与排除列表中的书重复（含同一本书的不同译名）
- 必须返回合法 JSON"""


def generate_books_batch(category: str, count: int = 6, exclude_titles: list = None) -> list:
    """
    一次 API 调用批量生成 count 本完整新书（省 token：1 次调用 = 6 本书完整资料）
    返回: [{"title", "author", "one_liner", "story_summary", "concepts", "quotes"}]
    """
    if USE_MOCK or _is_over_limit():
        return []

    exclude = exclude_titles or []
    exclude_str = "、".join(exclude[:80]) if exclude else "（书库暂时为空）"
    user_msg = f'请为"{category}"类别推荐 {count} 本经典好书并生成完整资料。书库已有以下书，不要重复推荐：{exclude_str}'

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": _BATCH_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=2800,
            temperature=0.8,
        )
        _log_api_call()
        content = response.choices[0].message.content.strip()
        print(f"[DeepSeek] 批量生成原始返回: {content[:200]}")
        result = _extract_json(content)
        if result:
            return result.get("books", [])
    except Exception as e:
        print(f"[DeepSeek] 批量生成失败: {e}")
    return []


def chat_about_book(title: str, summary: str, question: str, history=None) -> str:
    """针对书籍内容回答问题"""
    if USE_MOCK or _is_over_limit():
        return _mock_answer(title, question)

    messages = [
        {
            "role": "system",
            "content": f"""你是《{title}》的解读助手。用户是没时间或不愿意读完整本书的人，想快速了解书的内容。

回答规则：
1. 基于以下书籍摘要回答，不要编造书中没有的内容
2. 理性、客观，不要一味认可用户的问题——如果问题有误区或前提错误，直接指出
3. 如果书中的观点本身有争议，要说明争议在哪，而不是单方面站队
4. 回答简洁有深度，200字以内
5. 如果用户问的问题超出了这本书的范围，直接说明"这超出了本书讨论范围"

书籍摘要：
{summary}"""
        },
    ]
    if history:
        messages.extend(history[-10:])
    messages.append({"role": "user", "content": question})

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            max_tokens=400,    # 500 → 400
            temperature=0.7,
        )
        _log_api_call()
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[DeepSeek] 对话失败: {e}")
        return _mock_answer(title, question)


def extract_from_text(text: str, filename: str = "上传文档") -> dict:
    """
    从用户上传的文本中提取重点
    返回: {"title": str, "one_liner": str, "concepts": [...], "quotes": [...], "chapters": [...]}
    """
    if USE_MOCK or _is_over_limit():
        return {
            "title": filename,
            "one_liner": "这是一份上传的文档，AI 已提取重点。",
            "concepts": [
                {"title": "核心要点一", "explanation": "文档中的第一个核心观点"},
                {"title": "核心要点二", "explanation": "文档中的第二个核心观点"},
                {"title": "核心要点三", "explanation": "文档中的第三个核心观点"},
            ],
            "quotes": ["文档中的金句1", "文档中的金句2"],
            "chapters": [],
        }

    # 截取前 4000 字避免 token 超限
    truncated = text[:4000] if len(text) > 4000 else text

    user_msg = f'用户上传了一份文档（文件名：{filename}），请提取重点内容。\n\n文档内容：\n{truncated}'

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": _EXTRACT_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=2000,   # 3000 → 2000
            temperature=0.5,
        )
        _log_api_call()
        content = response.choices[0].message.content.strip()
        print(f"[DeepSeek] 提取原始返回: {content[:200]}")
        result = _extract_json(content)
        if result:
            return result
        return {"title": filename, "one_liner": "提取失败", "concepts": [], "quotes": [], "chapters": []}
    except Exception as e:
        print(f"[DeepSeek] 提取失败: {e}")
        return {"title": filename, "one_liner": "提取失败", "concepts": [], "quotes": [], "chapters": []}


def _extract_json(content: str) -> dict | None:
    """从 API 返回中提取 JSON（统一处理）"""
    try:
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1:
            content = content[start:end+1]
        return json.loads(content)
    except Exception:
        return None


# ===== Mock 模式 =====

def _mock_summary(title: str, author: str) -> dict:
    """Mock 模式摘要"""
    return {
        "one_liner": f"《{title}》是一本值得深思的书，核心在于改变认知方式。",
        "concepts": [
            {"title": "核心思想", "explanation": f"《{title}》通过多个视角揭示了事物的本质，引导读者建立新的思维框架。"},
            {"title": "实践方法", "explanation": "书中提供了具体可操作的方法，将抽象理念转化为日常实践。"},
            {"title": "深层启示", "explanation": "读完此书，你会对自我、他人和世界产生新的理解层次。"},
        ],
        "quotes": [
            f"《{title}》告诉我们：真正的改变始于认知的突破。",
            "读一本好书，是和许多高尚的人谈话。",
        ],
    }


def _mock_answer(title: str, question: str) -> str:
    """Mock 模式回答"""
    return f"""关于《{title}》的这个问题——"{question}"

这是一个很好的问题。在 Mock 模式下，我无法给出深度解答。

💡 要启用真实 AI 对话，请在 `backend/.env` 文件中填写你的 DeepSeek API Key：
```
DEEPSEEK_API_KEY=你的Key
```
获取地址：https://platform.deepseek.com

填好后重启后端，即可获得基于本书内容的智能问答。"""
