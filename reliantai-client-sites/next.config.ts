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
    API_BASE_URL: process.env.API_BASE_URL || process.env.PLATFORM_API_URL,
    PLATFORM_API_URL: process.env.PLATFORM_API_URL || process.env.API_BASE_URL,
    PLATFORM_API_KEY: process.env.PLATFORM_API_KEY,
    REVALIDATE_SECRET: process.env.REVALIDATE_SECRET,
  },
};

export default nextConfig;
