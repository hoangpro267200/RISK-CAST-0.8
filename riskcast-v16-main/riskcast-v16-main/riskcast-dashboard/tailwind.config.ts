import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "primary-neon": "#00FFC6",
        "primary-accent": "#00E0A8",
        "bg-deep": "#050B16",
        "bg-secondary": "#0A1628",
        "status-low": "#00FFC6",
        "status-medium": "#FFB020",
        "status-high": "#FF4F4F",
        "status-neutral": "#A8BACD",
        "text-high": "#E8F7FF",
        "text-medium": "#A8BACD",
        "text-low": "#7A8BA0",
      },
      boxShadow: {
        "glow-low": "0 0 12px rgba(0,255,198,0.2)",
        "glow-medium": "0 0 20px rgba(0,255,198,0.35)",
        "glow-high": "0 0 30px rgba(0,255,198,0.5)",
        "layer-1": "0 4px 20px rgba(0,0,0,0.25)",
        "layer-2": "0 8px 32px rgba(0,0,0,0.35)",
        "layer-3": "0 12px 48px rgba(0,0,0,0.45)",
      },
    },
  },
  plugins: [],
};

export default config;

