import { useState, useCallback, useRef } from "react";

interface SpeechRecognitionHook {
  isListening: boolean;
  transcript: string;
  error: string | null;
  startListening: () => void;
  stopListening: () => void;
  supported: boolean;
}

export function useSpeechRecognition(): SpeechRecognitionHook {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);

  const SpeechRecognitionAPI =
    typeof window !== "undefined"
      ? (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
      : null;

  const supported = !!SpeechRecognitionAPI;

  const startListening = useCallback(() => {
    if (!SpeechRecognitionAPI) {
      setError("Speech recognition not supported in this browser.");
      return;
    }

    const recognition = new SpeechRecognitionAPI();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      const result = event.results[0][0].transcript;
      setTranscript(result);
      setIsListening(false);
    };

    recognition.onerror = (event: any) => {
      setError(`Speech error: ${event.error}`);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;
    setError(null);
    setTranscript("");
    setIsListening(true);
    recognition.start();
  }, [SpeechRecognitionAPI]);

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop();
    setIsListening(false);
  }, []);

  return { isListening, transcript, error, startListening, stopListening, supported };
}
