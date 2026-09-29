import { useEffect } from "react";
import { BrowserRouter, Link, Navigate, Route, Routes } from "react-router-dom";

import { Brand, EmptyState, Footer, Toaster } from "./components/common";
import { ShieldIcon } from "./components/Icons";
import { AdminLayout } from "./layouts/AdminLayout";
import { StudentLayout } from "./layouts/StudentLayout";
import {
  AdminDashboard,
  AdminResourceBulkForm,
  AdminResourceEditForm,
  AdminResources,
  AdminSettings,
  AdminSubjectForm,
  AdminSubjects,
} from "./pages/admin";
import { Login } from "./pages/auth/Login";
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
        detail="This area is for faculty."
        action={
          <div className="row row--tight">
            <Link to="/faculty" className="btn btn--primary">Faculty sign-in</Link>
            <Link to="/" className="btn">Student portal</Link>
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
            <Link to="/" className="btn btn--primary">Go to the portal</Link>
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

  // Re-validates a persisted token against the API before the first
  // protected route renders, so a revoked or demoted account is caught on boot.
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

        {/* Department selection — the first step after a student signs in. */}
        <Route
          path="/departments"
          element={
            <RequireAuth>
              <Departments />
            </RequireAuth>
          }
        />
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

        {/* Faculty: sign in at /faculty, everything else scoped under it. */}
        <Route
          path="/faculty"
          element={
            <RedirectIfAuthenticated>
              <Login admin />
            </RedirectIfAuthenticated>
          }
        />
        <Route
          element={
            <RequireAdmin>
              <AdminLayout />
            </RequireAdmin>
          }
        >
          <Route path="/faculty/dashboard" element={<AdminDashboard />} />
          <Route path="/faculty/subjects" element={<AdminSubjects />} />
          <Route path="/faculty/subjects/new" element={<AdminSubjectForm />} />
          <Route path="/faculty/subjects/:subjectId/edit" element={<AdminSubjectForm />} />
          <Route path="/faculty/resources" element={<AdminResources />} />
          <Route path="/faculty/resources/new" element={<AdminResourceBulkForm />} />
          <Route path="/faculty/resources/:resourceId/edit" element={<AdminResourceEditForm />} />
          <Route path="/faculty/settings" element={<AdminSettings />} />
        </Route>

        {/* Old links and bookmarks. */}
        <Route path="/admin/*" element={<Navigate to="/faculty" replace />} />
        <Route path="/admin/login" element={<Navigate to="/faculty" replace />} />
        <Route path="/register" element={<Navigate to="/login" replace />} />
        <Route path="/forbidden" element={<Forbidden />} />
        <Route path="/index.html" element={<Navigate to="/" replace />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
      <Toaster />
    </BrowserRouter>
  );
}
