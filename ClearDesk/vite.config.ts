import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          pdf: ['pdfjs-dist'],
          ocr: ['tesseract.js'],
          docx: ['mammoth'],
          xlsx: ['xlsx'],
          icons: ['lucide-react'],
          utils: ['date-fns'],
        },
      },
    },
  },
})
