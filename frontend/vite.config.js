import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { resolve } from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    port: 5173,
    host: true,
    // Proxy solo si no hay VITE_API_URL configurado (desarrollo local)
    // Si VITE_API_URL está configurado, axios usará esa URL directamente
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
})
