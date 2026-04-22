// src/content/config.ts
//
// Astro content collection schema for the Nexus documentation site.
// Validates frontmatter in .mdx files under src/content/docs/.

import { defineCollection, z } from "astro:content";

const docs = defineCollection({
  type: "content",
  schema: z.object({
    title:       z.string(),
    description: z.string().optional(),
    section:     z.enum(["Architecture", "Implementation", "Operations", "Reference"]),
    order:       z.number().int().positive(),
    // Whether this doc contains live WASM islands (affects build ordering)
    hasLiveWasm: z.boolean().default(false),
  }),
});

export const collections = { docs };
