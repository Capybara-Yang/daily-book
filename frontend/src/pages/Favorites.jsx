import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useUserStore } from '../store/userStore'
import api from '../api/client'
import BookCard from '../components/BookCard'

export default function Favorites() {
  const navigate = useNavigate()
  const { userId } = useUserStore()
  const [books, setBooks] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get(`/books/favorites/${userId}`)
        setBooks(res.data)
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [userId])

  return (
    <div className="px-6 py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">我的收藏</h1>
      </header>

      {loading ? (
        <div className="card animate-pulse">
          <div className="h-6 bg-slate-200 rounded w-3/4 mb-3"></div>
          <div className="h-4 bg-slate-200 rounded w-1/2"></div>
        </div>
      ) : books.length > 0 ? (
        <div className="space-y-4">
          {books.map(book => (
            <BookCard
              key={book.id}
              book={book}
              onClick={() => navigate(`/book/${book.id}`)}
            />
          ))}
        </div>
      ) : (
        <div className="card text-center text-slate-400">
          还没有收藏的书籍
          <br />
          点击书籍详情页的 ☆ 收藏
        </div>
      )}
    </div>
  )
}
