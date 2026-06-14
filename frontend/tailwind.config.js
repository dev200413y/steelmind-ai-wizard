import tailwindScrollbar from 'tailwind-scrollbar';

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0B0F19',
        surface: 'rgba(20, 25, 40, 0.6)',
        surface_hover: 'rgba(30, 40, 60, 0.8)',
        border_subtle: 'rgba(255, 255, 255, 0.1)',
        steel: {
          900: '#0F172A',
          800: '#1E293B',
          700: '#334155',
          600: '#475569',
          500: '#64748B',
        },
        accent: {
          500: '#00F0FF', // Neon Cyan
          600: '#00B8D4',
        },
        heat: {
          500: '#FF5E00', // Neon Orange/Heat
          600: '#E65100',
        },
        danger: {
          500: '#FF3366', // Neon Pink-Red
          600: '#D50000',
        },
        warning: {
          500: '#FFD600',
        },
        success: {
          500: '#00E676',
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'glass-gradient': 'linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.01) 100%)',
      },
      keyframes: {
        pulseGlow: {
          '0%, 100%': { opacity: 1, boxShadow: '0 0 15px 0px rgba(0, 240, 255, 0.5)' },
          '50%': { opacity: 0.7, boxShadow: '0 0 30px 5px rgba(0, 240, 255, 0.8)' },
        },
        fadeInUp: {
          '0%': { opacity: 0, transform: 'translateY(10px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        }
      },
      animation: {
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'fade-in-up': 'fadeInUp 0.3s ease-out forwards',
      }
    },
  },
  plugins: [
    tailwindScrollbar,
  ],
}
