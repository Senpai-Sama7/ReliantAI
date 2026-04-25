import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "preview.reliantai.org",
      },
      {
        protocol: "https",
        hostname: "api.reliantai.org",
      },
    ],
  },
  env: {
    PLATFORM_API_URL: process.env.PLATFORM_API_URL,
    PLATFORM_API_KEY: process.env.PLATFORM_API_KEY,
  },
};

export default nextConfig;
