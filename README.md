# 每日一书 📖

每天推荐一本好书，AI 为你提炼精华。PWA 应用，手机/电脑浏览器打开即用，可安装到主屏幕。

## 在线预览

👉 **[点击打开 Railway 部署版](https://daily-book-production.up.railway.app/)**

> Railway 免费额度：30 天或 $5 试用，之后需要升级或迁移。

## 功能

- **每日推荐**：根据阅读偏好每天推一本书
- **结构化摘要**：一句话核心 + 三大概念 + 金句
- **AI 对话追问**：针对每本书提问，AI 基于书的内容回答
- **搜索实时讲解**：搜索任意书，AI 即时生成摘要
- **阅读偏好问卷**：兴趣领域 + 阅读节奏 + 探索比例
- **多本阅读**：「再读一本」按钮，无上限
- **收藏 / 历史**：本地持久化
- **定时推送**：每日刷新 + Web Push / 邮件（可选）
- **PWA**：可安装到主屏幕，离线缓存

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | React 18 + Vite + TailwindCSS + Zustand |
| 后端 | FastAPI (Python 3.11) + SQLite + APScheduler |
| AI | DeepSeek API（双模式：Mock / 真实） |
| PWA | vite-plugin-pwa |

## 快速开始

### 1. 启动后端

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # 填入 DeepSeek API Key（可选，不填用 Mock 模式）
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. 启动前端

```bash
cd frontend
pnpm install
pnpm dev
```

打开 http://localhost:5173 即可使用。

### 3. 启用真实 AI（可选）

1. 去 https://platform.deepseek.com 注册获取 API Key
2. 编辑 `backend/.env`，填入：
   ```
   DEEPSEEK_API_KEY=你的Key
   ```
3. 重启后端

不填 Key 时自动使用 Mock 模式，对话和搜索功能可用预设回答跑通流程。

## 成本估算（DeepSeek）

| 操作 | 单次成本 |
|------|---------|
| 生成一本书摘要 | ≈ ¥0.001 |
| 一本书 + 10 个问题对话 | ≈ ¥0.011 |
| 每天读 1 本书 + 20 问 | ≈ ¥0.02/天 |
| 每月 | ≈ ¥0.6 |

## 目录结构

```
daily-book/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── api/                 # API 路由
│   │   ├── books.py         # 书库 / 推荐 / 搜索
│   │   ├── chat.py          # 对话追问
│   │   ├── survey.py        # 问卷
│   │   └── user.py          # 用户设置
│   ├── services/
│   │   ├── database.py      # SQLite 管理
│   │   ├── deepseek.py      # DeepSeek 封装（Mock + 真实）
│   │   ├── recommender.py   # 推荐算法
│   │   └── scheduler.py     # 定时任务
│   ├── data/
│   │   ├── books.json       # 初始 30 本书
│   │   └── daily_books.db   # SQLite（运行时生成）
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/           # 问卷 / 首页 / 详情 / 搜索 / 设置
│   │   ├── components/      # BookCard / SummaryView / ChatBox / Navbar
│   │   ├── store/           # Zustand 状态管理
│   │   └── api/             # Axios 封装
│   └── vite.config.js
└── README.md
```

## 初始书库（30 本）

| 领域 | 书目 |
|------|------|
| 心理/成长 | 原子习惯、被讨厌的勇气、心流、思考快与慢、活出生命的意义 |
| 商业/创业 | 精益创业、从0到1、原则、富爸爸穷爸爸 |
| 科技/未来 | 人类简史、未来简史、AI 3.0、区块链革命 |
| 哲学/思辨 | 苏菲的世界、存在与时间、西西弗神话、沉思录 |
| 历史/人文 | 万历十五年、枪炮病菌与钢铁、人类群星闪耀时 |
| 科学/科普 | 时间简史、上帝掷骰子吗、自私的基因 |
| 文学/小说 | 小王子、月亮与六便士、活着、百年孤独 |
| 健康/生活 | 睡眠革命、饮食术、运动改造大脑 |

## 部署到生产

### 前端构建
```bash
cd frontend
pnpm build
# 生成 dist/ 目录，部署到任意静态服务器
```

### 后端部署
```bash
cd backend
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Nginx 反向代理示例
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /path/to/frontend/dist;
        try_files $uri /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

## License

MIT
