import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const courses = defineCollection({
  loader: glob({ pattern: '[0-9][0-9]-*.md', base: '../' }),
  schema: z.object({
    title: z.string().optional(),
    order: z.number().optional(),
    est_time: z.string().optional(),
    free: z.boolean().optional(),
    description: z.string().optional(),
  }),
});

export const collections = { courses };
