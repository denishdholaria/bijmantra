import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'robots.txt', 'icons/*.png'],
      manifest: {
        name: 'Bijmantra - Plant Breeding App',
        short_name: 'Bijmantra',
        description: 'BrAPI v2.1 compliant Plant Breeding Application',
        theme_color: '#10b981',
        background_color: '#ffffff',
        display: 'standalone',
        orientation: 'portrait',
        scope: '/',
        start_url: '/',
        icons: [
          {
            src: '/icons/icon-72x72.png',
            sizes: '72x72',
            type: 'image/png',
          },
          {
            src: '/icons/icon-96x96.png',
            sizes: '96x96',
            type: 'image/png',
          },
          {
            src: '/icons/icon-128x128.png',
            sizes: '128x128',
            type: 'image/png',
          },
          {
            src: '/icons/icon-144x144.png',
            sizes: '144x144',
            type: 'image/png',
          },
          {
            src: '/icons/icon-152x152.png',
            sizes: '152x152',
            type: 'image/png',
          },
          {
            src: '/icons/icon-192x192.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: '/icons/icon-384x384.png',
            sizes: '384x384',
            type: 'image/png',
          },
          {
            src: '/icons/icon-512x512.png',
            sizes: '512x512',
            type: 'image/png',
          },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2,wasm}'],
        maximumFileSizeToCacheInBytes: 5 * 1024 * 1024, // 5MB for WASM files
        runtimeCaching: [
          // API calls - Network First with fallback
          {
            urlPattern: /^https?:\/\/.*\/api\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 200,
                maxAgeSeconds: 60 * 60 * 24, // 24 hours
              },
              cacheableResponse: {
                statuses: [0, 200],
              },
              networkTimeoutSeconds: 10,
            },
          },
          // BrAPI endpoints - Network First
          {
            urlPattern: /^https?:\/\/.*\/brapi\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'brapi-cache',
              expiration: {
                maxEntries: 500,
                maxAgeSeconds: 60 * 60 * 24, // 24 hours
              },
              cacheableResponse: {
                statuses: [0, 200],
              },
              networkTimeoutSeconds: 10,
            },
          },
          // Seed Bank specific endpoints - Stale While Revalidate for faster offline access
          {
            urlPattern: /^https?:\/\/.*\/(accessions|vaults|viability|regeneration|exchange).*/i,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'seed-bank-cache',
              expiration: {
                maxEntries: 1000,
                maxAgeSeconds: 60 * 60 * 24 * 7, // 7 days
              },
              cacheableResponse: {
                statuses: [0, 200],
              },
            },
          },
          // Static assets - Cache First
          {
            urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp)$/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'images-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 * 24 * 30, // 30 days
              },
            },
          },
          // Fonts - Cache First
          {
            urlPattern: /\.(?:woff|woff2|ttf|otf|eot)$/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'fonts-cache',
              expiration: {
                maxEntries: 20,
                maxAgeSeconds: 60 * 60 * 24 * 365, // 1 year
              },
            },
          },
        ],
      },
      devOptions: {
        enabled: false, // Enable for testing SW in dev
      },
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          // Vendor chunks - split large dependencies
          if (id.includes('node_modules')) {
            // React core
            if (id.includes('react-dom') || id.includes('react-router') || id.includes('/react/')) {
              return 'vendor-react'
            }
            // UI components (Radix)
            if (id.includes('@radix-ui')) {
              return 'vendor-ui'
            }
            // Charts - ECharts (heavy)
            if (id.includes('echarts')) {
              return 'vendor-echarts'
            }
            // Charts - Recharts
            if (id.includes('recharts')) {
              return 'vendor-recharts'
            }
            // Data fetching
            if (id.includes('@tanstack')) {
              return 'vendor-query'
            }
            // Forms
            if (id.includes('react-hook-form') || id.includes('@hookform') || id.includes('/zod/')) {
              return 'vendor-forms'
            }
            // 3D rendering
            if (id.includes('three') || id.includes('@react-three')) {
              return 'vendor-three'
            }
            // Icons - keep separate for tree-shaking visibility
            if (id.includes('lucide-react')) {
              return 'vendor-icons'
            }
            // Maps
            if (id.includes('leaflet') || id.includes('react-leaflet')) {
              return 'vendor-maps'
            }
            // Markdown
            if (id.includes('react-markdown') || id.includes('remark')) {
              return 'vendor-markdown'
            }
            // Offline/sync
            if (id.includes('dexie') || id.includes('yjs') || id.includes('y-indexeddb')) {
              return 'vendor-offline'
            }
            // Utils
            if (id.includes('date-fns') || id.includes('clsx') || id.includes('tailwind-merge')) {
              return 'vendor-utils'
            }
          }
          
          // Division-based code splitting - pages load with their division
          if (id.includes('/divisions/seed-bank/')) {
            return 'div-seed-bank'
          }
          if (id.includes('/divisions/seed-operations/')) {
            return 'div-seed-ops'
          }
          if (id.includes('/divisions/earth-systems/')) {
            return 'div-earth'
          }
          if (id.includes('/divisions/commercial/')) {
            return 'div-commercial'
          }
          if (id.includes('/divisions/plant-sciences/')) {
            return 'div-plant-sciences'
          }
          if (id.includes('/divisions/knowledge/')) {
            return 'div-knowledge'
          }
          if (id.includes('/divisions/sensor-networks/')) {
            return 'div-sensors'
          }
          if (id.includes('/divisions/sun-earth-systems/')) {
            return 'div-sun-earth'
          }
          if (id.includes('/divisions/space-research/')) {
            return 'div-space'
          }
          if (id.includes('/divisions/integrations/')) {
            return 'div-integrations'
          }
          
          // Heavy pages that should be separate chunks
          if (id.includes('/pages/Pedigree3D') || id.includes('/pages/BreedingSimulator')) {
            return 'pages-3d'
          }
          if (id.includes('/pages/FieldMap') || id.includes('/pages/YieldMap')) {
            return 'pages-maps'
          }
          if (id.includes('/pages/DataVisualization') || id.includes('/pages/AnalyticsDashboard')) {
            return 'pages-analytics'
          }
          if (id.includes('/pages/Wasm')) {
            return 'pages-wasm'
          }
        },
      },
    },
    chunkSizeWarningLimit: 1500, // Increase limit for large PWA
    sourcemap: false, // Disable sourcemaps in production for smaller builds
  },
  server: {
    port: 5173,
    proxy: {
      '/brapi': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
