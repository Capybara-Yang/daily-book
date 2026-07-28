import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'

export default function Upload() {
  const navigate = useNavigate()
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleUpload = async () => {
    if (!file) return
    setLoading(true)
    setError('')

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await api.post('/upload/extract', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000,
      })
      navigate(`/book/${res.data.id}`)
    } catch (err) {
      setError(err.response?.data?.detail || '上传失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="px-6 py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">上传文档</h1>
        <p className="text-sm text-slate-500 mt-1">
          上传 PDF/TXT/Markdown，AI 帮你提取重点和精彩部分
        </p>
      </header>

      <div className="card">
        <div className="mb-4">
          <label className="block text-sm text-slate-600 mb-2">
            选择文件
          </label>
          <input
            type="file"
            accept=".pdf,.txt,.md,.markdown"
            onChange={e => setFile(e.target.files[0])}
            className="w-full text-sm text-slate-500 file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-medium file:bg-primary-50 file:text-primary-600 hover:file:bg-primary-100"
          />
        </div>

        {file && (
          <div className="bg-slate-50 rounded-xl p-3 mb-4 text-sm text-slate-600">
            📄 {file.name} ({(file.size / 1024).toFixed(1)} KB)
          </div>
        )}

        {error && (
          <div className="text-red-500 text-sm mb-4 text-center">
            {error}
          </div>
        )}

        <button
          onClick={handleUpload}
          disabled={!file || loading}
          className="btn-primary w-full disabled:opacity-50"
        >
          {loading ? 'AI 提取中...' : '🤖 AI 提取重点'}
        </button>
      </div>

      <div className="mt-6 card bg-slate-50">
        <h3 className="text-sm font-bold text-slate-500 mb-3">支持格式</h3>
        <ul className="text-sm text-slate-600 space-y-1">
          <li>📄 PDF 文档</li>
          <li>📝 TXT 纯文本</li>
          <li>📋 Markdown 文件</li>
        </ul>
        <p className="text-xs text-slate-400 mt-3">
          AI 会提取核心要点、金句、精华段落，并标注最精彩的部分
        </p>
      </div>
    </div>
  )
}
