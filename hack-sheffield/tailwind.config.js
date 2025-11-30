/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {},
        fontFamily: {
        barriecito: ["Barriecito", "cursive"],
        ephesis: ["Ephesis", "cursive"],
        kavoon: ["Kavoon", "cursive"],
        libreBodoni: ["Libre Bodoni", "serif"],
        play: ["Play", "sans-serif"],
        playfair: ["Playfair Display", "serif"],
        roboto: ["Roboto", "sans-serif"],
      }
  },
  plugins: [],
};