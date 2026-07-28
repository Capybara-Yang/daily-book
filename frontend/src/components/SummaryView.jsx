import { useState } from 'react'

export default function SummaryView({ book }) {
  const isStory = book.story_summary && book.story_summary.length > 0

  return (
    <div className="space-y-6">
      {/* 一句话核心 */}
      <div className="card bg-gradient-to-br from-primary-50 to-white">
        <div className="text-xs text-primary-600 font-medium mb-2">
          {isStory ? "本书精髓" : "一句话核心"}
        </div>
        <p className="text-lg text-slate-800 leading-relaxed font-medium">
          {book.one_liner}
        </p>
      </div>

      {/* 故事概要（小说类） */}
      {isStory && (
        <div className="card bg-blue-50 border-blue-100">
          <h3 className="text-sm font-bold text-blue-700 mb-3 uppercase tracking-wide">
            故事概要
          </h3>
          <p className="text-sm text-slate-700 leading-relaxed">
            {book.story_summary}
          </p>
        </div>
      )}

      {/* 核心概念 / 核心主题（可折叠） */}
      {book.concepts && book.concepts.length > 0 && (
        <div className="card">
          <h3 className="text-sm font-bold text-slate-500 mb-4 uppercase tracking-wide">
            {isStory ? "三大核心主题" : "三大核心概念"}
          </h3>
          <div className="space-y-2">
            {book.concepts.map((concept, i) => (
              <ConceptItem key={i} index={i} concept={concept} />
            ))}
          </div>
          <p className="text-xs text-slate-400 mt-3 text-center">
            💡 点击标题展开详细解释
          </p>
        </div>
      )}

      {/* 金句 */}
      {book.quotes && book.quotes.length > 0 && (
        <div className="card bg-amber-50 border-amber-100">
          <h3 className="text-sm font-bold text-amber-700 mb-4 uppercase tracking-wide">
            金句
          </h3>
          <div className="space-y-3">
            {book.quotes.map((quote, i) => (
              <blockquote
                key={i}
                className="border-l-4 border-amber-400 pl-4 text-slate-700 italic leading-relaxed"
              >
                {quote}
              </blockquote>
            ))}
          </div>
        </div>
      )}

      {/* 章节概要 + 精彩标注 */}
      {book.chapters && book.chapters.length > 0 && (
        <div className="card">
          <h3 className="text-sm font-bold text-slate-500 mb-4 uppercase tracking-wide">
            精华章节
          </h3>
          <div className="space-y-2">
            {book.chapters.map((chapter, i) => (
              <ChapterItem key={i} index={i} chapter={chapter} />
            ))}
          </div>
          <p className="text-xs text-slate-400 mt-3 text-center">
            💡 点击章节查看概要，点击"原文摘录"读精彩片段
          </p>
        </div>
      )}
    </div>
  )
}

// 可折叠的章节项
function ChapterItem({ index, chapter }) {
  const [expanded, setExpanded] = useState(false)
  const [showExcerpt, setShowExcerpt] = useState(false)

  return (
    <div className="border border-slate-100 rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 p-3 text-left hover:bg-slate-50 transition-colors"
      >
        <span className="flex-shrink-0 w-7 h-7 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center text-sm font-bold">
          {index + 1}
        </span>
        <span className="flex-1 font-bold text-slate-800 text-sm">
          {chapter.title}
        </span>
        <span className={`flex-shrink-0 text-slate-400 transition-transform ${expanded ? 'rotate-180' : ''}`}>
          ▼
        </span>
      </button>
      {expanded && (
        <div className="px-3 pb-3 pt-1">
          <div className="pl-10 pr-2 space-y-2">
            <p className="text-sm text-slate-600 leading-relaxed">
              {chapter.summary}
            </p>
            {chapter.highlight && (
              <div className="bg-emerald-50 rounded-lg p-3 mt-2">
                <span className="text-xs text-emerald-600 font-bold">✨ 最精彩的部分</span>
                <p className="text-sm text-slate-700 leading-relaxed mt-1">
                  {chapter.highlight}
                </p>
                {chapter.excerpt && (
                  <button
                    onClick={() => setShowExcerpt(!showExcerpt)}
                    className="mt-2 text-xs text-emerald-600 font-medium hover:text-emerald-700 transition-colors flex items-center gap-1"
                  >
                    {showExcerpt ? '收起原文' : '📖 点击查看原文摘录'}
                    <span className={`transition-transform ${showExcerpt ? 'rotate-180' : ''}`}>▼</span>
                  </button>
                )}
                {showExcerpt && chapter.excerpt && (
                  <div className="mt-2 bg-white/70 rounded-lg p-3 border-l-3 border-emerald-300">
                    <p className="text-sm text-slate-600 leading-loose italic">
                      {chapter.excerpt}
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// 可折叠的概念项
function ConceptItem({ index, concept }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="border border-slate-100 rounded-xl overflow-hidden">
      {/* 标题行（可点击） */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 p-3 text-left hover:bg-slate-50 transition-colors"
      >
        <span className="flex-shrink-0 w-7 h-7 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center text-sm font-bold">
          {index + 1}
        </span>
        <span className="flex-1 font-bold text-slate-800 text-sm">
          {concept.title}
        </span>
        <span className={`flex-shrink-0 text-slate-400 transition-transform ${expanded ? 'rotate-180' : ''}`}>
          ▼
        </span>
      </button>
      {/* 解释（展开时显示） */}
      {expanded && (
        <div className="px-3 pb-3 pt-1">
          <div className="pl-10 pr-2">
            <p className="text-sm text-slate-600 leading-relaxed">
              {concept.explanation}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
