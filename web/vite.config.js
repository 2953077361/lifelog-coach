import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 从仓库根目录执行 npm run build / npm run dev，因此这里把 root 显式指向 web/，
// 否则 Vite 会以当前工作目录（仓库根）作为 root 去找 index.html。
const root = fileURLToPath(new URL('.', import.meta.url))

export default defineConfig({
  root,
  plugins: [vue()],
  server: {
    // 显式绑定 127.0.0.1：默认 localhost 在部分机器上只监听 IPv6(::1)，会导致 127.0.0.1 拒绝连接。
    host: '127.0.0.1',
    port: 5173,
    // 开发态把 /api 反向代理到 FastAPI（8777）；生产态由 FastAPI 直接托管 dist。
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8777',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true
  }
})
