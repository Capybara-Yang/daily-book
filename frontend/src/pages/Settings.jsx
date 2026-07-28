import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useUserStore } from '../store/userStore'
import api from '../api/client'

export default function Settings() {
  const navigate = useNavigate()
  const { userId, survey, logout } = useUserStore()

  const [pushEnabled, setPushEnabled] = useState(false)
  const [pushTime, setPushTime] = useState('07:00')
  const [email, setEmail] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get(`/user/settings/${userId}`)
        setPushEnabled(res.data.push_enabled)
        setPushTime(res.data.push_time || '07:00')
        setEmail(res.data.email || '')
      } catch (err) {
        console.error(err)
      }
    }
    load()
  }, [userId])

  const handleSave = async () => {
    setSaving(true)
    try {
      await api.put('/user/push-settings', {
        user_id: userId,
        push_enabled: pushEnabled,
        push_time: pushTime,
        email: email || null,
      })
      alert('设置已保存')
    } catch (err) {
      alert('保存失败')
    } finally {
      setSaving(false)
    }
  }

  const handleLogout = () => {
    if (confirm('确定退出？问卷和偏好将清除，需重新填写。')) {
      logout()
      navigate('/survey')
    }
  }

  return (
    <div className="px-6 py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">设置</h1>
      </header>

      {/* 偏好信息 */}
      {survey && (
        <div className="card mb-6">
          <h3 className="text-sm font-bold text-slate-500 mb-4 uppercase tracking-wide">
            我的阅读偏好
          </h3>
          <div className="space-y-3 text-sm">
            <div>
              <span className="text-slate-400">兴趣领域：</span>
              <span className="text-slate-700">{survey.categories?.join('、')}</span>
            </div>
            <div>
              <span className="text-slate-400">阅读节奏：</span>
              <span className="text-slate-700">
                {survey.pace === 'daily' && '一天一本'}
                {survey.pace === 'two-day' && '两天一本'}
                {survey.pace === 'weekly' && '一周一本'}
              </span>
            </div>
            <div>
              <span className="text-slate-400">探索比例：</span>
              <span className="text-slate-700">
                {Math.round(survey.explore_ratio * 100)}%
              </span>
            </div>
            <div>
              <span className="text-slate-400">阅读目的：</span>
              <span className="text-slate-700">{survey.purposes?.join('、')}</span>
            </div>
          </div>
        </div>
      )}

      {/* 推送设置 */}
      <div className="card mb-6">
        <h3 className="text-sm font-bold text-slate-500 mb-4 uppercase tracking-wide">
          每日推送
        </h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-700">开启每日推送提醒</span>
            <button
              onClick={() => setPushEnabled(!pushEnabled)}
              className={`w-12 h-6 rounded-full transition-colors relative ${
                pushEnabled ? 'bg-primary-600' : 'bg-slate-300'
              }`}
            >
              <span className={`absolute top-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
                pushEnabled ? 'translate-x-6' : 'translate-x-0.5'
              }`} />
            </button>
          </div>
          <div>
            <label className="text-sm text-slate-700 block mb-2">推送时间</label>
            <input
              type="time"
              value={pushTime}
              onChange={e => setPushTime(e.target.value)}
              className="px-4 py-2 rounded-xl border border-slate-200 focus:outline-none focus:border-primary-400"
            />
          </div>
          <div>
            <label className="text-sm text-slate-700 block mb-2">邮箱（可选，用于邮件推送）</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full px-4 py-2 rounded-xl border border-slate-200 focus:outline-none focus:border-primary-400"
            />
          </div>
          <button
            onClick={handleSave}
            disabled={saving}
            className="btn-primary w-full disabled:opacity-50"
          >
            {saving ? '保存中...' : '保存设置'}
          </button>
        </div>
      </div>

      {/* 关于 */}
      <div className="card mb-6">
        <h3 className="text-sm font-bold text-slate-500 mb-3 uppercase tracking-wide">
          更多
        </h3>
        <button
          onClick={() => navigate('/upload')}
          className="w-full py-3 text-left text-sm text-slate-700 flex items-center justify-between hover:text-primary-600 transition-colors"
        >
          <span>📤 上传文档提取重点</span>
          <span className="text-slate-400">→</span>
        </button>
      </div>

      {/* 版本信息 */}
      <div className="card mb-6">
        <p className="text-sm text-slate-600 leading-relaxed">
          每日一书 v1.3<br />
          每天推荐好书，AI 为你提炼精华。
        </p>
      </div>

      {/* 退出 */}
      <button
        onClick={handleLogout}
        className="w-full py-3 text-red-500 text-sm font-medium"
      >
        重置（重新填写问卷）
      </button>
    </div>
  )
}
