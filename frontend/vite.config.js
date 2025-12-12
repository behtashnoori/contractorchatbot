import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Fixed dev port to avoid conflicts per project convention
    port: 8308,
    strictPort: true,
  },
  preview: {
    // Fixed preview port
    port: 8308,
    strictPort: true,
  },
})
