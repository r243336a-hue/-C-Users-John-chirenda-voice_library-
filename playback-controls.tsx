import { Play, Pause, Square, Volume2 } from "lucide-react";
import { Book } from "@/lib/books";

interface PlaybackControlsProps {
  book: Book;
  isSpeaking: boolean;
  isPaused: boolean;
  progress: number;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
}

export function PlaybackControls({
  book,
  isSpeaking,
  isPaused,
  progress,
  onPause,
  onResume,
  onStop,
}: PlaybackControlsProps) {
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-card border-t border-border p-4 shadow-lg z-50">
      <div className="max-w-3xl mx-auto">
        <div className="w-full h-1 bg-secondary rounded-full mb-3 overflow-hidden">
          <div
            className="h-full bg-primary rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>

        <div className="flex items-center gap-4">
          {isSpeaking && !isPaused && (
            <div className="flex items-end gap-0.5 h-6">
              {[1, 2, 3, 4, 5].map((i) => (
                <div
                  key={i}
                  className="w-1 bg-wave rounded-full animate-sound-wave"
                  style={{
                    height: "100%",
                    animationDelay: `${i * 0.15}s`,
                  }}
                />
              ))}
            </div>
          )}
          {(!isSpeaking || isPaused) && <Volume2 className="w-6 h-6 text-muted-foreground" />}

          <div className="flex-1 min-w-0">
            <p className="font-display text-sm font-semibold text-foreground truncate">{book.title}</p>
            <p className="text-xs text-muted-foreground font-body">{book.author}</p>
          </div>

          <div className="flex items-center gap-2">
            {isPaused ? (
              <button
                onClick={onResume}
                className="w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center hover:scale-105 transition-transform"
                aria-label="Resume"
              >
                <Play className="w-5 h-5 ml-0.5" />
              </button>
            ) : (
              <button
                onClick={onPause}
                className="w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center hover:scale-105 transition-transform"
                aria-label="Pause"
              >
                <Pause className="w-5 h-5" />
              </button>
            )}
            <button
              onClick={onStop}
              className="w-10 h-10 rounded-full bg-secondary text-secondary-foreground flex items-center justify-center hover:scale-105 transition-transform"
              aria-label="Stop"
            >
              <Square className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
