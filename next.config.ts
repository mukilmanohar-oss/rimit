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
    domains: ['0fc6-111-92-121-234.ngrok-free.app'],
  },
  turbopack: {},
  allowedDevOrigins: ['0fc6-111-92-121-234.ngrok-free.app'],
  webpack: (config: any, { dev, isServer, webpack }: any) => {
    if (dev && !isServer) {
      // Force HMR to use the ngrok wss endpoint
      config.plugins.push(new webpack.DefinePlugin({
        'process.env.__NEXT_HMR_URL': JSON.stringify('wss://0fc6-111-92-121-234.ngrok-free.app/_next/webpack-hmr'),
      }));

      config.devServer = {
        ...config.devServer,
        allowedHosts: 'all', // Allows the ngrok tunnel host (webpack 5 uses a string or array)
      };
      config.watchOptions = {
        poll: 1000,
        aggregateTimeout: 300,
      };
    }
    return config;
  },
  async rewrites() {
    // Proxy /api/* and /webhooks/* to Django backend on port 8000.
    // In sandbox preview, Caddy intercepts these via XTransformPort query param first.
    const apiUrl = process.env.API_URL || 'http://127.0.0.1:8000';
    return [
      { source: '/api/:path*', destination: `${apiUrl}/api/:path*` },
      { source: '/webhooks/:path*', destination: `${apiUrl}/webhooks/:path*` },
    ];
  },
};

export default nextConfig;
