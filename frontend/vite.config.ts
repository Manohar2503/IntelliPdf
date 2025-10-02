import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import fs from "fs";
import { componentTagger } from "lovable-tagger";

const copyCurrentDocPlugin = () => ({
  name: 'copy-current-doc',
  buildStart() {
    const sourcePath = path.resolve(__dirname, '../backend/output/current_doc.json');
    const destPath = path.resolve(__dirname, './public/current_doc.json');
    if (fs.existsSync(sourcePath)) {
      fs.copyFileSync(sourcePath, destPath);
      console.log(`Copied ${sourcePath} to ${destPath}`);
    } else {
      console.warn(`Warning: ${sourcePath} not found. Skipping copy.`);
    }
  },
});

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 5173,
  },
  plugins: [
    react(),
    mode === 'development' && componentTagger(),
    copyCurrentDocPlugin(),
  ].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
