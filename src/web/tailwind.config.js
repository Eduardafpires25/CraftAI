/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f4f0ff",
          100: "#ebe4ff",
          200: "#d4c5ff",
          300: "#b89dff",
          400: "#9a73ff",
          500: "#7c5cfa",
          600: "#6b3fef",
          700: "#5a2ed4",
          800: "#4823a8",
          900: "#311a78",
        },
        ink: {
          // Backgrounds para dark theme (do design)
          950: "#0a0617",
          900: "#0e0a1f",
          800: "#15102b",
          700: "#1c1638",
          600: "#252046",
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      backgroundImage: {
        'glow-radial':
          'radial-gradient(circle at 30% 30%, rgba(124,92,250,0.18), transparent 60%)',
      },
      boxShadow: {
        glow: '0 0 60px -10px rgba(124, 92, 250, 0.45)',
      },
    },
  },
  plugins: [],
};
