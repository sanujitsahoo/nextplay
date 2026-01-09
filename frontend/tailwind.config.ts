import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      animation: {
        'in': 'fadeIn 0.3s ease-in-out',
        'slide-in-from-top-2': 'slideInFromTop 0.3s ease-out',
        'shimmer': 'shimmer 2s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideInFromTop: {
          '0%': { transform: 'translateY(-8px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        shimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
      },
      colors: {
        // Pastel color palette
        pastel: {
          pink: '#FFD6E8',
          blue: '#D6E9FF',
          purple: '#E6D6FF',
          green: '#D6FFE6',
          yellow: '#FFF6D6',
          orange: '#FFE6D6',
          red: '#FFD6D6',
        },
        category: {
          urgent: '#FFB3BA', // Soft red
          likely: '#BAE1FF', // Soft blue
          challenge: '#D6BAFF', // Soft purple
        },
        // Landing page colors - teal shades
        teal: {
          500: '#14B8A6',
          600: '#0D9488',
          700: '#0F766E',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
export default config

