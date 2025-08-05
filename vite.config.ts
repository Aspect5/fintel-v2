import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  root: 'frontend',
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'frontend/src'),
    },
  },
  server: {
    port: parseInt(process.env.PORT || '9002'),
    host: process.env.HOST || '0.0.0.0',
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
        secure: false,
        timeout: 60000,
      }
    }
  },
  preview: {
    port: parseInt(process.env.PORT || '4173'),
    host: process.env.HOST || '0.0.0.0',
    strictPort: true,
  }
})
