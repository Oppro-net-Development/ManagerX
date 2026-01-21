import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

export default defineConfig(({ mode }) => ({
  // WICHTIG: Erlaubt korrekte Pfade auf deiner Subdomain
  base: "/", 
  
  server: {
    host: "::",
    port: 8080,
    hmr: {
      overlay: false,
    },
  },
  plugins: [
    react(), 
    mode === "development" && componentTagger()
  ].filter(Boolean),
  resolve: {
    alias: {
      // Dein Alias zeigt auf ./src/web - das ist wichtig für deine Imports
      "@": path.resolve(__dirname, "./src/web"),
    },
  },
  build: {
    // Stellt sicher, dass der Output-Ordner 'dist' heißt (passend zur deploy.yml)
    outDir: "dist",
    // Optimierung für sauberen Code
    minify: "esbuild",
    reportCompressedSize: false,
  },
}));