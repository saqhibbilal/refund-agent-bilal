import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./features/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        worknoon: {
          dark: "#1C1C1C",
          ice: "#D6EFFF",
          panel: "rgba(214, 239, 255, 0.065)",
          panelStrong: "rgba(214, 239, 255, 0.12)",
          border: "rgba(214, 239, 255, 0.18)",
          muted: "rgba(214, 239, 255, 0.6)",
        },
        volt: {
          500: "#D6EFFF",
          600: "#D6EFFF",
        },
      },
      fontFamily: {
        sans: ["var(--font-roboto-condensed)", "system-ui", "sans-serif"],
        display: ["var(--font-oswald)", "system-ui", "sans-serif"],
        mono: ["ui-monospace", "monospace"],
      },
      fontSize: {
        chat: ["0.9375rem", { lineHeight: "1.6" }],
      },
    },
  },
  plugins: [],
};

export default config;
