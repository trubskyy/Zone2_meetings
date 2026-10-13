import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    // Allow access through a tunnel (Telegram requires HTTPS for Mini Apps).
    host: true,
    allowedHosts: true,
    proxy: {
      '/api': { target: 'http://localhost:8000', ws: true },
    },
  },
})
