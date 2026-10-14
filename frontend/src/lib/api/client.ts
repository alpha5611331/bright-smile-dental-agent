import createClient from "openapi-fetch";

import type { components, paths } from "./schema";

/** Shared error body for every non-2xx backend response (SPEC section 7.3). */
export type ApiError = components["schemas"]["ErrorResponse"];

/**
 * Typed client for the backend. Paths, parameters, and bodies are checked against `openapi.json`,
 * which is exported from FastAPI and regenerated with `pnpm gen:api`.
 *
 * Requests are same-origin (`/api/...`) and reach the backend through the Next.js rewrite.
 */
export const api = createClient<paths>({ baseUrl: "" });
