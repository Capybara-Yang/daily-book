"""测试章节概要功能"""
import requests
import json

# 先删旧记录
from services.database import get_conn
c = get_conn().cursor()
c.execute("DELETE FROM books WHERE title='非暴力沟通'")
get_conn().commit()

# 搜索生成
r = requests.post("http://127.0.0.1:8000/api/books/search",
    json={"title":"非暴力沟通","author":"马歇尔·卢森堡"}, timeout=40)
d = r.json()
print("一句话:", d["one_liner"])
chs = d.get("chapters", [])
print(f"章节数: {len(chs)}")
for ch in chs[:2]:
    print(f"  章: {ch['title']}")
    print(f"  概要: {ch['summary']}")
    print(f"  精彩: {ch['highlight'][:60]}")
    print()
