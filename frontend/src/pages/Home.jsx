import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useUserStore, useHistoryStore, useCheckinStore } from '../store/userStore'
import api from '../api/client'
import BookCard from '../components/BookCard'

export default function Home() {
  const navigate = useNavigate()
  const { userId } = useUserStore()
  const { addToHistory } = useHistoryStore()
  const { checkin, hasCheckedInToday, getStreak } = useCheckinStore()

  const [books, setBooks] = useState([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [offset, setOffset] = useState(0)

  const loadToday5 = async (newOffset = 0) => {
    setLoading(true)
    try {
      const res = await api.get(`/books/today5/${userId}?offset=${newOffset}`)
      setBooks(res.data.books || [])
      setOffset(newOffset)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleSelectBook = async (book) => {
    checkin()
    addToHistory(book)
    try {
      await api.post(`/books/select/${userId}/${book.id}`)
    } catch (e) {}
    navigate(`/book/${book.id}`)
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    await loadToday5(offset + 5)
    setRefreshing(false)
  }

  useEffect(() => {
    loadToday5()
  }, [])

  const streak = getStreak()
  const checkedIn = hasCheckedInToday()

  return (
    <div className="px-6 py-8">
      <header className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">今日推荐</h1>
            <p className="text-sm text-slate-500 mt-1">
              {new Date().toLocaleDateString('zh-CN', {
                year: 'numeric', month: 'long', day: 'numeric', weekday: 'long'
              })}
            </p>
          </div>
          {streak > 0 && (
            <div className="text-center">
              <div className="text-2xl">🔥</div>
              <div className="text-sm font-bold text-orange-500">{streak}</div>
              <div className="text-xs text-slate-400">连续天数</div>
            </div>
          )}
        </div>
        {checkedIn && (
          <div className="mt-2 text-xs text-emerald-600 bg-emerald-50 rounded-lg px-3 py-1 inline-block">
            ✅ 今日已打卡
          </div>
        )}
      </header>

      {loading ? (
        <div className="space-y-3">
          {[1,2,3,4,5].map(i => (
            <div key={i} className="card animate-pulse">
              <div className="h-5 bg-slate-200 rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-slate-200 rounded w-1/2 mb-3"></div>
              <div className="h-3 bg-slate-200 rounded w-5/6"></div>
            </div>
          ))}
        </div>
      ) : books.length > 0 ? (
        <>
          <p className="text-sm text-slate-500 mb-3">
            📚 为你精选 {books.length} 本，选一本开始阅读吧
          </p>
          <div className="space-y-3">
            {books.map((book, i) => (
              <div key={book.id} className="relative">
                <div className="absolute -left-2 -top-2 z-10 w-6 h-6 rounded-full bg-primary-500 text-white text-xs font-bold flex items-center justify-center shadow-md">
                  {i + 1}
                </div>
                <BookCard
                  book={book}
                  onClick={() => handleSelectBook(book)}
                />
              </div>
            ))}
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="btn-secondary w-full mt-4 disabled:opacity-50"
          >
            {refreshing ? '换一批中...' : '🔄 换一批'}
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
