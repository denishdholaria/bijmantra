import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),

    // VitePWA({...}),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        // DISABLED: Manual chunking causes "Cannot access X before initialization" errors
        // on Vercel due to chunk load order issues. Let Vite handle all chunking automatically.
        // 
        // Root cause: Vercel's edge network loads chunks in parallel, but our chunks have
        // interdependencies that require specific load order. Vite's default chunking
        // handles this correctly.
        //
        // Trade-off: Larger initial bundle (~8MB) but guaranteed to work.
      },
    },
    chunkSizeWarningLimit: 1500, // Increase limit for large PWA
    sourcemap: false, // Disable sourcemaps in production for smaller builds
  },
  server: {
    port: 5173,
    allowedHosts: ['0.bijmantra.org', 's108.bijmantra.org', 'localhost'],
    proxy: {
      '/brapi': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // Configure for SSE streaming endpoints
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq, req) => {
            // Disable buffering for streaming endpoints
            if (req.url?.includes('/chat/stream')) {
              proxyReq.setHeader('X-Accel-Buffering', 'no');
            }
          });
        },
      },
      // WebSocket support for Socket.IO
      '/ws': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
      },
    },
  },
})
