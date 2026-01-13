import react from '@vitejs/plugin-react-swc';
import { defineConfig } from 'vite';
import { visualizer } from 'rollup-plugin-visualizer';
import path from 'path';

function isPlugin(p) {
  return Boolean(p);
}

export default defineConfig(({ mode }) => {
  const analyzePlugin =
    mode === 'analyze'
      ? visualizer({
          filename: 'dist/bundle-analysis.html',
          open: false,
          gzipSize: true,
          brotliSize: true,
        })
      : null;

  return {
    plugins: [react(), analyzePlugin].filter(isPlugin),
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    css: {
      postcss: './postcss.config.js',
    },
    server: {
      port: 3000,
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
        },
        '/results/data': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
          configure: (proxy, _options) => {
            proxy.on('proxyReq', (proxyReq, req, _res) => {
              // Ensure JSON content type for API calls
              if (req.url.includes('/results/data')) {
                proxyReq.setHeader('Accept', 'application/json');
              }
            });
          },
        },
        '/results': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
        },
        '/assets': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
        },
      },
    },
    build: {
      reportCompressedSize: true,
      sourcemap: true, // Enable sourcemap for debugging
      minify: false, // Disable minify to avoid terser dependency
      commonjsOptions: {
        include: [/node_modules/],
        transformMixedEsModules: true,
      },
      rollupOptions: {
        output: {
          manualChunks: (id) => {
            // Vendor chunks (Phase 5 - Performance optimization)
            if (id.includes('node_modules')) {
              // React core - MUST be in same chunk to avoid multiple React instances
              if (id.includes('react') || id.includes('react-dom') || id.includes('react-is')) {
                return 'vendor-react';
              }
              // Motion/Animation - Bundle with React to avoid multiple React instances
              // This prevents "Cannot set properties of undefined (setting 'Children')" error
              if (id.includes('motion') || id.includes('framer') || id.includes('with-selector')) {
                return 'vendor-react'; // Bundle with React to avoid multiple React instances
              }
              // Charts
              if (id.includes('recharts') || id.includes('d3')) {
                return 'vendor-charts';
              }
              // UI libraries
              if (id.includes('lucide-react') || id.includes('@mui')) {
                return 'vendor-ui';
              }
              // Other vendor code
              return 'vendor-other';
            }
            
            // Component chunks (lazy load large components)
            if (id.includes('/components/')) {
              // Large chart components
              if (id.includes('Chart') || id.includes('Radar') || id.includes('Waterfall')) {
                return 'components-charts';
              }
              // Large UI components
              if (id.includes('Executive') || id.includes('Narrative') || id.includes('SystemChat')) {
                return 'components-ui';
              }
            }
          },
        },
      },
      chunkSizeWarningLimit: 700,
    },
  };
});
