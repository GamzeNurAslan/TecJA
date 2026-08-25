import path from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = path.dirname(fileURLToPath(import.meta.url));

export default {
  root: path.join(projectRoot, "frontend"),
  cacheDir: path.join(projectRoot, ".vite-cache"),
  server: {
    host: "127.0.0.1",
    port: 5173
  },
  esbuild: {
    jsx: "automatic"
  }
};
