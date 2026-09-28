import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { Brand, EmptyState, Footer, Loading, Notice, PageHead, Toaster } from "../../components/common";
import { BookIcon, ChevronRightIcon, LayersIcon, SearchIcon } from "../../components/Icons";
import { api } from "../../services/api";
import { ApiError } from "../../services/client";
import { useDepartment } from "../../stores/department";
import type { Department } from "../../types";

/**
 * Department selection — the first step for a student opening the portal.
 *
 * The list comes from the API, never from a constant in this file: adding a
 * department later is a database change, and this page picks it up with no
 * frontend edit.
 */
export function Departments() {
  const navigate = useNavigate();
  const select = useDepartment((state) => state.select);

  const [departments, setDepartments] = useState<Department[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [term, setTerm] = useState("");

  useEffect(() => {
    let cancelled = false;
    api.departments
      .list()
      .then((rows) => !cancelled && setDepartments(rows))
      .catch((caught) =>
        !cancelled &&
        setError(caught instanceof ApiError ? caught.message : "Could not load departments."),
      );
    return () => {
      cancelled = true;
    };
  }, []);

  /**
   * Filtering runs locally here.
   *
   * Nineteen rows arrive in one request, so a round trip per keystroke would be
   * slower and no more correct. The API supports `?search=` for when the list
   * grows past what is sensible to hold client-side.
   */
  const visible = useMemo(() => {
    if (!departments) return [];
    const needle = term.trim().toLowerCase();
    if (!needle) return departments;
    return departments.filter(
      (department) =>
        department.name.toLowerCase().includes(needle) ||
        department.code.toLowerCase().includes(needle),
    );
  }, [departments, term]);

  function choose(department: Department) {
    select(department);
    navigate(department.has_curriculum ? "/dashboard" : `/departments/${department.id}`);
  }

  return (
    <div className="appshell">
      <header className="topbar">
        <div className="topbar__inner">
          <Brand to="/departments" />
        </div>
      </header>

      <main id="main" className="appmain">
        <PageHead
          eyebrow="Rajalakshmi Engineering College"
          title="Select Your Department"
          lead="Choose your department to access your academic resources."
        />

        <form className="panel searchfield" role="search" onSubmit={(e) => e.preventDefault()}>
          <span className="searchfield__icon" aria-hidden="true">
            <SearchIcon width={17} height={17} />
          </span>
          <label htmlFor="department-search" className="sr-only">
            Search department
          </label>
          <input
            id="department-search"
            className="input"
            type="search"
            value={term}
            onChange={(event) => setTerm(event.target.value)}
            placeholder="Search department..."
            autoComplete="off"
          />
        </form>

        {error ? <Notice kind="crit">{error}</Notice> : null}
        {!departments && !error ? <Loading label="Loading departments..." /> : null}

        {departments ? (
          <>
            <p className="muted" role="status" aria-live="polite">
              {term
                ? `${visible.length} of ${departments.length} departments match "${term}".`
                : `${departments.length} departments`}
            </p>

            {visible.length === 0 ? (
              <EmptyState
                title="No departments match your search"
                detail="Try a shorter term, or the department's abbreviation."
              />
            ) : (
              <div className="grid grid-3">
                {visible.map((department) => (
                  <button
                    key={department.id}
                    type="button"
                    className="deptcard"
                    onClick={() => choose(department)}
                  >
                    <span className="deptcard__code">{department.code}</span>
                    <span className="deptcard__name">{department.name}</span>
                    <span className="deptcard__foot">
                      <span className="meta">
                        {department.has_curriculum
                          ? `${department.semester_count} semesters · ${department.subject_count} subjects`
                          : "Curriculum coming soon"}
                      </span>
                      <span className="deptcard__go" aria-hidden="true">
                        View Department
                        <ChevronRightIcon width={14} height={14} />
                      </span>
                    </span>
                  </button>
                ))}
              </div>
            )}
          </>
        ) : null}
      </main>

      <Footer />
      <Toaster />
    </div>
  );
}

/**
 * A department that has no curriculum yet.
 *
 * Reached by selecting any department whose syllabus has not been supplied.
 * Deliberately shows nothing that looks like content — no placeholder
 * semesters, no sample subjects — because an invented structure is worse than
 * an honest gap.
 */
export function DepartmentPending() {
  const { departmentId } = useParams();
  const select = useDepartment((state) => state.select);
  const navigate = useNavigate();

  const [department, setDepartment] = useState<Department | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api.departments
      .get(departmentId!)
      .then((row) => {
        if (cancelled) return;
        setDepartment(row);
        select(row);
        // A department that has since gained a syllabus goes straight through.
        if (row.has_curriculum) navigate("/dashboard", { replace: true });
      })
      .catch((caught) =>
        !cancelled &&
        setError(caught instanceof ApiError ? caught.message : "Could not load this department."),
      );
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [departmentId]);

  if (error) return <Notice kind="crit">{error}</Notice>;
  if (!department) return <Loading label="Loading department..." />;

  return (
    <>
      <PageHead eyebrow={department.code} title={department.name} />

      <EmptyState
        icon={<LayersIcon />}
        title={`Academic resources for ${department.name} are currently being prepared.`}
        detail="Subject and semester information will be available soon."
        action={
          <div className="row row--tight">
            <Link to="/departments" className="btn btn--primary">
              Choose another department
            </Link>
          </div>
        }
      />

      <div className="panel stack-8">
        <div className="row row--tight">
          <span className="iconbadge" aria-hidden="true">
            <BookIcon width={16} height={16} />
          </span>
          <div>
            <p style={{ margin: 0, fontWeight: 700 }}>Nothing is being invented here</p>
            <p className="muted" style={{ margin: "2px 0 0" }}>
              This department has no semesters, subjects or resources in the portal yet. They will
              appear as soon as the department's syllabus is published — no placeholder content is
              shown in the meantime.
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
