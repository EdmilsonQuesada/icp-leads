import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    watch: {
      // Necessário para hot-reload funcionar com volumes Docker no Windows
      usePolling: true,
      interval: 1000,
    },
  },
})
