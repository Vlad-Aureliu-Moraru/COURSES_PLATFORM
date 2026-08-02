#!/usr/bin/env node
// Fails the build if PUBLIC_API_URL is not set, so production never
// silently falls back to http://localhost:8000.
const url = process.env.PUBLIC_API_URL ?? '';

if (!url || !/^https?:\/\/.+\/api\/v1\/?$/.test(url)) {
  console.error(
    '[check-env] PUBLIC_API_URL is not set to a valid API base URL.\n' +
      '[check-env] Set it in the Cloudflare Pages environment (production):\n' +
      '[check-env]   PUBLIC_API_URL=https://api.banionline.ro/api/v1\n' +
      '[check-env] Or run the build with PUBLIC_API_URL set explicitly.',
  );
  process.exit(1);
}

console.log(`[check-env] PUBLIC_API_URL = ${url}`);
