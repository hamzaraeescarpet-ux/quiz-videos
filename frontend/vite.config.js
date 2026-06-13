import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api/hf': {
        target: 'https://hamzaraeescarpet-quiz-viral-api.hf.space',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/hf/, '/api'),
      }
    }
  }
})
