import { NavLink } from 'react-router-dom'

const navItems = [
  { to: '/', icon: '📖', label: '今日' },
  { to: '/search', icon: '🔍', label: '搜索' },
  { to: '/upload', icon: '📤', label: '上传' },
  { to: '/favorites', icon: '⭐', label: '收藏' },
  { to: '/settings', icon: '⚙️', label: '设置' },
]

export default function Navbar() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 max-w-2xl mx-auto bg-white border-t border-slate-200 px-2 py-2 z-50">
      <div className="flex justify-around items-center">
        {navItems.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex flex-col items-center gap-0.5 px-3 py-1 rounded-lg transition-colors ${
                isActive ? 'text-primary-600' : 'text-slate-400'
              }`
            }
          >
            <span className="text-xl">{item.icon}</span>
            <span className="text-xs">{item.label}</span>
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
