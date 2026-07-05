import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  base: '/static/vue/',
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true
      },
      '/static': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: '../backend/app/static/vue',
    emptyOutDir: true
  }
})
