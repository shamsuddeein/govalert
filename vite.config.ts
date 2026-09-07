import { defineConfig } from "@lovable.dev/vite-tanstack-config";

export default defineConfig({
  tanstackStart: {
    // Redirect TanStack Start's bundled server entry to src/server.ts (our SSR error wrapper).
    // nitro/vite builds from this
    server: { entry: "server" },
  },
  vite: {
    build: {
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes("node_modules/recharts")) {
              return "recharts-vendor";
            }
            if (id.includes("node_modules/lucide-react")) {
              return "lucide-vendor";
            }
            if (id.includes("node_modules/d3-") || id.includes("node_modules/lodash")) {
              return "charts-utils";
            }
          },
        },
      },
    },
  },
});
