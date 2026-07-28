import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useUserStore, useHistoryStore } from '../store/userStore'
import api from '../api/client'
import BookCard from '../components/BookCard'

export default function Home() {
  const navigate = useNavigate()
  const { userId } = useUserStore()
  const { addToHistory } = useHistoryStore()

  const [book, setBook] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadToday = async () => {
    setLoading(true)
    try {
      const res = await api.get(`/books/today/${userId}`)
      setBook(res.data)
      addToHistory(res.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const loadNext = async () => {
    setLoading(true)
    try {
      const res = await api.get(`/books/next/${userId}`)
      setBook(res.data)
      addToHistory(res.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadToday()
  }, [])

  return (
    <div className="px-6 py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">
          今日一书
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          {new Date().toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            weekday: 'long'
          })}
        </p>
      </header>

      {loading ? (
        <div className="card animate-pulse">
          <div className="h-6 bg-slate-200 rounded w-3/4 mb-3"></div>
          <div className="h-4 bg-slate-200 rounded w-1/2 mb-6"></div>
          <div className="h-4 bg-slate-200 rounded mb-2"></div>
          <div className="h-4 bg-slate-200 rounded w-5/6"></div>
        </div>
      ) : book ? (
        <>
          <BookCard
            book={book}
            onClick={() => navigate(`/book/${book.id}`)}
          />
          <button
            onClick={loadNext}
            className="btn-secondary w-full mt-4"
          >
            📚 再读一本
          </button>
        </>
      ) : (
        <div className="card text-center text-slate-500">
          暂无推荐，请稍后再试
        </div>
      )}
    </div>
  )
}
