"""文件上传 + AI 提取 API"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from services.deepseek import extract_from_text
from services.database import get_conn
import json
import uuid
import io

router = APIRouter()

try:
    import PyPDF2
    HAS_PDF = True
except ImportError:
    HAS_PDF = False


@router.post("/extract")
async def extract_document(file: UploadFile = File(...)):
    """上传文件 → AI 提取重点"""
    content = await file.read()
    filename = file.filename or "上传文档"

    text = ""

    # PDF 文件
    if filename.lower().endswith(".pdf"):
        if not HAS_PDF:
            raise HTTPException(500, "PDF 解析库未安装")
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(content))
            for page in reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e:
            raise HTTPException(400, f"PDF 解析失败: {e}")

    # 文本文件
    elif filename.lower().endswith((".txt", ".md", ".markdown")):
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("gbk", errors="ignore")

    else:
        # 尝试当文本处理
        try:
            text = content.decode("utf-8")
        except:
            raise HTTPException(400, "不支持的文件格式，请上传 PDF、TXT 或 Markdown")

    if not text.strip():
        raise HTTPException(400, "文件内容为空")

    # 调 AI 提取
    result = extract_from_text(text, filename)

    # 存入数据库
    book_id = str(uuid.uuid4())[:8]
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO books (id, title, author, category, one_liner, concepts, quotes, story_summary, chapters, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, '', ?, 'uploaded')
    """, (
        book_id,
        result.get("title", filename),
        "上传文档",
        "我的上传",
        result.get("one_liner", ""),
        json.dumps(result.get("concepts", []), ensure_ascii=False),
        json.dumps(result.get("quotes", []), ensure_ascii=False),
        json.dumps(result.get("chapters", []), ensure_ascii=False),
    ))
    conn.commit()
    conn.close()

    return {
        "id": book_id,
        "title": result.get("title", filename),
        "author": "上传文档",
        "category": "我的上传",
        "one_liner": result.get("one_liner", ""),
        "concepts": result.get("concepts", []),
        "quotes": result.get("quotes", []),
        "chapters": result.get("chapters", []),
        "source": "uploaded",
    }
