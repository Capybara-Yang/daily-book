"""测试完整返回"""
import requests
import json
from services.database import get_conn

c = get_conn().cursor()
c.execute("DELETE FROM books WHERE title='非暴力沟通'")
get_conn().commit()

r = requests.post("http://127.0.0.1:8000/api/books/search",
    json={"title":"非暴力沟通","author":"马歇尔·卢森堡"}, timeout=60)
d = r.json()
print("所有字段:", list(d.keys()))
print("chapters:", json.dumps(d.get("chapters",[]), ensure_ascii=False, indent=2)[:500])
