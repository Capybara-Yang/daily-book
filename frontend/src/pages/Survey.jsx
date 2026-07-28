import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useUserStore } from '../store/userStore'
import api from '../api/client'

const CATEGORIES = [
  '商业/创业', '心理/成长', '科技/未来', '历史/人文',
  '哲学/思辨', '文学/小说', '科学/科普', '健康/生活'
]

const PACES = [
  { value: 'daily', label: '一天一本（快节奏）' },
  { value: 'two-day', label: '两天一本（适中）' },
  { value: 'weekly', label: '一周一本（精读）' },
]

const PURPOSES = [
  '提升技能', '拓宽视野', '解决问题', '放松享受'
]

export default function Survey() {
  const navigate = useNavigate()
  const { setUserId, setSurvey } = useUserStore()

  const [step, setStep] = useState(0)
  const [categories, setCategories] = useState([])
  const [pace, setPace] = useState('daily')
  const [exploreRatio, setExploreRatio] = useState(0.4)
  const [purposes, setPurposes] = useState([])
  const [submitting, setSubmitting] = useState(false)

  const toggleCategory = (cat) => {
    setCategories(prev =>
      prev.includes(cat) ? prev.filter(c => c !== cat) : [...prev, cat]
    )
  }

  const togglePurpose = (p) => {
    setPurposes(prev =>
      prev.includes(p) ? prev.filter(x => x !== p) : [...prev, p]
    )
  }

  const handleSubmit = async () => {
    setSubmitting(true)
    try {
      const res = await api.post('/survey/submit', {
        categories,
        pace,
        explore_ratio: exploreRatio,
        purposes,
      })
      setUserId(res.data.user_id)
      setSurvey(res.data.survey)
      navigate('/')
    } catch (err) {
      alert('提交失败，请重试')
    } finally {
      setSubmitting(false)
    }
  }

  const steps = [
    // Step 0: 兴趣领域
    {
      title: '你最感兴趣哪些领域？',
      subtitle: '可多选，这决定了你的兴趣书池',
      content: (
        <div className="grid grid-cols-2 gap-3">
          {CATEGORIES.map(cat => (
            <button
              key={cat}
              onClick={() => toggleCategory(cat)}
              className={`p-4 rounded-xl border-2 text-sm font-medium transition-all ${
                categories.includes(cat)
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-slate-200 text-slate-600 hover:border-slate-300'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      ),
      canNext: categories.length > 0,
    },
    // Step 1: 阅读节奏
    {
      title: '你的阅读节奏？',
      subtitle: '可以之后在设置中修改',
      content: (
        <div className="space-y-3">
          {PACES.map(p => (
            <button
              key={p.value}
              onClick={() => setPace(p.value)}
              className={`w-full p-4 rounded-xl border-2 text-left transition-all ${
                pace === p.value
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-slate-200 hover:border-slate-300'
              }`}
            >
              <span className={`text-sm font-medium ${pace === p.value ? 'text-primary-700' : 'text-slate-600'}`}>
                {p.label}
              </span>
            </button>
          ))}
        </div>
      ),
      canNext: true,
    },
    // Step 2: 探索比例
    {
      title: '你想要多少"意外之书"？',
      subtitle: '探索比例控制兴趣外书籍的占比',
      content: (
        <div className="space-y-6">
          <div className="text-center">
            <div className="text-4xl font-bold text-primary-600 mb-2">
              {Math.round(exploreRatio * 100)}%
            </div>
            <div className="text-sm text-slate-500">
              {exploreRatio === 0 && '全部读我感兴趣的'}
              {exploreRatio === 1 && '全部探索新领域'}
              {exploreRatio > 0 && exploreRatio < 1 && `${Math.round((1-exploreRatio)*100)}% 兴趣 + ${Math.round(exploreRatio*100)}% 探索`}
            </div>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={exploreRatio * 100}
            onChange={e => setExploreRatio(e.target.value / 100)}
            className="w-full accent-primary-600"
          />
          <div className="flex justify-between text-xs text-slate-400">
            <span>全兴趣</span>
            <span>全探索</span>
          </div>
          <div className="bg-slate-50 rounded-xl p-4 text-sm text-slate-600 leading-relaxed">
            💡 比如 60% 兴趣 + 40% 探索，意味着每推 10 本书，6 本来自你选的领域，4 本是你没选但口碑好的入门书。
          </div>
        </div>
      ),
      canNext: true,
    },
    // Step 3: 阅读目的
    {
      title: '你的阅读目的？',
      subtitle: '可多选，帮助我们更好地匹配',
      content: (
        <div className="grid grid-cols-2 gap-3">
          {PURPOSES.map(p => (
            <button
              key={p}
              onClick={() => togglePurpose(p)}
              className={`p-4 rounded-xl border-2 text-sm font-medium transition-all ${
                purposes.includes(p)
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-slate-200 text-slate-600 hover:border-slate-300'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      ),
      canNext: purposes.length > 0,
    },
  ]

  const current = steps[step]

  return (
    <div className="min-h-screen px-6 py-12">
      <div className="max-w-md mx-auto">
        {/* 进度条 */}
        <div className="flex gap-2 mb-8">
          {steps.map((_, i) => (
            <div
              key={i}
              className={`h-1 flex-1 rounded-full transition-colors ${
                i <= step ? 'bg-primary-600' : 'bg-slate-200'
              }`}
            />
          ))}
        </div>

        {/* 标题 */}
        <h1 className="text-2xl font-bold text-slate-800 mb-2">
          {current.title}
        </h1>
        <p className="text-sm text-slate-500 mb-8">{current.subtitle}</p>

        {/* 内容 */}
        <div className="mb-8">
          {current.content}
        </div>

        {/* 按钮 */}
        <div className="flex gap-3">
          {step > 0 && (
            <button
              onClick={() => setStep(step - 1)}
              className="btn-secondary flex-1"
            >
              上一步
            </button>
          )}
          {step < steps.length - 1 ? (
            <button
              onClick={() => setStep(step + 1)}
              disabled={!current.canNext}
              className="btn-primary flex-1 disabled:opacity-50"
            >
              下一步
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!current.canNext || submitting}
              className="btn-primary flex-1 disabled:opacity-50"
            >
              {submitting ? '生成推荐中...' : '开始阅读 ✨'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
