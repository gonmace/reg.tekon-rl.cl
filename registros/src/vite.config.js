const path = require('path');
const { defineConfig } = require('vite')

module.exports = defineConfig({
    build: {
        outDir: path.resolve(__dirname, '../../static/js'),
        minify: true,
        rollupOptions: {
            output: {
                entryFileNames: 'maps.js',
                format: 'iife',
              },
            input: './index-maps.js',
        }
    }
});
