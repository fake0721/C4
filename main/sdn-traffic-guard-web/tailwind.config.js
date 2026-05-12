/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // 启用深色模式
  theme: {
    extend: {
      colors: {
        primary: '#165DFF',
        success: '#52C41A',
        warning: '#FAAD14',
        danger: '#FF4D4F',
        dark: '#1D2129',
        'dark-2': '#4E5969',
        'light-1': '#F2F3F5',
        'light-2': '#E5E6EB',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'glow': 'glow 2s ease-in-out infinite alternate',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-slow': 'bounce 3s infinite',
      },
      keyframes: {
        glow: {
          '0%': { 
            boxShadow: '0 0 5px #0ff, 0 0 10px #0ff, 0 0 15px #0ff',
            filter: 'drop-shadow(0 0 5px #0ff)'
          },
          '100%': { 
            boxShadow: '0 0 10px #0ff, 0 0 20px #0ff, 0 0 30px #0ff',
            filter: 'drop-shadow(0 0 10px #0ff)'
          }
        }
      }
    },
  },
  plugins: [],
}
