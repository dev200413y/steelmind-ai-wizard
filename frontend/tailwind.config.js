/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        steel: {
          900: '#0F172A',
          800: '#1E293B',
          700: '#334155',
          600: '#475569',
          500: '#64748B',
        },
        accent: {
          500: '#00D1FF',
          600: '#00A3FF',
        },
        danger: {
          500: '#FF3B30',
          600: '#D70015',
        },
        warning: {
          500: '#FF9F0A',
        },
        success: {
          500: '#34C759',
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'hero-pattern': "url('/noise.png')",
      }
    },
  },
  plugins: [],
}
