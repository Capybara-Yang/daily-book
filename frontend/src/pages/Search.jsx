import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import BookCard from '../components/BookCard'

const DISCOVER_CATEGORIES = [
  '成功学', '心理学', '经济学', '哲学',
  '历史', '科幻', '传记', '管理学',
  '社会学', '人工智能', '投资理财', '沟通技巧',
  '自我成长', '时间管理', '领导力', '写作',
  '设计', '艺术', '音乐', '电影',
  '旅行', '美食', '养生', '育儿',
]

export default function Search() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [author, setAuthor] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [multipleResults, setMultipleResults] = useState(null)
  const [error, setError] = useState('')

  // 类别发现
  const [discoverMode, setDiscoverMode] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState('')
  const [customCategory, setCustomCategory] = useState('')
  const [discoverResults, setDiscoverResults] = useState([])
  const [discoverLoading, setDiscoverLoading] = useState(false)
  const [generatingBook, setGeneratingBook] = useState(null)

  const handleSearch = async () => {
    if (!query.trim() && !author.trim()) return
    setLoading(true)
    setError('')
    setResult(null)
    setMultipleResults(null)
    try {
      const res = await api.post('/books/search', {
        title: query.trim(),
        author: author.trim(),
      })
      if (res.data.multiple) {
        setMultipleResults(res.data.results)
      } else if (res.data.error) {
        setError(res.data.error)
      } else {
        setResult(res.data)
      }
    } catch (err) {
      setError('搜索失败，请稍后再试')
    } finally {
      setLoading(false)
    }
  }

  const handleDiscover = async (cat) => {
    setSelectedCategory(cat)
    setDiscoverLoading(true)
    setDiscoverResults([])
    try {
      const res = await api.post('/books/discover', { category: cat })
      setDiscoverResults(res.data.books || [])
    } catch (err) {
      setError('推荐失败，请稍后再试')
    } finally {
      setDiscoverLoading(false)
    }
  }

  const handleCustomDiscover = () => {
    if (!customCategory.trim()) return
    handleDiscover(customCategory.trim())
    setCustomCategory('')
  }

  const handleGenerateBook = async (title, author) => {
    setGeneratingBook(title)
    try {
      const res = await api.post('/books/search', { title, author })
      navigate(`/book/${res.data.id}`)
    } catch (err) {
      setError('生成摘要失败')
    } finally {
      setGeneratingBook(null)
    }
  }

  return (
    <div className="px-6 py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">发现书籍</h1>
        <p className="text-sm text-slate-500 mt-1">
          搜索特定书，或按类别发现新书
        </p>
      </header>

      {/* 模式切换 */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setDiscoverMode(false)}
          className={`flex-1 py-2 rounded-xl text-sm font-medium transition-all ${
            !discoverMode
              ? 'bg-primary-600 text-white'
              : 'bg-slate-100 text-slate-500'
          }`}
        >
          🔍 搜书名
        </button>
        <button
          onClick={() => setDiscoverMode(true)}
          className={`flex-1 py-2 rounded-xl text-sm font-medium transition-all ${
            discoverMode
              ? 'bg-primary-600 text-white'
              : 'bg-slate-100 text-slate-500'
          }`}
        >
          📚 按类别发现
        </button>
      </div>

      {error && (
        <div className="card text-center text-red-500 text-sm mb-4">
          {error}
        </div>
      )}

      {/* 搜书名模式 */}
      {!discoverMode && (
        <>
          <div className="space-y-3 mb-6">
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              placeholder="书名（可只记关键词，如：习惯）"
              className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:border-primary-400"
            />
            <input
              type="text"
              value={author}
              onChange={e => setAuthor(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              placeholder="作者（可只记姓氏，如：余华）"
              className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:border-primary-400"
            />
            <button
              onClick={handleSearch}
              disabled={(!query.trim() && !author.trim()) || loading}
              className="btn-primary w-full disabled:opacity-50"
            >
              {loading ? 'AI 搜索中...' : '🔍 搜索'}
            </button>
            <p className="text-xs text-slate-400 text-center">
              💡 记不全书名也没关系，输入记得的部分即可
            </p>
          </div>

          {/* 多本匹配结果 */}
          {multipleResults && (
            <div>
              <p className="text-sm text-slate-500 mb-3">
                {multipleResults.length > 0 && `找到 ${multipleResults.length} 本相关书籍：`}
              </p>
              <div className="space-y-3">
                {multipleResults.map(book => (
                  <BookCard
                    key={book.id}
                    book={book}
                    onClick={() => navigate(`/book/${book.id}`)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* 单本结果 */}
          {result && !multipleResults && (
            <div>
              <p className="text-sm text-slate-500 mb-3">
                {result.source === 'generated' ? '✨ AI 新生成' : '📚 已收录'}
              </p>
              <BookCard
                book={result}
                onClick={() => navigate(`/book/${result.id}`)}
              />
            </div>
          )}

          {/* 空状态 */}
          {!result && !multipleResults && !loading && !error && (
            <div className="card text-center text-slate-400 text-sm">
              搜索任意书籍，AI 会为你生成结构化摘要
              <br />
              <span className="text-xs mt-2 block">
                小说/戏剧/传记会自动生成故事概要
              </span>
            </div>
          )}
        </>
      )}

      {/* 按类别发现模式 */}
      {discoverMode && (
        <>
          {/* 自定义输入 */}
          <div className="card mb-4">
            <p className="text-sm text-slate-600 mb-3">
              想了解什么领域？输入任意关键词：
            </p>
            <div className="flex gap-2">
              <input
                type="text"
                value={customCategory}
                onChange={e => setCustomCategory(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleCustomDiscover()}
                placeholder="如：编程、摄影、冥想、茶道..."
                className="flex-1 px-4 py-2 rounded-xl border border-slate-200 focus:outline-none focus:border-primary-400 text-sm"
              />
              <button
                onClick={handleCustomDiscover}
                disabled={!customCategory.trim() || discoverLoading}
                className="btn-primary !px-4 !py-2 text-sm disabled:opacity-50"
              >
                推荐
              </button>
            </div>
          </div>

          {/* 预设类别 */}
          <p className="text-xs text-slate-400 mb-2">或选择热门领域：</p>
          <div className="grid grid-cols-3 gap-2 mb-6">
            {DISCOVER_CATEGORIES.map(cat => (
              <button
                key={cat}
                onClick={() => handleDiscover(cat)}
                className={`p-2.5 rounded-xl border-2 text-sm font-medium transition-all ${
                  selectedCategory === cat
                    ? 'border-primary-500 bg-primary-50 text-primary-700'
                    : 'border-slate-200 text-slate-600 hover:border-slate-300'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* 推荐结果 */}
          {discoverLoading && (
            <div className="card text-center text-slate-400 text-sm">
              AI 正在为你挑选 {selectedCategory} 领域的好书...
            </div>
          )}

          {!discoverLoading && discoverResults.length > 0 && (
            <div>
              <p className="text-sm text-slate-500 mb-3">
                📚 {selectedCategory}领域入门推荐
              </p>
              <div className="space-y-3">
                {discoverResults.map((book, i) => (
                  <div
                    key={i}
                    className="card cursor-pointer hover:shadow-md transition-shadow"
                    onClick={() => handleGenerateBook(book.title, book.author)}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h4 className="font-bold text-slate-800">
                          《{book.title}》
                        </h4>
                        <p className="text-xs text-slate-500">{book.author}</p>
                      </div>
                      {generatingBook === book.title ? (
                        <span className="text-xs text-primary-600">生成中...</span>
                      ) : (
                        <span className="text-xs text-primary-500">点击查看 →</span>
                      )}
                    </div>
                    <p className="text-sm text-slate-600 leading-relaxed">
                      {book.reason}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {!discoverLoading && discoverResults.length === 0 && (
            <div className="card text-center text-slate-400 text-sm">
              输入你感兴趣的领域，或选择上方类别
              <br />
              <span className="text-xs mt-2 block">
                AI 会推荐 4 本入门书并说明理由
              </span>
            </div>
          )}
        </>
      )}
    </div>
  )
}
