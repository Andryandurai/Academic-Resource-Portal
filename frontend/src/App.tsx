import { useEffect } from "react";
import { BrowserRouter, Link, Navigate, Route, Routes } from "react-router-dom";

import { Brand, EmptyState, Footer, Toaster } from "./components/common";
import { ShieldIcon } from "./components/Icons";
import { AdminLayout } from "./layouts/AdminLayout";
import {
  AdminDashboard,
  AdminResourceBulkForm,
  AdminResourceEditForm,
  AdminResources,
  AdminSettings,
  AdminSubjectForm,
  AdminSubjects,
  AdminUsers,
} from "./pages/admin";
import { Login } from "./pages/auth/Login";
import { RedirectIfAuthenticated, RequireAdmin } from "./routes/guards";
import { useSession } from "./stores/session";

function Forbidden() {
  return (
    <div className="authwrap">
      <Brand to="/admin/login" admin />
      <EmptyState
        icon={<ShieldIcon />}
        title="Access denied"
        detail="Your account does not have administrator privileges."
        action={
          <Link to="/admin/login" className="btn btn--primary">Back to login</Link>
        }
      />
    </div>
  );
}

function NotFound() {
  return (
    <div className="authwrap">
      <Brand to="/admin/login" admin />
      <EmptyState
        title="Page not found"
        detail="The page you are looking for does not exist."
        action={<Link to="/admin" className="btn btn--primary">Go to dashboard</Link>}
      />
      <Footer />
    </div>
  );
}

export function App() {
  const hydrate = useSession((state) => state.hydrate);

  // Re-validates a persisted token against the API before the first protected
  // route renders, so a revoked or demoted account is caught on boot.
  useEffect(() => {
    void hydrate();
  }, [hydrate]);

  return (
    <BrowserRouter>
      <a href="#main" className="sr-only">Skip to main content</a>
      <Routes>
        <Route path="/" element={<Navigate to="/admin/login" replace />} />
        <Route
          path="/admin/login"
          element={
            <RedirectIfAuthenticated>
              <Login />
            </RedirectIfAuthenticated>
          }
        />
        <Route path="/forbidden" element={<Forbidden />} />

        <Route
          element={
            <RequireAdmin>
              <AdminLayout />
            </RequireAdmin>
          }
        >
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/subjects" element={<AdminSubjects />} />
          <Route path="/admin/subjects/new" element={<AdminSubjectForm />} />
          <Route path="/admin/subjects/:subjectId/edit" element={<AdminSubjectForm />} />
          <Route path="/admin/resources" element={<AdminResources />} />
          <Route path="/admin/resources/new" element={<AdminResourceBulkForm />} />
          <Route path="/admin/resources/:resourceId/edit" element={<AdminResourceEditForm />} />
          <Route path="/admin/users" element={<AdminUsers />} />
          <Route path="/admin/settings" element={<AdminSettings />} />
        </Route>

        <Route path="/index.html" element={<Navigate to="/" replace />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
      <Toaster />
    </BrowserRouter>
  );
}
