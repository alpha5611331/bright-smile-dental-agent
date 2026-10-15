import { NextResponse, type NextRequest } from "next/server";

/** Must match the backend cookie name (bright_smile.core.security.SESSION_COOKIE). */
const SESSION_COOKIE = "bs_session";
const LOGIN_PATH = "/dashboard/login";

/**
 * Optimistic gate for the staff area: without a session cookie, go straight to the login page.
 * The backend still verifies every request; an invalid cookie gets a 401 and the client redirects.
 */
export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  if (pathname === LOGIN_PATH || request.cookies.has(SESSION_COOKIE)) {
    return NextResponse.next();
  }
  const login = new URL(LOGIN_PATH, request.url);
  login.searchParams.set("next", pathname + search);
  return NextResponse.redirect(login);
}

export const config = {
  matcher: ["/dashboard", "/dashboard/:path*"],
};
