import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('react') || id.includes('react-dom') || id.includes('react-router-dom')) {
              return 'vendor-react';
            }
            if (id.includes('lucide-react')) {
              return 'vendor-icons';
            }
            if (id.includes('firebase')) {
              return 'vendor-firebase';
            }
          }
        }
      }
    },
    chunkSizeWarningLimit: 1200,
  },
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
