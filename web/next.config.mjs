/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // Browser calls same-origin /api/backend/* → FastAPI on localhost:8000
    // Works for local dev and ngrok (single tunnel on :3000).
    return [
      {
        source: "/api/backend/:path*",
        destination: "http://127.0.0.1:8000/:path*",
      },
    ];
  },
};

export default nextConfig;
