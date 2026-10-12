export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
        handwriting: ['"Caveat"', '"Kalam"', 'cursive'],
        kalam: ['"Kalam"', 'cursive'],
        mono: ['"JetBrains Mono"', 'monospace']
      },
      colors: {
        ink: "#0f172a",
        "ink-blue": "#1e3a8a",
        "ink-muted": "#475569",
        ocean: "#1d5f78",
        mint: "#0f766e",
        coral: "#dc2626",
        paper: "#fdfbf7",
        "paper-warm": "#fcf8ef",
        "paper-ruled": "#e2edf8",
        "paper-margin": "#fca5a5",
        "sticky-yellow": "#fef08a",
        "sticky-green": "#bbf7d0",
        "sticky-cyan": "#bae6fd",
        "sticky-pink": "#fbcfe8",
        "cover-kraft": "#d5b895",
        "cover-navy": "#0f172a",
      },
      boxShadow: {
        'book-3d': '0 20px 40px -15px rgba(15, 23, 42, 0.3), 0 2px 4px rgba(0,0,0,0.08), -8px 0 16px -6px rgba(0,0,0,0.15)',
        'page-float': '0 15px 30px -8px rgba(30, 41, 59, 0.15), 0 0 0 1px rgba(0,0,0,0.05)',
        'sticky': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1), 2px 2px 8px rgba(0,0,0,0.06)',
        'btn-3d': '0 4px 0 #0f4457, 0 6px 12px rgba(0,0,0,0.15)',
        'btn-3d-active': '0 1px 0 #0f4457, 0 2px 4px rgba(0,0,0,0.1)',
        'btn-secondary-3d': '0 3px 0 #cbd5e1, 0 4px 8px rgba(0,0,0,0.08)',
      }
    }
  },
  plugins: []
};
