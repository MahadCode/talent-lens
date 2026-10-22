import type { NextConfig } from "next";

const apiRewriteTarget = process.env.API_REWRITE_TARGET;

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "standalone",
  experimental: {
    optimizePackageImports: ["lucide-react", "recharts", "framer-motion"],
    staleTimes: {
      dynamic: 180,
      static: 180,
    },
  },
  images: {
    remotePatterns: [{ protocol: "https", hostname: "**" }],
  },
  async rewrites() {
    if (!apiRewriteTarget) {
      return [];
    }
    return [
      {
        source: "/api/v1/:path*",
        destination: `${apiRewriteTarget.replace(/\/$/, "")}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
