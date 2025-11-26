import { defineConfig } from 'vite';
import { viteSingleFile } from 'vite-plugin-singlefile';

export default defineConfig({
  plugins: [viteSingleFile()],
  build: {
    target: 'es2015',
    outDir: 'dist',
    assetsDir: '',
    rollupOptions: {
      output: {
        inlineDynamicImports: true,
        entryFileNames: 'bundle.js',
        assetFileNames: 'styles.css'
      }
    },
    minify: 'terser'
  }
});
