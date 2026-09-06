import { Navigate, useLocation } from "react-router-dom";
import type { ReactNode } from "react";

import { Loading } from "../components/common";
import { useSession } from "../stores/session";

/**
 * Route guards.
 *
 * These decide what is *rendered*; they are not what protects the data. Every
 * API endpoint re-checks the caller's role server-side, so a crafted request —
 * or the bundle — still gets a 403 from Django.
 */

export function RequireAdmin({ children }: { children: ReactNode }) {
  const booting = useSession((state) => state.booting);
  const user = useSession((state) => state.user);
  const location = useLocation();

  if (booting) return <Loading label="Restoring your session..." />;
  if (!user) {
    return (
      <Navigate to="/admin/login" replace state={{ from: location.pathname + location.search }} />
    );
  }
  if (!user.is_admin) return <Navigate to="/forbidden" replace />;
  return <>{children}</>;
}

/** Keeps a signed-in administrator off the login screen. */
export function RedirectIfAuthenticated({ children }: { children: ReactNode }) {
  const booting = useSession((state) => state.booting);
  const user = useSession((state) => state.user);

  if (booting) return <Loading label="Loading..." />;
  if (user) return <Navigate to="/admin" replace />;
  return <>{children}</>;
}
