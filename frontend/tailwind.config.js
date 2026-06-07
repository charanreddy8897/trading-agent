/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'bg-primary':    '#0a0e17',
        'bg-secondary':  '#111827',
        'bg-tertiary':   '#1a2235',
        'border-dark':   '#1e293b',
        'accent-green':  '#10b981',
        'accent-red':    '#ef4444',
        'accent-amber':  '#f59e0b',
        'accent-cyan':   '#06b6d4',
        'accent-blue':   '#3b82f6',
        'accent-violet': '#8b5cf6',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'monospace'],
        sans: ['DM Sans', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
