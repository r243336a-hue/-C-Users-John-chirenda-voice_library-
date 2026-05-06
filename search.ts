import { books, Book } from "./books";

function similarity(a: string, b: string): number {
  const aLow = a.toLowerCase();
  const bLow = b.toLowerCase();
  if (aLow === bLow) return 1;
  if (aLow.includes(bLow) || bLow.includes(aLow)) return 0.85;

  const trigramsA = new Set<string>();
  const trigramsB = new Set<string>();
  for (let i = 0; i <= aLow.length - 3; i++) trigramsA.add(aLow.slice(i, i + 3));
  for (let i = 0; i <= bLow.length - 3; i++) trigramsB.add(bLow.slice(i, i + 3));

  if (trigramsA.size === 0 || trigramsB.size === 0) return 0;
  let intersection = 0;
  trigramsA.forEach((t) => {
    if (trigramsB.has(t)) intersection++;
  });
  return (2 * intersection) / (trigramsA.size + trigramsB.size);
}

export function searchBooks(query: string): Book[] {
  const q = query.toLowerCase().trim();
  if (!q) return books;

  const scored = books.map((book) => {
    const titleSim = similarity(q, book.title);
    const authorSim = similarity(q, book.author);
    const tagMatch = book.tags.some((t) => t.includes(q) || q.includes(t)) ? 0.7 : 0;
    const score = Math.max(titleSim, authorSim, tagMatch);
    return { book, score };
  });

  return scored
    .filter((s) => s.score > 0.2)
    .sort((a, b) => b.score - a.score)
    .map((s) => s.book);
}

export interface Intent {
  type: "SEARCH" | "PLAY" | "PAUSE" | "RESUME" | "STOP" | "UNKNOWN";
  query?: string;
}

export function classifyIntent(text: string): Intent {
  const t = text.toLowerCase().trim();

  if (/\b(find|search|look for|show me|look up)\b/.test(t)) {
    const query = t.replace(/\b(find|search|search for|look for|show me|look up)\b/i, "").trim();
    return { type: "SEARCH", query };
  }
  if (/\b(read|play)\b/.test(t)) {
    const query = t.replace(/\b(read|play)\b/i, "").trim();
    return { type: "PLAY", query: query || undefined };
  }
  if (/\bpause\b/.test(t)) return { type: "PAUSE" };
  if (/\bresume\b/.test(t)) return { type: "RESUME" };
  if (/\bstop\b/.test(t)) return { type: "STOP" };

  return { type: "SEARCH", query: t };
}
