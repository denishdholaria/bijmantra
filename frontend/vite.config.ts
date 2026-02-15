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
        // Manual chunking to split the 1.5MB index vendor bundle into smaller pieces.
        // Each group depends ONLY on react/react-dom — no circular deps between groups.
        //
        // Previous attempt broke Vercel with "Cannot access X before initialization" because
        // it split react itself across chunks. This version keeps react+react-dom together
        // as the base layer and only splits independent vendor trees.
        manualChunks(id) {
          if (!id.includes('node_modules')) return;

          // Base layer: react-dom + scheduler (must stay together, depends on react)
          if (id.includes('/react-dom/') || id.includes('/scheduler/')) {
            return 'vendor-react';
          }
          // react core stays in the default index chunk (shared by everything)

          // Routing layer
          if (id.includes('/react-router') || id.includes('/@remix-run/router')) {
            return 'vendor-router';
          }

          // Data layer: TanStack Query + Table + Virtual
          if (id.includes('/@tanstack/')) {
            return 'vendor-query';
          }

          // UI motion: framer-motion
          if (id.includes('/framer-motion/') || id.includes('/motion-dom/') || id.includes('/motion-utils/')) {
            return 'vendor-motion';
          }

          // Toast: sonner
          if (id.includes('/sonner/')) {
            return 'vendor-sonner';
          }

          // Radix UI primitives (used by all shadcn components) + floating-ui (radix dependency)
          if (id.includes('/@radix-ui/') || id.includes('/@floating-ui/')) {
            return 'vendor-radix';
          }

          // Real-time: socket.io-client + engine.io
          if (id.includes('/socket.io-client/') || id.includes('/@socket.io/') || id.includes('/socket.io-parser/') || id.includes('/engine.io-client/') || id.includes('/engine.io-parser/')) {
            return 'vendor-socket';
          }

          // Date utilities
          if (id.includes('/date-fns/')) {
            return 'vendor-date';
          }

          // Form handling
          if (id.includes('/react-hook-form/') || id.includes('/@hookform/')) {
            return 'vendor-form';
          }

          // Drawer component (vaul)
          if (id.includes('/vaul/')) {
            return 'vendor-radix'; // Bundle with radix since it's a UI primitive
          }

          // Search: Meilisearch client
          if (id.includes('/meilisearch/')) {
            return 'vendor-search';
          }

          // Schema validation: Zod
          if (id.includes('/zod/')) {
            return 'vendor-zod';
          }

          // Command palette: cmdk
          if (id.includes('/cmdk/')) {
            return 'vendor-radix'; // Bundles with radix (UI primitive)
          }
        },
      },
    },
    chunkSizeWarningLimit: 1100, // Largest chunk is index at ~1058KB (app framework shell + 350 routes)
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
