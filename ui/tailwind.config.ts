import type { Config } from 'tailwindcss'
const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: { extend: {
    colors: { jarvis: { glow: '#00d4ff', core: '#0080ff', dark: '#000a1a' } },
    keyframes: {
      pulseGlow: { '0%,100%': { boxShadow: '0 0 20px #00d4ff, 0 0 60px #0080ff44' }, '50%': { boxShadow: '0 0 40px #00d4ff, 0 0 120px #0080ff88' } },
    },
    animation: { 'pulse-glow': 'pulseGlow 2s ease-in-out infinite' },
  }},
  plugins: [],
}
export default config
