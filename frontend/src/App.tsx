import { useEffect } from "react";
import { BrowserRouter, Link, Navigate, Route, Routes } from "react-router-dom";

import { Brand, EmptyState, Footer, Toaster } from "./components/common";
import { ShieldIcon } from "./components/Icons";
import { AdminLayout } from "./layouts/AdminLayout";
import { StudentLayout } from "./layouts/StudentLayout";
import {
  AdminDashboard,
  AdminResourceForm,
  AdminResources,
  AdminSettings,
  AdminSubjectForm,
  AdminSubjects,
  AdminUsers,
} from "./pages/admin";
import { Login, Register } from "./pages/auth/Login";
import { Landing } from "./pages/Landing";
import { DepartmentPending, Departments } from "./pages/student/Departments";
import {
  Dashboard,
  Profile,
  ResourceCategory,
  SemesterDetail,
  Semesters,
  SubjectDetail,
  Subjects,
} from "./pages/student";
import {
  RedirectIfAuthenticated,
  RequireAdmin,
  RequireAuth,
  RequireDepartment,
} from "./routes/guards";
import { useSession } from "./stores/session";

function Forbidden() {
  return (
    <div className="authwrap">
      <Brand to="/" />
      <EmptyState
        icon={<ShieldIcon />}
        title="Access denied"
        detail="Your account does not have administrator privileges. Administrator tools are restricted to department administrators."
        action={
          <div className="row row--tight">
            <Link to="/dashboard" className="btn btn--primary">Go to your dashboard</Link>
            <Link to="/" className="btn">Homepage</Link>
          </div>
        }
      />
    </div>
  );
}

function NotFound() {
  return (
    <div className="authwrap">
      <Brand to="/" />
      <EmptyState
        title="Page not found"
        detail="The page you are looking for does not exist, or the subject or resource it referred to has been removed."
        action={
          <div className="row row--tight">
            <Link to="/" className="btn btn--primary">Go to homepage</Link>
            <Link to="/subjects" className="btn">Browse subjects</Link>
          </div>
        }
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
        {/* Public */}
        <Route path="/" element={<Landing />} />
        <Route
          path="/login"
          element={
            <RedirectIfAuthenticated>
              <Login />
            </RedirectIfAuthenticated>
          }
        />
        <Route
          path="/admin/login"
          element={
            <RedirectIfAuthenticated>
              <Login admin />
            </RedirectIfAuthenticated>
          }
        />
        <Route
          path="/register"
          element={
            <RedirectIfAuthenticated>
              <Register />
            </RedirectIfAuthenticated>
          }
        />
        <Route path="/forbidden" element={<Forbidden />} />

        {/* Department selection — the first step after a student signs in. */}
        <Route
          path="/departments"
          element={
            <RequireAuth>
              <Departments />
            </RequireAuth>
          }
        />

        {/* Student. Every screen below is scoped to the chosen department. */}
        <Route
          element={
            <RequireAuth>
              <StudentLayout />
            </RequireAuth>
          }
        >
          {/* Outside RequireDepartment: this is where a department with no
              curriculum yet lands, so requiring one would loop. */}
          <Route path="/departments/:departmentId" element={<DepartmentPending />} />
        </Route>

        <Route
          element={
            <RequireAuth>
              <RequireDepartment>
                <StudentLayout />
              </RequireDepartment>
            </RequireAuth>
          }
        >
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/semesters" element={<Semesters />} />
          <Route path="/semesters/:semesterId" element={<SemesterDetail />} />
          <Route path="/subjects" element={<Subjects />} />
          <Route path="/subjects/:subjectId" element={<SubjectDetail />} />
          <Route
            path="/subjects/:subjectId/resources/:resourceType"
            element={<ResourceCategory />}
          />
          <Route path="/profile" element={<Profile />} />
        </Route>

        {/* Administrator */}
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
          <Route path="/admin/resources/new" element={<AdminResourceForm />} />
          <Route path="/admin/resources/:resourceId/edit" element={<AdminResourceForm />} />
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
