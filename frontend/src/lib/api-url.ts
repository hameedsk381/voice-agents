/**
 * API base URL. In the browser we default to same-origin `/api/v1` (Next.js rewrite
 * to the backend) to avoid CORS and cross-port cookie issues during local dev.
 */
export function getApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");
  if (configured) {
    return configured;
  }
  if (typeof window !== "undefined") {
    return "/api/v1";
  }
  return "http://localhost:8001/api/v1";
}
