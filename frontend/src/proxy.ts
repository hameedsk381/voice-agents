import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const backendUrl = (process.env.BACKEND_URL || "http://localhost:8001").replace(
  /\/$/,
  ""
);

export async function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  if (pathname.startsWith("/api/v1")) {
    const url = new URL(pathname + search, backendUrl);

    const forwardHeaders = new Headers(request.headers);
    forwardHeaders.delete("host");

    const body = request.method !== "GET" && request.method !== "HEAD"
      ? await request.blob()
      : undefined;

    const backendRes = await fetch(url, {
      method: request.method,
      headers: forwardHeaders,
      body,
      redirect: "manual",
    });

    const bodyText = await backendRes.text();
    const responseHeaders = new Headers(backendRes.headers);
    return new NextResponse(bodyText, {
      status: backendRes.status,
      statusText: backendRes.statusText,
      headers: responseHeaders,
    });
  }
}

export const config = {
  matcher: "/api/v1/:path*",
};
