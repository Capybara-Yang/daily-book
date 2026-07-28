import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useEffect } from 'react'
import { useUserStore } from './store/userStore'
import Survey from './pages/Survey'
import Home from './pages/Home'
import BookDetail from './pages/BookDetail'
import Search from './pages/Search'
import Settings from './pages/Settings'
import Favorites from './pages/Favorites'
import History from './pages/History'
import Upload from './pages/Upload'
import Navbar from './components/Navbar'

function App() {
  const { userId } = useUserStore()
  const location = useLocation()

  // 如果未完成问卷，跳转到问卷页
  const showNavbar = userId && !location.hash.startsWith('#/survey')

  return (
    <div className="min-h-screen max-w-2xl mx-auto pb-20">
      <Routes>
        <Route path="/survey" element={<Survey />} />
        {!userId && <Route path="*" element={<Navigate to="/survey" />} />}
        {userId && (
          <>
            <Route path="/" element={<Home />} />
            <Route path="/book/:id" element={<BookDetail />} />
            <Route path="/search" element={<Search />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/favorites" element={<Favorites />} />
            <Route path="/history" element={<History />} />
            <Route path="/settings" element={<Settings />} />
          </>
        )}
      </Routes>
      {showNavbar && <Navbar />}
    </div>
  )
}

export default App
