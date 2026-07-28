export default function BookCard({ book, onClick }) {
  return (
    <div
      onClick={onClick}
      className="card cursor-pointer hover:shadow-md transition-shadow"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-bold text-slate-800 mb-1">
            《{book.title}》
          </h3>
          <p className="text-sm text-slate-500">{book.author}</p>
        </div>
        {book.category && (
          <span className="tag bg-primary-50 text-primary-600">
            {book.category}
          </span>
        )}
      </div>
      <p className="text-slate-600 text-sm leading-relaxed">
        {book.one_liner}
      </p>
    </div>
  )
}
