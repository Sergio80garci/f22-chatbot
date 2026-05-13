import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// En produccion (GitHub Pages) el sitio se sirve bajo /f22-chatbot/.
// En dev local usamos / para que las rutas no requieran prefijo.
// El workflow de GH Actions exporta VITE_BASE=/f22-chatbot/ en build.
export default defineConfig(({ command }) => ({
  base: command === 'build' ? (process.env.VITE_BASE || '/f22-chatbot/') : '/',
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
}))
