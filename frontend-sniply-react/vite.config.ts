import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server on :3000. A strict Content-Security-Policy is shipped via the
// <meta> tag in index.html (see plan security item 5) so in-memory tokens are
// protected against XSS: scripts limited to self, connect-src to API + Auth0.
export default defineConfig({
  plugins: [react()],
  server: { port: 3000, strictPort: true },
});
