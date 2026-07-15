import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  typescript: {
    ignoreBuildErrors: true,
  },
  reactStrictMode: false,
  skipTrailingSlashRedirect: true,  // Don't strip trailing slashes (Django requires them)
  devIndicators: {
    buildActivity: true,
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
      {
        protocol: 'http',
        hostname: '**',
      }
    ],
  },

  async rewrites() {
    // Proxy /api/* and /webhooks/* to Django backend on port 8000.
    // In sandbox preview, Caddy intercepts these via XTransformPort query param first.
    const apiUrl = process.env.API_URL || 'http://127.0.0.1:8000';
    return [
      { source: '/api/:path*', destination: `${apiUrl}/api/:path*` },
      { source: '/webhooks/:path*', destination: `${apiUrl}/webhooks/:path*` },
      { source: '/media/:path*', destination: `${apiUrl}/media/:path*` },
    ];
  },
};

import withPWAInit from '@ducanh2912/next-pwa';

const withPWA = withPWAInit({
  dest: 'public',
  disable: process.env.NODE_ENV === 'development',
  register: true,
});

export default withPWA(nextConfig);
