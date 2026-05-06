import { Mic, MicOff } from "lucide-react";

interface VoiceButtonProps {
  isListening: boolean;
  onClick: () => void;
  supported: boolean;
}

export function VoiceButton({ isListening, onClick, supported }: VoiceButtonProps) {
  if (!supported) {
    return (
      <div className="text-center text-muted-foreground text-sm">
        Voice recognition is not supported in this browser. Try Chrome or Edge.
      </div>
    );
  }

  return (
    <button
      onClick={onClick}
      className={`
        relative w-24 h-24 rounded-full flex items-center justify-center
        transition-all duration-300 focus:outline-none focus:ring-4 focus:ring-ring/30
        ${
          isListening
            ? "bg-listening text-primary-foreground animate-pulse-glow scale-110"
            : "bg-primary text-primary-foreground hover:scale-105 hover:shadow-lg"
        }
      `}
      aria-label={isListening ? "Stop listening" : "Start voice command"}
    >
      {isListening ? <MicOff className="w-10 h-10" /> : <Mic className="w-10 h-10" />}
      {isListening && (
        <span className="absolute -bottom-8 text-sm font-body text-listening font-medium">Listening...</span>
      )}
    </button>
  );
}
