import type { NextConfig } from "next";
import path from "path";

const BACKEND_URL = process.env.BACKEND_URL || "http://140.84.183.154:8000";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Avoid picking up the monorepo root lockfile when building on Vercel
  outputFileTracingRoot: path.join(__dirname),
  transpilePackages: ["@met4citizen/talkinghead", "three"],
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      "three/addons": path.resolve(__dirname, "node_modules/three/examples/jsm"),
    };
    // TalkingHead ships ESM .mjs + worklet
    config.module.rules.push({
      test: /\.mjs$/,
      include: /node_modules\/@met4citizen\/talkinghead/,
      type: "javascript/auto",
    });
    return config;
  },
  async rewrites() {
    // Only proxy API. /voice is a real Next.js page (do not rewrite it away).
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
        source: "/app",
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
