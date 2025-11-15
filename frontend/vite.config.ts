import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/run-google-mail': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/uber-earnings': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
