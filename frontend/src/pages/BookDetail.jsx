import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useUserStore, useFavoritesStore, useHistoryStore } from '../store/userStore'
import api from '../api/client'
import SummaryView from '../components/SummaryView'
import ChatBox from '../components/ChatBox'

export default function BookDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { userId } = useUserStore()
  const { favorites, toggleFavorite } = useFavoritesStore()
  const { markAsRead, isRead } = useHistoryStore()

  const [book, setBook] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchBook = async () => {
      try {
        const historyRes = await api.get(`/books/history/${userId}`)
        const found = historyRes.data.find(b => b.id === id)
        if (found) {
          setBook(found)
          setLoading(false)
          return
        }
        const allRes = await api.get('/books/all')
        const foundBook = allRes.data.find(b => b.id === id)
        if (foundBook) setBook(foundBook)
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    fetchBook()
  }, [id, userId])

  const isFav = favorites.includes(id)
  const readAlready = isRead(id)

  if (loading) {
    return (
      <div className="px-6 py-8">
        <div className="card animate-pulse">
          <div className="h-8 bg-slate-200 rounded w-3/4 mb-3"></div>
          <div className="h-4 bg-slate-200 rounded w-1/2 mb-6"></div>
        </div>
      </div>
    )
  }

  if (!book) {
    return (
      <div className="px-6 py-8 text-center text-slate-500">
        <p>找不到这本书</p>
        <button onClick={() => navigate(-1)} className="btn-secondary mt-4">
          返回
        </button>
      </div>
    )
  }

  return (
    <div className="px-6 py-8">
      <button
        onClick={() => navigate(-1)}
        className="text-slate-400 text-sm mb-4 flex items-center gap-1"
      >
        ← 返回
      </button>

      <div className="mb-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-slate-800 mb-2">
              《{book.title}》
            </h1>
            <p className="text-slate-500">{book.author}</p>
          </div>
          <button
            onClick={() => toggleFavorite(book.id)}
            className="flex-shrink-0 w-10 h-10 rounded-full bg-slate-50 flex items-center justify-center text-xl"
          >
            {isFav ? '⭐' : '☆'}
          </button>
        </div>
        <div className="flex items-center gap-2 mt-3">
          {book.category && (
            <span className="tag bg-primary-50 text-primary-600">
              {book.category}
            </span>
          )}
          {readAlready && (
            <span className="tag bg-emerald-50 text-emerald-600">
              ✓ 已读
            </span>
          )}
        </div>
      </div>

      {/* 已读按钮 */}
      {!readAlready && (
        <button
          onClick={() => markAsRead(book.id)}
          className="w-full mb-4 py-2.5 rounded-xl bg-emerald-50 text-emerald-600 text-sm font-medium border border-emerald-200 hover:bg-emerald-100 transition-colors"
        >
          📖 标记为已读
        </button>
      )}

      <SummaryView book={book} />

      <div className="mt-6">
        <ChatBox book={book} />
      </div>
    </div>
  )
}
