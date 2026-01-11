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
          // IMPORTANT: React + TanStack must be in same chunk to prevent
          // "createContext is undefined" errors on Vercel (chunk load order issue)
          if (id.includes('node_modules')) {
            // React core + ecosystem + TanStack Query + Icons (must load together)
            // Icons use React.forwardRef, so they MUST be in same chunk as React
            // to prevent "Cannot read properties of undefined (reading 'forwardRef')" on Vercel
            if (id.includes('react-dom') || id.includes('react-router') || 
                id.includes('/react/') || id.includes('@tanstack') ||
                id.includes('lucide-react')) {
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
            // Forms
            if (id.includes('react-hook-form') || id.includes('@hookform') || id.includes('/zod/')) {
              return 'vendor-forms'
            }
            // 3D rendering
            if (id.includes('three') || id.includes('@react-three')) {
              return 'vendor-three'
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

          // App structure chunks
          if (id.includes('/src/components/')) {
            return 'app-components'
          }
          if (id.includes('/src/hooks/')) {
            return 'app-hooks'
          }
          if (id.includes('/src/store/')) {
            return 'app-store'
          }
          if (id.includes('/src/lib/')) {
            return 'app-lib'
          }

          // Granular page chunks
          const pagesPath = '/src/pages/';
          if (id.includes(pagesPath)) {
            const pageFile = id.substring(id.indexOf(pagesPath) + pagesPath.length);

            // Heavy pages (restoring original logic)
            if (id.includes('/pages/Pedigree3D') || id.includes('/pages/BreedingSimulator')) return 'pages-3d'
            if (id.includes('/pages/FieldMap') || id.includes('/pages/YieldMap')) return 'pages-maps'
            if (id.includes('/pages/DataVisualization') || id.includes('/pages/AnalyticsDashboard')) return 'pages-analytics'

            // Sub-directories
            if (pageFile.startsWith('commercial/')) return 'pages-commercial';
            if (pageFile.startsWith('prototypes/')) return 'pages-prototypes';
            if (pageFile.startsWith('workspaces/')) return 'pages-workspaces';

            // Group by prefix / functionality
            if (pageFile.startsWith('Germplasm')) return 'pages-germplasm';
            if (pageFile.startsWith('Trial') || pageFile.startsWith('Study')) return 'pages-studies';
            if (pageFile.startsWith('Location')) return 'pages-locations';
            if (pageFile.startsWith('Cross') || pageFile.startsWith('Breeding') || pageFile.startsWith('Pedigree')) return 'pages-breeding';
            if (pageFile.startsWith('Vision')) return 'pages-vision';
            if (pageFile.startsWith('Seed') || pageFile.startsWith('Inventory')) return 'pages-seed';
            if (pageFile.startsWith('Trait')) return 'pages-traits';
            if (pageFile.startsWith('Program')) return 'pages-programs';
            if (pageFile.startsWith('People') || pageFile.startsWith('Person')) return 'pages-people';
            if (pageFile.startsWith('Wasm')) return 'pages-wasm';
            if (pageFile.startsWith('Genetic') || pageFile.startsWith('Genome') || pageFile.startsWith('Allele') || pageFile.startsWith('Marker')) return 'pages-genetics';
            if (pageFile.startsWith('Phenotype') || pageFile.startsWith('Disease') || pageFile.startsWith('Abiotic')) return 'pages-phenotype';
            if (pageFile.startsWith('Field') || pageFile.startsWith('Nursery') || pageFile.startsWith('Plot')) return 'pages-field';
            if (pageFile.startsWith('Sample') || pageFile.startsWith('Barcode') || pageFile.startsWith('Label')) return 'pages-inventory';
            if (pageFile.startsWith('Admin') || pageFile.startsWith('User') || pageFile.startsWith('System')) return 'pages-admin';
            if (pageFile.startsWith('Data') || pageFile.startsWith('Observation') || pageFile.startsWith('Report')) return 'pages-data';

            // Fallback for other pages
            return 'pages-other';
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
