// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import rehypeExternalLinks from 'rehype-external-links';

// https://astro.build/config
export default defineConfig({
  site: 'https://banionline.ro',
  output: 'static',
  markdown: {
    rehypePlugins: [
      [
        rehypeExternalLinks,
        { rel: ['noopener', 'nofollow'], target: '_blank' },
      ],
    ],
  },
  vite: {
    plugins: [tailwindcss()],
  },
});
