/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,ts}"],
  theme: {
    extend: {
      // GLUD · Sistema visual institucional
      // Inspirado en USWDS y GOV.UK · cálido, sobrio, datos primero
      colors: {
        // Superficies
        cream: "#fafaf7",        // bg principal · más cálido que blanco puro
        "cream-2": "#f3f1ea",    // bg-alt · sidebars, filas alternas
        "cream-3": "#f8f4e9",    // crema clara · acentos cálidos
        card: "#ffffff",         // tarjetas, formularios

        // Tinta
        ink: "#14202c",          // texto principal (casi negro con sesgo azul)
        "ink-2": "#2c3e52",      // texto secundario
        muted: "#6b7785",        // etiquetas, ayudas

        // Líneas
        line: "#e7e3d8",
        "line-strong": "#c8c2b0",

        // Marca · Navy de gobierno
        navy: {
          DEFAULT: "#1a3a5c",
          light: "#2c5582",
          ui: "#7a9ec2",
          deep: "#0f2438",
        },

        // Acento · Dorado cálido (solo como acento, no fondo extenso)
        gold: {
          DEFAULT: "#c9a961",
          deep: "#b08e3f",       // dorado intenso
        },

        // Estados
        ok: "#4d7a3e",
        warn: "#b08e3f",
        err: "#a14545",

        // Modo oscuro (visualizaciones / casos donde aplica)
        "dark-bg": "#0f1620",
        "dark-card": "#161f2c",
        "dark-line": "#1d2a3a",
        "dark-ink": "#e8e4dc",
        "dark-muted": "#8a93a0",
      },
      fontFamily: {
        // Editorial · titulares con voz institucional
        serif: ['"Source Serif 4"', 'Georgia', 'Cambria', '"Times New Roman"', 'serif'],
        // UI · sans humanista (USWDS)
        sans: ['"Public Sans"', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        // Cifras tabulares
        mono: ['ui-monospace', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
      letterSpacing: {
        editorial: '-0.012em',
      },
    },
  },
  plugins: []
};
