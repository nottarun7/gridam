import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev: proxy /api/* to the FastAPI backend (nginx does this in prod).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true, rewrite: (p) => p.replace(/^\/api/, '') },
    },
  },
})
