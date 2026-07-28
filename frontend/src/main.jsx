import React from 'react'
import ReactDOM from 'react-dom/client'
import { HashRouter } from 'react-router-dom'
import App from './App.jsx'
import './index.css'

// PWA 自动更新：检测到新版本时自动清除缓存并刷新
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then(async (registrations) => {
    // 主动检查更新
    for (const reg of registrations) {
      await reg.update()
    }
    // 如果有注册，监听新版本
    if (registrations.length > 0) {
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        // 新 Service Worker 接管，强制刷新
        window.location.reload()
      })
    }
  })

  // 每30秒检查一次更新（确保用户能尽快看到新版本）
  setInterval(() => {
    navigator.serviceWorker.getRegistrations().then((registrations) => {
      registrations.forEach((reg) => reg.update())
    })
  }, 30000)
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <HashRouter>
      <App />
    </HashRouter>
  </React.StrictMode>
)
