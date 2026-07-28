"""直接测试 AI 返回"""
import os, httpx, json
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env")
key = os.getenv("DEEPSEEK_API_KEY")

from openai import OpenAI
client = OpenAI(api_key=key, base_url="https://api.deepseek.com", http_client=httpx.Client(verify=False))

r = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role":"user","content":"请为《非暴力沟通》生成摘要，返回JSON，包含 one_liner, concepts, quotes, chapters(每章有title,summary,highlight)"}],
    max_tokens=4000,
    temperature=0.7,
)
content = r.choices[0].message.content.strip()
print("原始返回长度:", len(content))
print("前500字:", content[:500])
print("---")
# 尝试解析
if "```" in content:
    content = content.split("```")[1]
    if content.startswith("json"):
        content = content[4:]
start = content.find("{")
end = content.rfind("}")
if start != -1 and end != -1:
    content = content[start:end+1]
data = json.loads(content)
print("字段:", list(data.keys()))
print("chapters:", json.dumps(data.get("chapters",[]), ensure_ascii=False)[:300])
