// Using next.config.js — this file intentionally left minimal
/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://jarvis-mq5i.onrender.com',
  },
};
export default nextConfig;
