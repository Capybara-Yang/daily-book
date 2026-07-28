"""
DeepSeek API 封装
双模式：无 API Key 时使用 Mock 模式
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# 用绝对路径加载 .env，避免工作目录问题
ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(ENV_PATH)

# 优先从环境变量读取，否则使用内置 Key（注意：公开仓库会暴露此 Key）
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY") or "sk-3411b5d1944a4df3ac1fb59da6ad57ce"

USE_MOCK = not DEEPSEEK_API_KEY
print(f"[DeepSeek] 模式: {'Mock' if USE_MOCK else '真实 API'}, Key: {DEEPSEEK_API_KEY[:10] if not USE_MOCK else '无'}")

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


def generate_summary(title: str, author: str = "") -> dict:
    """
    生成书籍摘要
    返回: {"one_liner": str, "concepts": [...], "quotes": [...], "story_summary": str(可选)}
    """
    if USE_MOCK:
        return _mock_summary(title, author)

    prompt = f"""请为《{title}》（作者：{author}）生成结构化摘要。

目标用户：没时间或不愿意读完整本书的人，想快速了解书的内容和精彩部分在哪里。

第一步，判断这本书是否属于"叙事性作品"。以下类型都属于叙事性作品，需要故事概要：
- 小说（长篇/中篇/短篇）
- 戏剧、剧本（话剧/戏曲/电影剧本）
- 传记、回忆录
- 纪实文学、报告文学
- 史诗、叙事诗
- 童话、寓���故事
- 任何以讲故事为主的作品

如果不属于上述类型（如方法论、科普、哲学、商业、自助、技术类等），则不需要故事概要。

第二步，根据判断结果生成摘要：

如果是叙事性作品：
- story_summary：200字内的故事梗概（讲清楚主要情节、人物、冲突、结局）
- concepts：3 个核心主题（这本书想探讨什么，而非知识点）
- one_liner：一句话点出本书精髓

如果不是叙事性作品：
- story_summary：留空字符串 ""
- concepts：3 个核心概念（知识点/方法论）
- one_liner：一句话核心观点

第三步，生成章节概要：
- 列出这本书最重要的 3-5 个章节（不是全部章节，挑最精华的）
- 每章给一句话概要
- 标注这章"最精彩的部分"是什么（具体到哪个观点/哪个情节/哪个案例）
- 为每章提供一段"原文摘录"（excerpt字段）：尽量还原该章节中最精彩的约100-150字的原文片段，让用户点击精彩部分时能直接读到原文。如果是小说/戏剧，摘录最动人的情节描写或对话；如果是方法论/科普，摘录最核心的论述段落。

严格按以下 JSON 格式返回（不要加 markdown 代码块）：

{{
  "one_liner": "一句话，20字以内",
  "story_summary": "叙事性作品写200字梗概，其他留空字符串",
  "concepts": [
    {{"title": "标题", "explanation": "解释说明，50字以内"}}
  ],
  "quotes": ["金句1", "金句2"],
  "chapters": [
    {{"title": "章节名", "summary": "一句话概要", "highlight": "最精彩的部分是什么，具体说明", "excerpt": "约100-150字的原文摘录，尽量接近原书文字"}}
  ]
}}

要求：
- quotes 提供 2 条金句
- chapters 提供 3-5 个精华章节
- 内容要精炼、深刻、有启发性
- 必须返回合法 JSON"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.7,
        )
        content = response.choices[0].message.content.strip()
        print(f"[DeepSeek] 摘要原��返回: {content[:300]}")
        # 尝试提取 JSON
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()
        # 找到第一个 { 和最后一个 }，提取 JSON
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1:
            content = content[start:end+1]
        result = json.loads(content)
        print(f"[DeepSeek] 解析成功，字段: {list(result.keys())}, chapters数: {len(result.get('chapters',[]))}")
        return result
    except Exception as e:
        print(f"[DeepSeek] 生成摘要失败: {e}")
        return _mock_summary(title, author)


def discover_by_category(category: str) -> list:
    """
    根据类别推荐 3-5 本入门书
    返回: [{"title": str, "author": str, "reason": str}]
    """
    if USE_MOCK:
        return _mock_discover(category)

    prompt = f"""用户想了解"{category}"领域的书，但他对这个领域不了解。
请推荐 4 本最适合入门的经典书籍。

严格按以下 JSON 格式返回（不要加 markdown 代码块）：

{{
  "books": [
    {{"title": "书名", "author": "作者", "reason": "为什么推荐这本作为入门书，30字以内"}}
  ]
}}

要求：
- 推荐 4 本书
- 优先选择口碑好、易读、适合新手的入门书
- 覆盖该领域不同侧面
- 必须返回合法 JSON"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.7,
        )
        content = response.choices[0].message.content.strip()
        print(f"[DeepSeek] 发现原始返回: {content[:300]}")
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1:
            content = content[start:end+1]
        data = json.loads(content)
        return data.get("books", [])
    except Exception as e:
        print(f"[DeepSeek] 发现失败: {e}")
        return _mock_discover(category)


def _mock_discover(category: str) -> list:
    return [
        {"title": f"{category}入门一", "author": "佚名", "reason": "经典入门书，通俗易懂"},
        {"title": f"{category}入门二", "author": "佚名", "reason": "系统全面，适合新手"},
    ]


def chat_about_book(title: str, summary: str, question: str, history=None) -> str:
    """针对书籍内容回答问题"""
    if USE_MOCK:
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
            max_tokens=500,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[DeepSeek] 对话失败: {e}")
        return _mock_answer(title, question)


def extract_from_text(text: str, filename: str = "上传文档") -> dict:
    """
    从用户上传的文本中提取重点
    返回: {"title": str, "one_liner": str, "concepts": [...], "quotes": [...], "chapters": [...]}
    """
    if USE_MOCK:
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

    prompt = f"""用户上传了一份文档（文件名：{filename}），请提取重点内容。

目标用户：没时间读完整文档的人，想快速了解内容和精彩部分在哪里。

严格按以下 JSON 格式返回（不要加 markdown 代码块）：

{{
  "title": "给这份文档起一个简洁的标题",
  "one_liner": "一句话概括核心内容，20字以内",
  "concepts": [
    {{"title": "核心要点标题", "explanation": "解释说明，50字以内"}}
  ],
  "quotes": ["文档中的金句或重要原话1", "金句2"],
  "chapters": [
    {{"title": "段落/章节名", "summary": "一句话概要", "highlight": "最精彩的部分是什么", "excerpt": "约100-150字的原文摘录"}}
  ]
}}

要求：
- concepts 提供 3 个核心要点
- quotes 提供 2 条文档中的原话
- chapters 提供 2-4 个精华段落
- excerpt 必须从文档原文中直接摘取，不要改写
- 必须基于文档实际内容，不要编造
- 必须返回合法 JSON

文档内容：
{truncated}"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=3000,
            temperature=0.5,
        )
        content = response.choices[0].message.content.strip()
        print(f"[DeepSeek] 提取原始返回: {content[:300]}")
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
    except Exception as e:
        print(f"[DeepSeek] 提取失败: {e}")
        return {"title": filename, "one_liner": "提取失败", "concepts": [], "quotes": [], "chapters": []}


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
