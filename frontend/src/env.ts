import { z } from "zod";

/**
 * Server-side environment, validated once at startup (`next dev`, `next build`, `next start`).
 * Nothing here is exposed to the browser; client code talks to the same-origin `/api/*` proxy.
 */
const serverEnvSchema = z.object({
  BACKEND_URL: z
    .url({ protocol: /^https?$/ })
    .default("http://localhost:8000")
    .transform((url) => url.replace(/\/+$/, "")),
});

export type ServerEnv = z.infer<typeof serverEnvSchema>;

export function parseServerEnv(
  source: Record<string, string | undefined> = process.env,
): ServerEnv {
  const result = serverEnvSchema.safeParse(source);
  if (!result.success) {
    throw new Error(`Invalid frontend environment:\n${z.prettifyError(result.error)}`);
  }
  return result.data;
}
