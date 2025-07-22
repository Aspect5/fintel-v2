import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // This is the proxy configuration
    proxy: {
      // Any request starting with /api will be forwarded
      '/api': {
        // Target the Flask backend server
        target: 'http://127.0.0.1:5001',
        // Needed for the backend to correctly process the request
        changeOrigin: true,
      },
    },
  },
});