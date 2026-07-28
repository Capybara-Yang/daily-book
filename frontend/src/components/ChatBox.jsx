import { useState, useRef, useEffect } from 'react'
import api from '../api/client'

export default function ChatBox({ book }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const question = input.trim()
    const newMessages = [...messages, { role: 'user', content: question }]
    setMessages(newMessages)
    setInput('')
    setLoading(true)

    try {
      const res = await api.post('/chat/ask', {
        book_id: book.id,
        question,
        history: messages,
      })
      setMessages([...newMessages, { role: 'assistant', content: res.data.answer }])
    } catch (err) {
      setMessages([...newMessages, {
        role: 'assistant',
        content: '抱歉，回答出错了，请稍后再试。'
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h3 className="text-sm font-bold text-slate-500 mb-4 uppercase tracking-wide">
        问问 AI
      </h3>

      {/* 消息列表 */}
      <div ref={scrollRef} className="max-h-96 overflow-y-auto space-y-3 mb-4 min-h-[100px]">
        {messages.length === 0 && (
          <div className="text-center text-slate-400 text-sm py-8">
            对《{book.title}》有什么疑问？尽管问吧 💬
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] px-4 py-2 rounded-2xl text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-primary-600 text-white rounded-br-sm'
                  : 'bg-slate-100 text-slate-800 rounded-bl-sm'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-100 px-4 py-2 rounded-2xl rounded-bl-sm text-sm text-slate-400">
              思考中...
            </div>
          </div>
        )}
      </div>

      {/* 输入框 */}
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder="输入你的问题..."
          className="flex-1 px-4 py-2 rounded-xl border border-slate-200 focus:outline-none focus:border-primary-400 text-sm"
          disabled={loading}
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || loading}
          className="btn-primary !px-4 !py-2 text-sm disabled:opacity-50"
        >
          发送
        </button>
      </div>
    </div>
  )
}
