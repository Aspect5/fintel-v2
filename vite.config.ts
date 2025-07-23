// frontend/vite.config.ts

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  
  // (FIX) Add this entire 'server' block
  server: {
    // This is the port your frontend runs on
    port: 5173, 
    proxy: {
      // This says: "any request that starts with /api..."
      '/api': {
        // "...should be sent to the backend server."
        target: 'http://localhost:5001',
        
        // This is crucial for the proxy to work correctly
        changeOrigin: true, 
        
        // (Optional but good practice) Remove '/api' from the start of the path 
        // when it's sent to the backend, if your Flask routes don't include it.
        // In your case, they DO, so we can comment this out or remove it.
        // rewrite: (path) => path.replace(/^\/api/, '') 
      }
    }
  }
})