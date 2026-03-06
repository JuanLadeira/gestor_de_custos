import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://app:8000',
        changeOrigin: true,
      },
      '/auth': {
        target: 'http://app:8000',
        changeOrigin: true,
      },
      '/admin': {
        target: 'http://app:8000',
        changeOrigin: true,
      },
      '/stripe': {
        target: 'http://app:8000',
        changeOrigin: true,
      },
      '/checkout': {
        target: 'http://app:8000',
        changeOrigin: true,
      },
    },
  },
})
