import { Navigate, useLocation } from "react-router-dom";
import type { ReactNode } from "react";

import { Loading } from "../components/common";
import { useDepartment } from "../stores/department";
import { useSession } from "../stores/session";

/**
 * Route guards.
 *
 * These decide what is *rendered*; they are not what protects the data. Every
 * write endpoint re-checks the caller's role server-side, so a crafted request —
 * or an edited bundle — still gets a 403 from Django. Reading the catalogue
 * needs no sign-in at all: students browse freely.
 */

/** Faculty-only area. Anyone else is sent to the faculty sign-in. */
export function RequireAdmin({ children }: { children: ReactNode }) {
  const booting = useSession((state) => state.booting);
  const user = useSession((state) => state.user);
  const location = useLocation();

  if (booting) return <Loading label="Restoring your session..." />;
  if (!user) {
    return <Navigate to="/faculty" replace state={{ from: location.pathname + location.search }} />;
  }
  if (!user.is_admin) return <Navigate to="/forbidden" replace />;
  return <>{children}</>;
}

/**
 * Requires a chosen department before any department-scoped screen renders.
 *
 * Purely a navigation concern: the department id is a query parameter the API
 * scopes on, so a missing selection means "we do not know what to show you yet",
 * not "you are not allowed".
 */
export function RequireDepartment({ children }: { children: ReactNode }) {
  const selected = useDepartment((state) => state.selected);
  if (!selected) return <Navigate to="/departments" replace />;
  // Selecting a department that has no syllabus yet must not drop the student
  // into an empty dashboard.
  if (!selected.has_curriculum) {
    return <Navigate to={`/departments/${selected.id}`} replace />;
  }
  return <>{children}</>;
}

/** Keeps a signed-in faculty member off the sign-in screen. */
export function RedirectIfAuthenticated({ children }: { children: ReactNode }) {
  const booting = useSession((state) => state.booting);
  const user = useSession((state) => state.user);

  if (booting) return <Loading label="Loading..." />;
  if (user?.is_admin) return <Navigate to="/faculty/dashboard" replace />;
  return <>{children}</>;
}
