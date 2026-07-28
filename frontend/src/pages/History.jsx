import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useUserStore, useHistoryStore } from '../store/userStore'
import api from '../api/client'
import BookCard from '../components/BookCard'

export default function History() {
  const navigate = useNavigate()
  const { userId } = useUserStore()
  const { isRead } = useHistoryStore()
  const [books, setBooks] = useState([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('unread')

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get(`/books/history/${userId}`)
        setBooks(res.data)
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [userId])

  const unreadBooks = books.filter(b => !isRead(b.id))
  const readBooks = books.filter(b => isRead(b.id))

  return (
    <div className="px-6 py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">阅读历史</h1>
      </header>

      {/* 标签切换 */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setTab('unread')}
          className={`flex-1 py-2 rounded-xl text-sm font-medium transition-all ${
            tab === 'unread'
              ? 'bg-primary-600 text-white'
              : 'bg-slate-100 text-slate-500'
          }`}
        >
          📖 未读 ({unreadBooks.length})
        </button>
        <button
          onClick={() => setTab('read')}
          className={`flex-1 py-2 rounded-xl text-sm font-medium transition-all ${
            tab === 'read'
              ? 'bg-emerald-600 text-white'
              : 'bg-slate-100 text-slate-500'
          }`}
        >
          ✓ 已读 ({readBooks.length})
        </button>
      </div>

      {loading ? (
        <div className="card animate-pulse">
          <div className="h-6 bg-slate-200 rounded w-3/4 mb-3"></div>
          <div className="h-4 bg-slate-200 rounded w-1/2"></div>
        </div>
      ) : tab === 'unread' ? (
        unreadBooks.length > 0 ? (
          <div className="space-y-4">
            {unreadBooks.map(book => (
              <BookCard
                key={book.id}
                book={book}
                onClick={() => navigate(`/book/${book.id}`)}
              />
            ))}
          </div>
        ) : (
          <div className="card text-center text-slate-400">
            没有未读的书了 🎉
          </div>
        )
      ) : (
        readBooks.length > 0 ? (
          <div className="space-y-4">
            {readBooks.map(book => (
              <BookCard
                key={book.id}
                book={book}
                onClick={() => navigate(`/book/${book.id}`)}
              />
            ))}
          </div>
        ) : (
          <div className="card text-center text-slate-400">
            还没有读完的书
            <br />
            <span className="text-xs mt-2 block">在书详情页点"标记为已读"</span>
          </div>
        )
      )}
    </div>
  )
}
