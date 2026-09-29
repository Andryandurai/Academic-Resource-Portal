import { useEffect, useMemo, useState } from "react";

import { EmptyState, Loading, Notice, formatBytes, formatDate } from "./common";
import { DownloadIcon, EyeIcon, FileIcon } from "./Icons";
import { api } from "../services/api";
import { ApiError } from "../services/client";
import { useUi } from "../stores/ui";
import {
  RESOURCE_TYPES,
  RESOURCE_TYPE_LABELS,
  roman,
  type Department,
  type Resource,
  type ResourceCounts,
  type ResourceType,
  type Semester,
  type Subject,
} from "../types";

/**
 * Department → Semester → Course → Unit, as four dependent dropdowns.
 *
 * Each level is fetched from the API using the level above it as its scope, so
 * a child can only ever offer options that belong to its parent — the same
 * Department → Semester → Subject → Resource chain the rest of the portal
 * walks, just collapsed into one control. Nothing is held in a lookup table
 * here; the options are whatever the database currently holds.
 *
 * "Unit" is not a new concept: it is the resource category a file is filed
 * under (Unit 1-5, CAT 1, CAT 2, Semester Exam), which the Resource model has
 * always carried. No schema or endpoint changed to support this.
 *
 * Every level below the first is optional. Stopping at the department shows
 * everything that department has published; stopping at the semester shows that
 * semester's; and so on. Only the department is required, because listing every
 * file in the college at once is not a useful answer to any question.
 */
export function CascadingResourceFilter({ search = "" }: { search?: string }) {
  const toast = useUi((state) => state.toast);

  const [departmentId, setDepartmentId] = useState("");
  const [semesterId, setSemesterId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [unit, setUnit] = useState<ResourceType | "">("");

  const [departments, setDepartments] = useState<Department[]>([]);
  const [semesters, setSemesters] = useState<Semester[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [unitCounts, setUnitCounts] = useState<ResourceCounts | null>(null);

  const [resources, setResources] = useState<Resource[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // The parent's search box is uncontrolled by us, so its value is debounced
  // here rather than firing a request per keystroke.
  const [term, setTerm] = useState(search);
  useEffect(() => {
    const timer = window.setTimeout(() => setTerm(search), 250);
    return () => window.clearTimeout(timer);
  }, [search]);

  const fail = (caught: unknown, fallback: string) =>
    setError(caught instanceof ApiError ? caught.message : fallback);

  /* --- options, each scoped by the level above it ------------------------ */

  useEffect(() => {
    let cancelled = false;
    api.departments
      .list()
      // A department awaiting its syllabus has no semesters, courses or files,
      // so it is not offered here — it could only ever lead to an empty result.
      // The cards below still list it, with its own "coming soon" state.
      .then((rows) => !cancelled && setDepartments(rows.filter((d) => d.has_curriculum)))
      .catch((caught) => !cancelled && fail(caught, "Could not load departments."));
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!departmentId) {
      setSemesters([]);
      return;
    }
    let cancelled = false;
    api.semesters
      .list(departmentId)
      .then((rows) => !cancelled && setSemesters(rows))
      .catch((caught) => !cancelled && fail(caught, "Could not load semesters."));
    return () => {
      cancelled = true;
    };
  }, [departmentId]);

  useEffect(() => {
    if (!semesterId) {
      setSubjects([]);
      return;
    }
    let cancelled = false;
    api.subjects
      // Scoped by department as well as semester: the semester id already
      // implies one, and sending both means a mismatched pair returns nothing
      // rather than another department's courses.
      .list({ department: departmentId, semester: semesterId, page_size: 200 })
      .then((page) => !cancelled && setSubjects(page.results))
      .catch((caught) => !cancelled && fail(caught, "Could not load courses."));
    return () => {
      cancelled = true;
    };
  }, [departmentId, semesterId]);

  useEffect(() => {
    if (!subjectId) {
      setUnitCounts(null);
      return;
    }
    let cancelled = false;
    api.subjects
      .resourceCounts(subjectId)
      .then((counts) => !cancelled && setUnitCounts(counts))
      .catch((caught) => !cancelled && fail(caught, "Could not load units."));
    return () => {
      cancelled = true;
    };
  }, [subjectId]);

  /* --- results ----------------------------------------------------------- */

  useEffect(() => {
    if (!departmentId) {
      setResources(null);
      return;
    }
    let cancelled = false;
    setBusy(true);
    setError(null);
    api.resources
      .list({
        department: departmentId,
        semester: semesterId || undefined,
        subject: subjectId || undefined,
        resource_type: unit || undefined,
        search: term.trim() || undefined,
        page_size: 200,
      })
      .then((page) => !cancelled && setResources(page.results))
      .catch((caught) => !cancelled && fail(caught, "Could not load resources."))
      .finally(() => !cancelled && setBusy(false));
    return () => {
      cancelled = true;
    };
  }, [departmentId, semesterId, subjectId, unit, term]);

  /* --- cascade ----------------------------------------------------------- */
  // Resetting happens in the change handlers rather than in an effect, so a
  // stale child value is never briefly live against a new parent.

  function chooseDepartment(value: string) {
    setDepartmentId(value);
    setSemesterId("");
    setSubjectId("");
    setUnit("");
  }

  function chooseSemester(value: string) {
    setSemesterId(value);
    setSubjectId("");
    setUnit("");
  }

  function chooseSubject(value: string) {
    setSubjectId(value);
    setUnit("");
  }

  function clearAll() {
    chooseDepartment("");
    setError(null);
  }

  const department = departments.find((d) => String(d.id) === departmentId);
  const semester = semesters.find((s) => String(s.id) === semesterId);
  const subject = subjects.find((s) => String(s.id) === subjectId);

  /** The selection so far, as a readable trail. */
  const path = useMemo(
    () =>
      [
        department?.code,
        semester ? `Semester ${roman(semester.semester_number)}` : null,
        subject ? subject.course_title : null,
        unit ? RESOURCE_TYPE_LABELS[unit] : null,
      ].filter(Boolean) as string[],
    [department, semester, subject, unit],
  );

  async function download(resource: Resource) {
    try {
      await api.resources.download(resource.id, resource.file_name);
    } catch {
      toast("The file could not be downloaded.", "crit");
    }
  }

  async function preview(resource: Resource) {
    try {
      window.open(await api.resources.preview(resource.id), "_blank", "noopener");
    } catch {
      toast("The file could not be opened.", "crit");
    }
  }

  return (
    <section className="stack-3" aria-labelledby="cascade-heading">
      <div className="panel filterpanel">
        <div className="row row--between">
          <h2 id="cascade-heading" className="panel__title">
            Filters
          </h2>
          <button type="button" className="btn btn--sm" onClick={clearAll} disabled={!departmentId}>
            Clear Filters
          </button>
        </div>

        <div className="filterpanel__controls">
          <div className="field">
            <label htmlFor="cascade-department">Department</label>
            <select
              id="cascade-department"
              className="input"
              value={departmentId}
              onChange={(event) => chooseDepartment(event.target.value)}
            >
              <option value="">Select Department</option>
              {departments.map((d) => (
                <option key={d.id} value={String(d.id)}>
                  {d.code} — {d.name}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label htmlFor="cascade-semester">Semester</label>
            <select
              id="cascade-semester"
              className="input"
              value={semesterId}
              disabled={!departmentId}
              aria-describedby={!departmentId ? "cascade-semester-hint" : undefined}
              onChange={(event) => chooseSemester(event.target.value)}
            >
              <option value="">{departmentId ? "All semesters" : "Select Semester"}</option>
              {semesters.map((s) => (
                <option key={s.id} value={String(s.id)}>
                  Semester {roman(s.semester_number)} ({s.subject_count} courses)
                </option>
              ))}
            </select>
            {!departmentId ? (
              <span id="cascade-semester-hint" className="sr-only">
                Select a department first
              </span>
            ) : null}
          </div>

          <div className="field">
            <label htmlFor="cascade-course">Course</label>
            <select
              id="cascade-course"
              className="input"
              value={subjectId}
              disabled={!semesterId}
              aria-describedby={!semesterId ? "cascade-course-hint" : undefined}
              onChange={(event) => chooseSubject(event.target.value)}
            >
              <option value="">{semesterId ? "All courses" : "Select Course"}</option>
              {subjects.map((s) => (
                <option key={s.id} value={String(s.id)}>
                  {s.course_code ? `${s.course_code} — ` : ""}
                  {s.course_title}
                </option>
              ))}
            </select>
            {!semesterId ? (
              <span id="cascade-course-hint" className="sr-only">
                Select a semester first
              </span>
            ) : null}
          </div>

          <div className="field">
            <label htmlFor="cascade-unit">Unit</label>
            <select
              id="cascade-unit"
              className="input"
              value={unit}
              disabled={!subjectId}
              aria-describedby={!subjectId ? "cascade-unit-hint" : undefined}
              onChange={(event) => setUnit(event.target.value as ResourceType | "")}
            >
              <option value="">{subjectId ? "All units" : "Select Unit"}</option>
              {RESOURCE_TYPES.map((type) => (
                <option key={type} value={type}>
                  {RESOURCE_TYPE_LABELS[type]}
                  {unitCounts ? ` (${unitCounts[type]})` : ""}
                </option>
              ))}
            </select>
            {!subjectId ? (
              <span id="cascade-unit-hint" className="sr-only">
                Select a course first
              </span>
            ) : null}
          </div>
        </div>

        {path.length ? (
          <p className="filterpath" role="status" aria-live="polite">
            {path.map((step, index) => (
              <span key={step}>
                {index > 0 ? <span className="filterpath__arrow" aria-hidden="true">→</span> : null}
                <span className="filterpath__step">{step}</span>
              </span>
            ))}
          </p>
        ) : null}
      </div>

      {error ? <Notice kind="crit">{error}</Notice> : null}

      {departmentId ? (
        <div className="stack-3">
          {busy && resources === null ? (
            <Loading label="Loading resources..." />
          ) : (
            <>
              <p className="muted" role="status" aria-live="polite">
                {resources?.length
                  ? `${resources.length} resource${resources.length === 1 ? "" : "s"} in ${path.join(" → ")}${term.trim() ? ` matching "${term.trim()}"` : ""}.`
                  : null}
              </p>

              {resources && resources.length === 0 ? (
                <EmptyState
                  icon={<FileIcon />}
                  title="No resources for this selection yet"
                  detail={
                    term.trim()
                      ? "No published file in this part of the catalogue matches your search. Try a shorter term, or widen the filters."
                      : "Nothing has been published here yet. Material appears as soon as the department uploads it."
                  }
                />
              ) : null}

              <ul className="stack-3" style={{ listStyle: "none", padding: 0, margin: 0 }}>
                {(resources ?? []).map((resource) => (
                  <li key={resource.id}>
                    <article className="panel row row--between row--top">
                      <div>
                        <h3 style={{ margin: 0 }}>{resource.title}</h3>
                        <p className="meta">
                          <span className="chip">{resource.resource_type_label}</span>{" "}
                          {resource.subject_code ? `${resource.subject_code} · ` : ""}
                          {resource.subject_title} · Semester {roman(resource.semester_number)}
                        </p>
                        <p className="meta">
                          <span className="chip">{resource.kind_label}</span>{" "}
                          {resource.is_link ? (
                            resource.url
                          ) : (
                            <>
                              {formatBytes(resource.file_size)} · {resource.file_name}
                            </>
                          )}{" "}
                          · Uploaded {formatDate(resource.created_at)}
                          {resource.uploaded_by_name ? ` · By ${resource.uploaded_by_name}` : ""}
                        </p>
                      </div>
                      <div className="row row--tight">
                        {resource.is_link ? (
                          <a
                            href={resource.url}
                            target="_blank"
                            rel="noreferrer"
                            className="btn btn--primary btn--sm"
                          >
                            <EyeIcon width={15} height={15} /> Open
                          </a>
                        ) : (
                          <>
                            {resource.inline_viewable ? (
                              <button
                                type="button"
                                className="btn btn--sm"
                                onClick={() => void preview(resource)}
                              >
                                <EyeIcon width={15} height={15} /> View
                              </button>
                            ) : null}
                            <button
                              type="button"
                              className="btn btn--primary btn--sm"
                              onClick={() => void download(resource)}
                            >
                              <DownloadIcon width={15} height={15} /> Download
                            </button>
                          </>
                        )}
                      </div>
                    </article>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      ) : null}
    </section>
  );
}
