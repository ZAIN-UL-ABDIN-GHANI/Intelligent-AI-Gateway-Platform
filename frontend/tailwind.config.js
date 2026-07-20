/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: "#0B0E14",
        surface: "#131720",
        surface2: "#1B2029",
        border: "#232938",
        ink: "#E4E7EB",
        muted: "#7C8699",
        gemma: "#2DD4BF",
        claude: "#FB7A5D",
        gpt: "#6366F1",
        gemini: "#F5A623",
        good: "#34D399",
        bad: "#F87171",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
