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
      addToHistory: (book) => {
        const { history } = get()
        const filtered = history.filter(b => b.id !== book.id)
        set({ history: [book, ...filtered].slice(0, 50) })
      },
    }),
    { name: 'daily-book-history' }
  )
)
