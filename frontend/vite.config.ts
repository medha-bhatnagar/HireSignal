import { resolve } from 'node:path'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      input: {
        main: resolve(import.meta.dirname, 'index.html'),
        // The background service worker is a second, independent entry
        // point -- it's not loaded by index.html, Chrome loads it directly
        // per manifest.json's "background.service_worker". It needs its
        // own chunk (not bundled into the popup) and a fixed, unhashed
        // filename so manifest.json can reference it by a stable path.
        background: resolve(import.meta.dirname, 'src/background.ts'),
      },
      output: {
        entryFileNames: (chunk) =>
          chunk.name === 'background' ? 'background.js' : 'assets/[name]-[hash].js',
      },
    },
  },
})
