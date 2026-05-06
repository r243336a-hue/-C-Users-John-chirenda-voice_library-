import { Book } from "@/lib/books";
import { BookOpen, Play } from "lucide-react";

interface BookCardProps {
  book: Book;
  onPlay: (book: Book) => void;
  isActive: boolean;
}

export function BookCard({ book, onPlay, isActive }: BookCardProps) {
  return (
    <div
      className={`
        group rounded-lg border p-5 transition-all duration-300 cursor-pointer
        ${
          isActive
            ? "border-primary bg-primary/5 shadow-md"
            : "border-border bg-card hover:border-primary/40 hover:shadow-sm"
        }
      `}
      onClick={() => onPlay(book)}
      role="button"
      tabIndex={0}
      aria-label={`Play ${book.title} by ${book.author}`}
      onKeyDown={(e) => e.key === "Enter" && onPlay(book)}
    >
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0 w-12 h-16 rounded bg-primary/10 flex items-center justify-center">
          <BookOpen className="w-6 h-6 text-primary" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-display text-lg font-semibold text-foreground truncate">{book.title}</h3>
          <p className="text-sm text-muted-foreground font-body">
            {book.author} · {book.year > 0 ? book.year : `${Math.abs(book.year)} BC`}
          </p>
          <p className="mt-2 text-sm text-foreground/70 line-clamp-2 font-body">{book.excerpt}</p>
          <div className="mt-3 flex items-center gap-2 flex-wrap">
            {book.tags.slice(0, 3).map((tag) => (
              <span
                key={tag}
                className="text-xs px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground font-body"
              >
                {tag}
              </span>
            ))}
            <span className="text-xs text-muted-foreground ml-auto font-body">
              {(book.wordCount / 1000).toFixed(0)}k words
            </span>
          </div>
        </div>
        <button
          className="flex-shrink-0 w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
          aria-label={`Play ${book.title}`}
          onClick={(e) => {
            e.stopPropagation();
            onPlay(book);
          }}
        >
          <Play className="w-4 h-4 ml-0.5" />
        </button>
      </div>
    </div>
  );
}
