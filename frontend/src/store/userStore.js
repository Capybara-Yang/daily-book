import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useUserStore = create(
  persist(
    (set) => ({
      userId: null,
      survey: null,
      setUserId: (id) => set({ userId: id }),
      setSurvey: (survey) => set({ survey }),
      logout: () => set({ userId: null, survey: null }),
    }),
    { name: 'daily-book-user' }
  )
)

export const useFavoritesStore = create(
  persist(
    (set, get) => ({
      favorites: [],
      toggleFavorite: (bookId) => {
        const { favorites } = get()
        if (favorites.includes(bookId)) {
          set({ favorites: favorites.filter(id => id !== bookId) })
        } else {
          set({ favorites: [...favorites, bookId] })
        }
      },
      isFavorite: (bookId) => get().favorites.includes(bookId),
    }),
    { name: 'daily-book-favorites' }
  )
)

export const useHistoryStore = create(
  persist(
    (set, get) => ({
      history: [],
      readBooks: [],
      addToHistory: (book) => {
        const { history } = get()
        const filtered = history.filter(b => b.id !== book.id)
        set({ history: [book, ...filtered].slice(0, 50) })
      },
      markAsRead: (bookId) => {
        const { readBooks } = get()
        if (!readBooks.includes(bookId)) {
          set({ readBooks: [...readBooks, bookId] })
        }
      },
      isRead: (bookId) => get().readBooks.includes(bookId),
    }),
    { name: 'daily-book-history' }
  )
)

export const useCheckinStore = create(
  persist(
    (set, get) => ({
      checkinDates: [],
      checkin: () => {
        const today = new Date().toISOString().slice(0, 10)
        const { checkinDates } = get()
        if (checkinDates.includes(today)) return false
        set({ checkinDates: [...checkinDates, today] })
        return true
      },
      hasCheckedInToday: () => {
        const today = new Date().toISOString().slice(0, 10)
        return get().checkinDates.includes(today)
      },
      getStreak: () => {
        const { checkinDates } = get()
        if (checkinDates.length === 0) return 0
        const sorted = [...checkinDates].sort().reverse()
        let streak = 0
        let checkDate = new Date()
        for (let i = 0; i < 365; i++) {
          const dateStr = checkDate.toISOString().slice(0, 10)
          if (sorted.includes(dateStr)) {
            streak++
            checkDate.setDate(checkDate.getDate() - 1)
          } else if (i === 0) {
            // 今天还没打卡，不算断
            checkDate.setDate(checkDate.getDate() - 1)
          } else {
            break
          }
        }
        return streak
      },
    }),
    { name: 'daily-book-checkin' }
  )
)
