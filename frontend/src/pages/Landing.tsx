import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Brand, COLLEGE, PORTAL_NAME, Footer } from "../components/common";
import { BookIcon, FileIcon } from "../components/Icons";
import { api } from "../services/api";
import { useSession } from "../stores/session";
import { EXAM_TYPES, LEARNING_TYPES, RESOURCE_TYPE_LABELS, type Department } from "../types";

/**
 * Public landing page.
 *
 * The semester and resource structure is public information; the counts and the
 * material behind them are not, so the statistics strip only appears for a
 * signed-in visitor rather than exposing them to anyone who loads the page.
 */
export function Landing() {
  const user = useSession((state) => state.user);
  const [departments, setDepartments] = useState<Department[] | null>(null);

  useEffect(() => {
    if (!user) return;
    void api.departments.list().then(setDepartments).catch(() => setDepartments(null));
  }, [user]);

  // A student's home is the department picker: no department is the default.
  const home = user ? (user.is_admin ? "/faculty/dashboard" : "/departments") : "/login";

  return (
    <div className="appshell">
      <header className="topbar">
        <div className="topbar__inner">
          <Brand to="/" />
          <nav className="row row--tight" aria-label="Primary">
            {user ? (
              <Link to={home} className="btn btn--primary btn--sm">
                {user.is_admin ? "Admin Dashboard" : "Dashboard"}
              </Link>
            ) : (
              <>
                <Link to="/faculty" className="btn btn--sm">Administrator</Link>
                <Link to="/login" className="btn btn--primary btn--sm">Student Login</Link>
              </>
            )}
          </nav>
        </div>
      </header>

      <main id="main" style={{ flex: 1 }}>
        <section className="rechero">
          <div className="rechero__inner">
            <span className="chip chip--signal">All departments</span>
            <h1>{COLLEGE}</h1>
            <p className="lead" style={{ color: "var(--signal-ink)", fontWeight: 700 }}>
              {PORTAL_NAME}
            </p>
            <p className="muted" style={{ maxWidth: "58ch" }}>
              A centralized academic resource hub for every department of the college. Choose your
              department to access its semester-wise subjects, unit notes, CAT resources and
              semester examination materials.
            </p>
            <div className="row row--tight" style={{ marginTop: "var(--s5)" }}>
              <Link to={user ? "/departments" : "/login"} className="btn btn--primary btn--lg">
                {user ? "Choose Your Department" : "Explore Departments"}
              </Link>
              <Link to={home} className="btn btn--lg">
                {user ? "Go to Dashboard" : "Student Login"}
              </Link>
            </div>
          </div>
        </section>

        {/* Departments, not semesters: the number of semesters differs by
            department, so the landing page must not assert a fixed structure. */}
        <section className="appmain">
          <h2>Departments</h2>
          <p className="muted">
            {departments
              ? `${departments.length} departments across the college. Choose yours to see its curriculum.`
              : "Sign in to choose your department."}
          </p>
          {departments ? (
            <div className="grid grid-4">
              {departments.map((department) => (
                <Link key={department.id} to="/departments" className="subjectcard">
                  <span className="label">{department.code}</span>
                  <strong style={{ fontSize: "var(--fs-body)", lineHeight: 1.35 }}>
                    {department.name}
                  </strong>
                  <span className="meta">
                    {department.has_curriculum
                      ? `${department.semester_count} semesters · ${department.subject_count} subjects`
                      : "Curriculum coming soon"}
                  </span>
                </Link>
              ))}
            </div>
          ) : null}
        </section>

        <section className="appmain">
          <h2>Academic Resources</h2>
          <p className="muted" style={{ maxWidth: "58ch" }}>
            Every subject carries the same eight resource categories, so material is always in a
            predictable place.
          </p>
          <div className="grid grid-2">
            <div className="panel">
              <div className="row row--tight">
                <span className="iconbadge iconbadge--signal"><BookIcon /></span>
                <h3 style={{ margin: 0 }}>Learning Materials</h3>
              </div>
              <div className="row row--tight" style={{ marginTop: "var(--s3)", flexWrap: "wrap" }}>
                {LEARNING_TYPES.map((type) => (
                  <span key={type} className="chip">{RESOURCE_TYPE_LABELS[type]}</span>
                ))}
              </div>
              <p className="muted">
                Unit-wise notes and reference material published by the department administrator.
              </p>
            </div>

            <div className="panel">
              <div className="row row--tight">
                <span className="iconbadge iconbadge--data"><FileIcon /></span>
                <h3 style={{ margin: 0 }}>Examination Resources</h3>
              </div>
              <div className="row row--tight" style={{ marginTop: "var(--s3)", flexWrap: "wrap" }}>
                {EXAM_TYPES.map((type) => (
                  <span key={type} className="chip">{RESOURCE_TYPE_LABELS[type]}</span>
                ))}
              </div>
              <p className="muted">
                Question papers, study material and important material for the continuous
                assessment tests and the semester examination.
              </p>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
