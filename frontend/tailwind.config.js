/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,ts}"],
  theme: {
    extend: {
      colors: {
        terminal: {
          900: "#0f172a",
          800: "#1a1b26",
          700: "#1f2937"
        },
        neon: {
          400: "#4ade80",
          500: "#22c55e"
        },
        violet: {
          500: "#7c3aed",
          600: "#6d28d9",
          700: "#5b21b6"
        }
      }
    }
  },
  plugins: []
};
