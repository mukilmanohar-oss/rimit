import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  typescript: {
    ignoreBuildErrors: true,
  },
  reactStrictMode: false,
  skipTrailingSlashRedirect: true,  // Don't strip trailing slashes (Django requires them)
  async rewrites() {
    // Proxy /api/* and /webhooks/* to Django backend on port 8000.
    // In sandbox preview, Caddy intercepts these via XTransformPort query param first.
    return [
      { source: '/api/:path*', destination: 'http://127.0.0.1:8000/api/:path*' },
      { source: '/webhooks/:path*', destination: 'http://127.0.0.1:8000/webhooks/:path*' },
    ];
  },
};

export default nextConfig;
