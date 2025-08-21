/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
    NEXT_PUBLIC_MAPTILER_API_KEY: process.env.NEXT_PUBLIC_MAPTILER_API_KEY,
  },
  images: {
    domains: ['api.maptiler.com'],
  },
  webpack: (config) => {
    // Handle MapTiler SDK
    config.resolve.fallback = {
      ...config.resolve.fallback,
      fs: false,
      net: false,
      tls: false,
    };
    return config;
  },
}

module.exports = nextConfig