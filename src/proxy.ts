import createMiddleware from "next-intl/middleware";
import { routing } from "./i18n/routing";

// In Next.js 16 this file replaces the former middleware.ts convention.
export default createMiddleware(routing);

export const config = {
  // Match all pathnames except for:
  // - /api, /trpc, /_next, /_vercel
  // - paths containing a dot (e.g. favicon.ico)
  matcher: "/((?!api|trpc|_next|_vercel|.*\\..*).*)",
};
