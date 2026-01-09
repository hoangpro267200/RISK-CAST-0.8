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
      rollupOptions: {
        output: {
          manualChunks: {
            'vendor-react': ['react', 'react-dom'],
            'vendor-charts': ['recharts'],
            'vendor-motion': ['motion'],
          },
        },
      },
      chunkSizeWarningLimit: 700,
    },
  };
});
