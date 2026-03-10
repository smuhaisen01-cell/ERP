import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') }
  },
  build: {
    outDir: '../deploy_package/static/spa',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/app/health': 'http://localhost:8000',
    }
  }
})
