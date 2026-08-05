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
    const tgFrameAncestors =
      "frame-ancestors 'self' https://web.telegram.org https://telegram.org";
    return [
      {
        source: "/app/:path*",
        headers: [{ key: "Content-Security-Policy", value: tgFrameAncestors }],
      },
      {
        source: "/voice/:path*",
        headers: [{ key: "Content-Security-Policy", value: tgFrameAncestors }],
      },
      {
        source: "/voice",
        headers: [{ key: "Content-Security-Policy", value: tgFrameAncestors }],
      },
    ];
  },
};

export default nextConfig;
