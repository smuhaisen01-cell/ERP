/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        arabic: ['Noto Sans Arabic', 'Tajawal', 'sans-serif'],
        latin: ['IBM Plex Sans', 'sans-serif'],
        mono: ['IBM Plex Mono', 'monospace'],
      },
      colors: {
        brand: {
          50:  '#f0f7ff',
          100: '#e0effe',
          200: '#bae0fd',
          300: '#7dc8fb',
          400: '#38aaf6',
          500: '#0e8de3',
          600: '#026fc2',
          700: '#03589d',
          800: '#074a82',
          900: '#0c3e6c',
          950: '#082849',
        },
        sand: {
          50:  '#fdf8f0',
          100: '#faefd9',
          200: '#f4ddb2',
          300: '#ecc581',
          400: '#e2a54e',
          500: '#d98c2c',
          600: '#c07320',
          700: '#9f591d',
          800: '#82481e',
          900: '#6b3c1b',
        },
        surface: {
          0:   '#ffffff',
          50:  '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          800: '#1e293b',
          900: '#0f172a',
          950: '#020617',
        }
      },
      borderRadius: {
        '4xl': '2rem',
      },
      boxShadow: {
        'card': '0 1px 3px 0 rgb(0 0 0 / 0.04), 0 4px 16px -2px rgb(0 0 0 / 0.06)',
        'card-hover': '0 4px 6px -1px rgb(0 0 0 / 0.06), 0 8px 32px -4px rgb(0 0 0 / 0.10)',
        'glass': 'inset 0 1px 0 0 rgb(255 255 255 / 0.1)',
      },
    },
  },
  plugins: [],
}
