import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  skipTrailingSlashRedirect: true,
  env: {
    BACKEND_URL: process.env.BACKEND_URL || "http://localhost:8001",
    NEXT_PUBLIC_BACKEND_URL: process.env.BACKEND_URL || "http://localhost:8001",
  },
  async headers() {
    return [
      {
        source: "/((?!_next/static|favicon).*)",
        headers: [
          { key: "Cache-Control", value: "no-cache, no-store, must-revalidate" },
        ],
      },
    ];
  },
};

export default nextConfig;
