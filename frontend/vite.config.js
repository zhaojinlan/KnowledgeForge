import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueJsx(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    proxy: {
      // WebSocket 代理必须放在 /api 之前，否则会被 /api 的 HTTP 代理拦截
      '/api/v1/ws': {
        target: 'ws://localhost:9000',
        ws: true,
      },
      '/api': {
        target: 'http://localhost:9000',
        changeOrigin: true,
      },
    },
  },
})
