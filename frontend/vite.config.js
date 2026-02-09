import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Base path for GitHub Pages - change 'rag_lex_project' to your repo name
  base: '/rag_lex_project/',
  build: {
    outDir: 'dist',
    // Generate static files for GitHub Pages
    assetsDir: 'assets',
  },
})
