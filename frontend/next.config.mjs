import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/** @type {import('next').NextConfig} */
const nextConfig = {
  outputFileTracingRoot: __dirname,
  async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || process.env.BACKEND_URL || 'http://127.0.0.1:8000';
    const cleanUrl = backendUrl.replace(/\/api\/v1\/?$/, '');
    return {
      beforeFiles: [
        {
          source: '/',
          destination: '/index.html',
        },
      ],
      afterFiles: [
        {
          source: '/api/v1/:path*',
          destination: `${cleanUrl}/api/v1/:path*`,
        },
      ],
    };
  },
};

export default nextConfig;
