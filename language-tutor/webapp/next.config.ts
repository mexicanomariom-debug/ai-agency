import type { NextConfig } from "next";

const BACKEND_URL = process.env.BACKEND_URL || "http://140.84.183.154:8000";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/proxy/:path*",
        destination: `${BACKEND_URL}/:path*`,
      },
    ];
  },
  async headers() {
    return [
      {
        source: "/app/:path*",
        headers: [
          {
            key: "Content-Security-Policy",
            value:
              "frame-ancestors 'self' https://web.telegram.org https://telegram.org",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
