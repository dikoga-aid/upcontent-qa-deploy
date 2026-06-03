import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// Dev server on :3001. CSP shipped via <meta> in index.html (plan security
// item 5): scripts limited to self; connect-src to API + Auth0 only.
export default defineConfig({
  plugins: [vue()],
  server: { port: 3001, strictPort: true },
});
