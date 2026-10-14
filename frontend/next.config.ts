import type { NextConfig } from "next";

import { parseServerEnv } from "./src/env";

const { BACKEND_URL } = parseServerEnv();

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  reactCompiler: true,
  poweredByHeader: false,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  // Same-origin API: the browser only ever calls /api/*, which is proxied to the FastAPI backend.
  // This keeps cookies first-party, avoids CORS, and hides the backend origin (SPEC section 9.2).
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${BACKEND_URL}/api/:path*` }];
  },
};

export default nextConfig;
