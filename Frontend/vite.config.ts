import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import tailwindcss from "@tailwindcss/vite";

// Vite config avec Tailwind et proxy vers backend
export default defineConfig({
    plugins: [
        react(),
        tailwindcss(),
    ],

    // Server dev
    server: {
        port: 5173, // ton frontend en dev
        proxy: {
            '/api': {
                target: 'http://localhost:5000', // Flask backend local
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/api/, '/'), // optionnel si ton Flask ne gère pas /api prefix
            },
        },
    },

    // Résolution des chemins pour Tailwind / alias
    resolve: {
        alias: {
            '@': path.resolve(__dirname, 'src'),
        },
    },

    //  Build (production)
    build: {
        outDir: 'dist', // ce que Nginx va servir
        emptyOutDir: true,
    },
});
