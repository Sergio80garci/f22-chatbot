import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Base path. En GitHub Pages el sitio se sirve bajo /f22-chatbot/.
// En dev local Vite ignora 'base' para HMR; en build lo usa para prefijar assets.
// Sobrescribible con VITE_BASE en .env si cambia el nombre del repo.
const BASE = process.env.VITE_BASE || '/f22-chatbot/'

export default defineConfig({
  base: BASE,
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8001'
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
})
