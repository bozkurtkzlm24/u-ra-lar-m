export interface Question {
  id: string;
  text: string;
  hint?: string;
}

export interface EntryAnswer {
  qid: string;
  text: string;
}

export interface DayEntry {
  dateISO: string;
  mood: number;
  answers: EntryAnswer[];
  tags: string[];
}

/**
 * Generates a short, human-readable summary of a reflection entry that can be copied
 * to the clipboard.  The helper keeps the format stable for downstream tooling
 * and trims overly long answers so that the clipboard payload stays compact.
 */
export function formatSummaryForClipboard(entry: DayEntry, questions: Question[]): string {
  const safeQuestions = Array.isArray(questions) ? questions : [];
  const answersById = new Map(entry.answers?.map((answer) => [answer.qid, answer.text]) ?? []);

  const lines = [
    `Tarih: ${entry.dateISO ?? ""}`,
    `Ruh hâli: ${typeof entry.mood === "number" ? entry.mood : ""}`,
    `Etiketler: ${(entry.tags && entry.tags.length ? entry.tags.join(", ") : "-")}`,
    "Cevaplar:",
    ...safeQuestions.map((question) => {
      const rawText = answersById.get(question.id) ?? "";
      const snippet = rawText.slice(0, 200);
      return `• ${question.text}: ${snippet}`;
    }),
  ];

  return lines.join("\n");
}
