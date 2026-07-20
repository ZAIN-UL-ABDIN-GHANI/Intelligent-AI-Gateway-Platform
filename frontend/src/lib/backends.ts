export const BACKEND_META: Record<string, { label: string; color: string; dot: string }> = {
  "gemma-local": { label: "GEMMA · LOCAL", color: "text-gemma", dot: "bg-gemma" },
  claude: { label: "CLAUDE", color: "text-claude", dot: "bg-claude" },
  gpt: { label: "GPT", color: "text-gpt", dot: "bg-gpt" },
  gemini: { label: "GEMINI", color: "text-gemini", dot: "bg-gemini" },
};

export function backendMeta(name: string) {
  return BACKEND_META[name] || { label: name.toUpperCase(), color: "text-muted", dot: "bg-muted" };
}
