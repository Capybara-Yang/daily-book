"""测试 DeepSeek API 连通性"""
import os, httpx
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
key = os.getenv('DEEPSEEK_API_KEY')
print('Key:', key[:15] if key else '空')

from openai import OpenAI
client = OpenAI(api_key=key, base_url='https://api.deepseek.com', http_client=httpx.Client(verify=False))
print('调用 DeepSeek...')
r = client.chat.completions.create(
    model='deepseek-chat',
    messages=[{'role':'user','content':'说一个字'}],
    max_tokens=10
)
print('响应:', r.choices[0].message.content)
