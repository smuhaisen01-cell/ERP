import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  base: '/static/spa/',
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/app/health': 'http://localhost:8000',
    }
  }
})