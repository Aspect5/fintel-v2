/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./frontend/index.html",
    "./frontend/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand': {
          'primary': '#58A6FF',
          'secondary': '#7C3AED',
          'accent': '#F59E0B',
          'success': '#10B981',
          'warning': '#F59E0B',
          'danger': '#EF4444',
          'bg': '#0D1117',
          'bg-secondary': '#161B22',
          'surface': '#21262D',
          'border': '#30363D',
          'text': {
            'primary': '#F0F6FC',
            'secondary': '#C9D1D9',
            'tertiary': '#8B949E',
          }
        }
      }
    },
  },
  plugins: [],
}