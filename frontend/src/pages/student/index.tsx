import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

import {
  Breadcrumbs,
  EmptyState,
  Fact,
  Loading,
  Notice,
  PageHead,
  SectionHead,
  Stat,
  formatBytes,
  formatDate,
} from "../../components/common";
import {
  ArrowLeftIcon,
  BookIcon,
  DownloadIcon,
  EyeIcon,
  FileIcon,
  CloseIcon,
  GridIcon,
  LayersIcon,
  SearchIcon,
} from "../../components/Icons";
import { LogoutButton } from "../../components/LogoutButton";
import { api, type SubjectQuery } from "../../services/api";
import { ApiError } from "../../services/client";
import { useDocumentTitle } from "../../hooks/useDocumentTitle";
import { useDepartment } from "../../stores/department";
import { useSession } from "../../stores/session";
import { useUi } from "../../stores/ui";
import {
  CATEGORY_LABELS,
  COURSE_TYPES,
  EXAM_TYPES,
  LEARNING_TYPES,
  RESOURCE_TYPE_LABELS,
  RESOURCE_TYPE_SLUGS,
  resourceTypeFromSlug,
  roman,
  type Resource,
  type ResourceCounts,
  type Semester,
  type Stats,
  type Subject,
  type SubjectFacets,
} from "../../types";

/* ------------------------------------------------------------------ hooks -- */
function useAsync<T>(loader: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    loader()
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(caught instanceof ApiError ? caught.message : "Could not load this page.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, error, loading };
}

/* ------------------------------------------------------------- components -- */
function SubjectCard({ subject, showSemester = false }: { subject: Subject; showSemester?: boolean }) {
  const kind = COURSE_TYPES.find((c) => c.value === subject.course_type);
  const chip =
    subject.course_type === "THEORY"
      ? "chip chip--signal"
      : subject.course_type === "LABORATORY"
        ? "chip chip--ok"
        : "chip chip--data";
  return (
    <article className="subjectcard">
      <div className="row row--between">
        {subject.course_code ? (
          <span className="subjectcard__code">{subject.course_code}</span>
        ) : (
          <span className="subjectcard__code subjectcard__code--none">Code not specified</span>
        )}
        <span className={chip}>{kind?.short ?? subject.course_type}</span>
      </div>

      <h3 className="subjectcard__title">
        <Link to={`/subjects/${subject.id}`}>{subject.course_title}</Link>
      </h3>

      <div className="row row--tight">
        <span className="chip">{subject.category}</span>
        {showSemester ? <span className="meta">Semester {roman(subject.semester_number)}</span> : null}
      </div>

      <dl className="ltpc">
        <div><dt>L</dt><dd className="tabular">{subject.l}</dd></div>
        <div><dt>T</dt><dd className="tabular">{subject.t}</dd></div>
        <div><dt>P</dt><dd className="tabular">{subject.p}</dd></div>
        <div className="is-credits"><dt>C</dt><dd className="tabular">{subject.credits}</dd></div>
      </dl>

      <div className="row row--between">
        <span className="meta">
          {subject.resource_count === 0
            ? "No resources yet"
            : `${subject.resource_count} resource${subject.resource_count === 1 ? "" : "s"}`}
        </span>
        <Link to={`/subjects/${subject.id}`} className="btn btn--sm">
          View Subject
        </Link>
      </div>
    </article>
  );
}

/** Theory and lab-oriented theory are never mixed into one unstructured list. */
function SubjectSections({
  subjects,
  showSemester,
  empty,
}: {
  subjects: Subject[];
  showSemester?: boolean;
  /** Shown instead of the search-miss message when the list is empty by nature
   *  rather than by filtering — a semester whose syllabus lists no courses. */
  empty?: ReactNode;
}) {
  // One section per course type, driven by the shared vocabulary — a new type
  // appears here without editing this component.
  const groups = COURSE_TYPES.map((kind) => ({
    kind,
    items: subjects.filter((s) => s.course_type === kind.value),
  })).filter((group) => group.items.length > 0);

  if (subjects.length === 0) {
    return (
      empty ?? (
        <EmptyState
          icon={<BookIcon />}
          title="No subjects match your search"
          detail="Try a different course code, subject name or filter combination."
        />
      )
    );
  }

  return (
    <div className="stack-8">
      {groups.map((group) => (
        <section key={group.kind.value}>
          <SectionHead title={`${group.kind.label} Courses`} count={group.items.length} />
          <div className="grid grid-3">
            {group.items.map((s) => (
              <SubjectCard key={s.id} subject={s} showSemester={showSemester} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

const ALL_DEPARTMENTS = "all";

/**
 * Every filter the catalogue understands, as it lives in the URL.
 *
 * The URL is the single source of truth: the bar writes to it, the page reads
 * from it, and a filtered view is therefore a link you can share, bookmark and
 * reach with the back button. There is no second copy of the filter state to
 * fall out of step, and no "Apply" step — changing a control rewrites the query
 * string, which re-runs the request. The page itself never reloads.
 */
const FILTER_KEYS = ["q", "department", "deptq", "semester", "type", "category", "credits"] as const;

/** Translates the URL into the API query. One place, so bar and page agree. */
function subjectQuery(params: URLSearchParams, fallbackDepartment?: number): SubjectQuery {
  const explicit = params.get("department");
  const departmentSearch = params.get("deptq") || undefined;
  // No department in the URL means "the one the student picked"; ALL_DEPARTMENTS
  // means they deliberately widened the search to the whole college.
  //
  // Typing in the department box is itself a decision to look past your own
  // department, so it lifts that default. Without this, searching "food" from
  // inside AI&DS would AND the two and answer zero — which reads as a broken
  // filter rather than as the contradiction it is.
  const fallback = departmentSearch ? ALL_DEPARTMENTS : fallbackDepartment ? String(fallbackDepartment) : "";
  const chosen = explicit ?? fallback;
  return {
    search: params.get("q") || undefined,
    department: chosen && chosen !== ALL_DEPARTMENTS ? chosen : undefined,
    department_search: departmentSearch,
    semester_number: params.get("semester") || undefined,
    course_type: params.get("type") || undefined,
    category: params.get("category") || undefined,
    credits: params.get("credits") || undefined,
  };
}

/** A removable summary of one active filter. */
function FilterChip({ label, value, onRemove }: { label: string; value: string; onRemove: () => void }) {
  return (
    <span className="chip filterchip">
      <span className="filterchip__label">{label}</span>
      <span className="filterchip__value">{value}</span>
      <button
        type="button"
        className="filterchip__x"
        onClick={onRemove}
        aria-label={`Remove ${label} filter: ${value}`}
      >
        <CloseIcon width={12} height={12} />
      </button>
    </span>
  );
}

/**
 * The catalogue filter bar.
 *
 * Options come from `/api/subjects/facets/` rather than from a list in this
 * file, so the bar offers exactly the departments, semesters, categories,
 * credit values and course types that some course actually has — and each shows
 * how many courses it would match, counted with its own filter lifted but every
 * other filter still applied.
 */
function SubjectFilters({
  facets,
  showSemester = true,
  showDepartment = false,
}: {
  facets: SubjectFacets | null;
  showSemester?: boolean;
  showDepartment?: boolean;
}) {
  const [params, setParams] = useSearchParams();
  const [term, setTerm] = useState(params.get("q") ?? "");
  const [deptTerm, setDeptTerm] = useState(params.get("deptq") ?? "");

  useEffect(() => {
    setTerm(params.get("q") ?? "");
    setDeptTerm(params.get("deptq") ?? "");
  }, [params]);

  // Both text boxes are debounced, so a request is not fired per keystroke.
  useEffect(() => {
    if (term === (params.get("q") ?? "")) return;
    const timer = window.setTimeout(() => update("q", term), 250);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [term]);

  useEffect(() => {
    if (deptTerm === (params.get("deptq") ?? "")) return;
    const timer = window.setTimeout(() => update("deptq", deptTerm), 250);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deptTerm]);

  function update(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next, { replace: true });
  }

  function clearAll() {
    const next = new URLSearchParams(params);
    FILTER_KEYS.forEach((key) => next.delete(key));
    setParams(next, { replace: true });
  }

  // Typing in the department box narrows the dropdown as well as the results,
  // so a college with nineteen departments stays navigable.
  const departments = useMemo(() => {
    const all = facets?.departments ?? [];
    const needle = deptTerm.trim().toLowerCase();
    if (!needle) return all;
    return all.filter(
      (d) => d.label.toLowerCase().includes(needle) || d.code.toLowerCase().includes(needle),
    );
  }, [facets, deptTerm]);

  const option = (label: string, count: number) => `${label} (${count})`;

  /** Active filters, in the order the controls appear, for the chip row. */
  const active: { key: string; label: string; value: string }[] = [];
  const push = (key: string, label: string, value: string | undefined | null) => {
    if (value) active.push({ key, label, value });
  };

  push("q", "Search", params.get("q"));
  if (showDepartment) {
    push("deptq", "Department search", params.get("deptq"));
    const chosen = params.get("department");
    if (chosen === ALL_DEPARTMENTS) {
      push("department", "Department", "All departments");
    } else if (chosen) {
      push(
        "department",
        "Department",
        facets?.departments.find((d) => String(d.value) === chosen)?.label ?? chosen,
      );
    }
  }
  if (showSemester) {
    const semester = params.get("semester");
    if (semester) push("semester", "Semester", `Semester ${roman(Number(semester))}`);
  }
  const category = params.get("category");
  if (category) {
    const label = CATEGORY_LABELS[category as keyof typeof CATEGORY_LABELS];
    push("category", "Category", label ? `${category} — ${label}` : category);
  }
  const type = params.get("type");
  if (type) push("type", "Course type", COURSE_TYPES.find((c) => c.value === type)?.label ?? type);
  const credits = params.get("credits");
  if (credits) push("credits", "Credits", credits);

  return (
    <div className="stack-3">
      <form className="panel filterpanel" role="search" onSubmit={(e) => e.preventDefault()}>
        <div className="searchfield filterpanel__search">
          <span className="searchfield__icon">
            <SearchIcon width={17} height={17} />
          </span>
          <label htmlFor="subject-search" className="sr-only">
            Search subjects
          </label>
          <input
            id="subject-search"
            className="input"
            type="search"
            value={term}
            onChange={(e) => setTerm(e.target.value)}
            placeholder="Search by course code, title, department, semester or category..."
          />
        </div>

        <div className="filterpanel__controls">
          {showDepartment ? (
            <>
              <div className="field">
                <label htmlFor="f-deptq">Find a department</label>
                <input
                  id="f-deptq"
                  className="input"
                  type="search"
                  value={deptTerm}
                  onChange={(e) => setDeptTerm(e.target.value)}
                  placeholder="e.g. cyber, food, mech"
                />
              </div>

              <div className="field">
                <label htmlFor="f-department">Department</label>
                <select
                  id="f-department"
                  className="input"
                  value={params.get("department") ?? ""}
                  onChange={(e) => update("department", e.target.value)}
                >
                  <option value="">My department</option>
                  <option value={ALL_DEPARTMENTS}>All departments</option>
                  {departments.map((d) => (
                    <option key={d.value} value={String(d.value)}>
                      {option(d.label, d.count)}
                    </option>
                  ))}
                </select>
              </div>
            </>
          ) : null}

          {showSemester ? (
            <div className="field">
              <label htmlFor="f-semester">Semester</label>
              <select
                id="f-semester"
                className="input"
                value={params.get("semester") ?? ""}
                onChange={(e) => update("semester", e.target.value)}
              >
                <option value="">All semesters</option>
                {(facets?.semesters ?? []).map((s) => (
                  <option key={s.value} value={String(s.value)}>
                    {option(`Semester ${roman(s.value)}`, s.count)}
                  </option>
                ))}
              </select>
            </div>
          ) : null}

          <div className="field">
            <label htmlFor="f-category">Category</label>
            <select
              id="f-category"
              className="input"
              value={params.get("category") ?? ""}
              onChange={(e) => update("category", e.target.value)}
            >
              <option value="">All categories</option>
              {(facets?.categories ?? []).map((c) => (
                <option key={c.value} value={c.value}>
                  {option(`${c.value} — ${c.label}`, c.count)}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label htmlFor="f-type">Course type</label>
            <select
              id="f-type"
              className="input"
              value={params.get("type") ?? ""}
              onChange={(e) => update("type", e.target.value)}
            >
              <option value="">All course types</option>
              {(facets?.course_types ?? []).map((c) => (
                <option key={c.value} value={c.value}>
                  {option(c.label, c.count)}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label htmlFor="f-credits">Credits</label>
            <select
              id="f-credits"
              className="input"
              value={params.get("credits") ?? ""}
              onChange={(e) => update("credits", e.target.value)}
            >
              <option value="">Any credits</option>
              {(facets?.credits ?? []).map((c) => (
                <option key={c.value} value={String(c.value)}>
                  {option(`${c.value} credit${c.value === 1 ? "" : "s"}`, c.count)}
                </option>
              ))}
            </select>
          </div>
        </div>
      </form>

      {active.length ? (
        <div className="filterchips">
          <div className="filterchips__list">
            <span className="muted nowrap">Active filters</span>
            {active.map((chip) => (
              <FilterChip
                key={chip.key}
                label={chip.label}
                value={chip.value}
                onRemove={() => update(chip.key, "")}
              />
            ))}
          </div>
          <button type="button" className="btn btn--sm nowrap" onClick={clearAll}>
            Clear all filters
          </button>
        </div>
      ) : null}
    </div>
  );
}

/* ------------------------------------------------------------------ pages -- */
export function Dashboard() {
  const user = useSession((state) => state.user);
  const department = useDepartment((state) => state.selected);
  const departmentId = department?.id;
  useDocumentTitle(department?.name, "Dashboard");
  const { data, loading, error } = useAsync(
    async () => ({
      stats: await api.stats(departmentId),
      semesters: await api.semesters.list(departmentId),
      recent: await api.resources.recent(6, departmentId),
    }),
    [departmentId],
  );

  if (loading) return <Loading label="Loading your dashboard..." />;
  if (error || !data) return <Notice kind="crit">{error}</Notice>;

  const { stats, semesters, recent } = data as {
    stats: Stats;
    semesters: Semester[];
    recent: Resource[];
  };

  return (
    <>
      <PageHead
        eyebrow={department?.name ?? "Academic Resource Portal"}
        title={`Welcome back, ${user?.name.split(" ")[0] ?? "Student"}`}
        lead="Access your department's semester-wise subjects, academic notes and examination resources in one place."
        actions={
          <>
            <Link to="/semesters" className="btn">Semesters</Link>
            <Link to="/subjects" className="btn btn--primary">Browse Subjects</Link>
          </>
        }
      />

      <div className="grid grid-4 stack-8">
        <Stat value={stats.semesters} label="Semesters" icon={<LayersIcon />} />
        <Stat value={stats.subjects} label="Subjects" icon={<BookIcon />} />
        <Stat value={stats.resources} label="Available Resources" icon={<FileIcon />} />
        <Stat
          value={stats.exam_resources}
          label="Exam Resources"
          note="CAT 1, CAT 2 and semester exam"
          icon={<GridIcon />}
        />
      </div>

      <section className="stack-8">
        <SectionHead title="Your Semesters" detail="Select a semester to see its courses." />
        <div className="grid grid-4">
          {semesters.map((semester) => (
            <Link key={semester.id} to={`/semesters/${semester.id}`} className="subjectcard">
              <span className="label">Semester</span>
              <strong style={{ fontSize: "var(--fs-h3)" }}>{roman(semester.semester_number)}</strong>
              <span className="meta">
                {semester.subject_count} {semester.subject_count === 1 ? "subject" : "subjects"}
              </span>
            </Link>
          ))}
        </div>
      </section>

      <section className="stack-8">
        <SectionHead
          title="Recently Added Resources"
          detail="The latest material published by the department."
        />
        {recent.length === 0 ? (
          <EmptyState
            icon={<FileIcon />}
            title="No resources have been published yet"
            detail="Notes and examination material appear here as soon as an administrator uploads them."
          />
        ) : (
          <div className="grid grid-3">
            {recent.map((resource) => (
              <article key={resource.id} className="reccard">
                <span className="iconbadge iconbadge--signal" aria-hidden="true">
                  <FileIcon width={16} height={16} />
                </span>
                <div className="reccard__body">
                  <h3 className="reccard__title">{resource.title}</h3>
                  <p className="reccard__subject">
                    {resource.subject_code ? <b>{resource.subject_code} </b> : null}
                    {resource.subject_title}
                  </p>
                  <p className="meta">
                    <span className="chip">{resource.resource_type_label}</span>{" "}
                    Semester {roman(resource.semester_number)} · {formatDate(resource.created_at)}
                  </p>
                  <Link
                    to={`/subjects/${resource.subject}/resources/${RESOURCE_TYPE_SLUGS[resource.resource_type]}`}
                    className="btn btn--sm"
                    style={{ marginTop: "var(--s2)" }}
                  >
                    Open {resource.resource_type_label}
                  </Link>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </>
  );
}

export function Semesters() {
  const department = useDepartment((state) => state.selected);
  useDocumentTitle(department?.name, "Semesters");
  const { data, loading, error } = useAsync(
    () => api.semesters.list(department?.id),
    [department?.id],
  );

  if (loading) return <Loading label="Loading semesters..." />;
  if (error || !data) return <Notice kind="crit">{error}</Notice>;

  return (
    <>
      <PageHead
        eyebrow={department?.name ?? "Semesters"}
        title="Semesters"
        lead={
          data.length
            ? `${data.length} semester${data.length === 1 ? "" : "s"} in this department.`
            : undefined
        }
      />
      <div className="grid grid-4">
        {data.map((semester) => (
          <article key={semester.id} className="subjectcard">
            <span className="label">Semester</span>
            <h2 style={{ margin: 0, fontSize: "var(--fs-h3)" }}>
              <Link to={`/semesters/${semester.id}`}>{roman(semester.semester_number)}</Link>
            </h2>
            <p className="muted">
              <b className="tabular">{semester.subject_count}</b>{" "}
              {semester.subject_count === 1 ? "subject" : "subjects"}
            </p>
            <Link to={`/semesters/${semester.id}`} className="btn btn--sm">
              View Subjects
            </Link>
          </article>
        ))}
      </div>
    </>
  );
}

export function SemesterDetail() {
  const { semesterId } = useParams();
  const departmentId = useDepartment((state) => state.selected)?.id;
  const [params] = useSearchParams();
  const query = params.toString();

  const { data, loading, error } = useAsync(async () => {
    // The route fixes both the semester and, through it, the department — so
    // the semester and department filters are neither offered nor applied here.
    // Carrying a department over from a cross-department search would contradict
    // the semester in the URL and empty the page.
    const filters = {
      ...subjectQuery(params, departmentId),
      semester_number: undefined,
      department: undefined,
      department_search: undefined,
    };
    return {
      semester: await api.semesters.get(semesterId!),
      facets: await api.subjects.facets({ ...filters, semester: semesterId }),
      subjects: (await api.subjects.list({ ...filters, semester: semesterId })).results,
    };
  }, [semesterId, query, departmentId]);

  if (loading) return <Loading label="Loading subjects..." />;
  if (error || !data) return <Notice kind="crit">{error}</Notice>;

  return (
    <>
      <Breadcrumbs
        items={[
          { label: "Home", to: "/departments" },
          { label: data.semester.department_name, to: "/dashboard" },
          { label: `Semester ${roman(data.semester.semester_number)}` },
        ]}
      />
      <PageHead
        eyebrow="Semester"
        title={data.semester.name}
        lead={`${data.semester.subject_count} subject${data.semester.subject_count === 1 ? "" : "s"} in this semester.`}
      />
      <SubjectFilters facets={data.facets} showSemester={false} />
      <ResultCount matching={data.facets.count} of={data.semester.subject_count} noun="subject" />
      <SubjectSections
        subjects={data.subjects}
        // A semester can legitimately hold no courses — Food Technology's final
        // term carries only a project, which is outside this catalogue. Saying
        // "no match" there would blame the reader's search for an empty syllabus.
        empty={
          data.semester.subject_count === 0 ? (
            <EmptyState
              icon={<BookIcon />}
              title="No subjects listed for this semester"
              detail="The syllabus publishes no regular academic courses for this term."
            />
          ) : undefined
        }
      />
    </>
  );
}

/** How many courses the current filters match, out of how many are reachable. */
function ResultCount({ matching, of, noun }: { matching: number; of: number; noun: string }) {
  const plural = (n: number) => `${n} ${noun}${n === 1 ? "" : "s"}`;
  return (
    <p className="muted resultcount" role="status" aria-live="polite">
      {matching === of ? (
        <>Showing all {plural(of)}.</>
      ) : (
        <>
          <b className="tabular">{plural(matching)}</b> of {of} match the current filters.
        </>
      )}
    </p>
  );
}

export function Subjects() {
  const selectedDepartment = useDepartment((state) => state.selected);
  const departmentId = selectedDepartment?.id;
  const departmentName = selectedDepartment?.name;
  useDocumentTitle(departmentName, "Subjects");
  const [params] = useSearchParams();
  const query = params.toString();

  const { data, loading, error } = useAsync(async () => {
    const filters = subjectQuery(params, departmentId);
    return {
      // Facets are fetched with the same filters, so every option's count
      // describes the set the student is actually looking at.
      facets: await api.subjects.facets(filters),
      page: await api.subjects.list(filters),
    };
  }, [query, departmentId]);

  if (loading) return <Loading label="Loading subjects..." />;
  if (error || !data) return <Notice kind="crit">{error}</Notice>;

  // "Out of" means the catalogue the current department selection exposes —
  // the whole college when the student has widened it to all departments.
  const reachable = params.get("department") === ALL_DEPARTMENTS
    ? data.facets.total
    : (data.facets.departments.find((d) => String(d.value) === (params.get("department") ?? String(departmentId)))
        ?.total ?? data.facets.total);

  return (
    <>
      <PageHead
        eyebrow={departmentName ?? "Subjects"}
        title="Subjects"
        lead="Search and filter the subject catalogue — by department, semester, category, credits and course type."
      />
      <SubjectFilters facets={data.facets} showDepartment />
      <ResultCount matching={data.page.count} of={reachable} noun="subject" />
      <SubjectSections subjects={data.page.results} showSemester />
    </>
  );
}

export function SubjectDetail() {
  const { subjectId } = useParams();
  const { data, loading, error } = useAsync(
    async () => ({
      subject: await api.subjects.get(subjectId!),
      counts: await api.subjects.resourceCounts(subjectId!),
    }),
    [subjectId],
  );

  if (loading) return <Loading label="Loading subject..." />;
  if (error || !data) return <Notice kind="crit">{error}</Notice>;

  const { subject, counts } = data as { subject: Subject; counts: ResourceCounts };
  const total = Object.values(counts).reduce((sum, n) => sum + n, 0);
  const lab = subject.course_type === "LAB_ORIENTED_THEORY";

  /**
   * One card per resource category — eight of them, never merged into a single
   * list. An empty category renders as an inert dashed card with no link, so
   * there is no button that leads nowhere.
   */
  const card = (type: keyof ResourceCounts, kind: "unit" | "exam") => {
    const count = counts[type];
    const label = RESOURCE_TYPE_LABELS[type];
    const kindLabel = kind === "unit" ? "Notes" : "Exam Resources";
    const to = `/subjects/${subject.id}/resources/${RESOURCE_TYPE_SLUGS[type]}`;

    if (count === 0) {
      return (
        <article key={type} className={`rescard rescard--empty rescard--${kind}`}>
          <div className="rescard__head">
            <div>
              <h3>{label}</h3>
              <p className="rescard__kind">{kindLabel}</p>
            </div>
            <span className="iconbadge" aria-hidden="true">
              <FileIcon width={15} height={15} />
            </span>
          </div>
          <p className="muted" style={{ margin: "var(--s2) 0 0" }}>No resources available yet.</p>
          <p className="meta">Please check again later.</p>
        </article>
      );
    }

    return (
      <article key={type} className={`rescard rescard--${kind}`}>
        <div className="rescard__head">
          <div>
            <h3>
              <Link to={to}>{label}</Link>
            </h3>
            <p className="rescard__kind">{kindLabel}</p>
          </div>
          <span
            className={kind === "unit" ? "iconbadge iconbadge--signal" : "iconbadge iconbadge--data"}
            aria-hidden="true"
          >
            <FileIcon width={15} height={15} />
          </span>
        </div>
        <p className="rescard__count tabular">
          {count} {count === 1 ? "Resource" : "Resources"}
        </p>
        <p className="rescard__go" aria-hidden="true">
          View &rarr;
        </p>
      </article>
    );
  };

  return (
    <>
      <Link to={`/semesters/${subject.semester}`} className="backlink">
        <ArrowLeftIcon width={15} height={15} aria-hidden="true" />
        Back to Semester {roman(subject.semester_number)}
      </Link>

      <Breadcrumbs
        items={[
          { label: "Home", to: "/departments" },
          { label: subject.department_code, to: "/dashboard" },
          { label: `Semester ${roman(subject.semester_number)}`, to: `/semesters/${subject.semester}` },
          { label: subject.course_code ?? subject.course_title },
        ]}
      />

      <section className="panel stack-8">
        <div className="row row--between row--top">
          <div>
            {subject.course_code ? (
              <p className="subjectcard__code" style={{ fontSize: "var(--fs-lead)" }}>
                {subject.course_code}
              </p>
            ) : (
              <p className="muted"><i>Course code: Not specified</i></p>
            )}
            <h1 style={{ margin: "4px 0 0" }}>{subject.course_title}</h1>
            <div className="row row--tight" style={{ marginTop: 8 }}>
              <span className={lab ? "chip chip--data" : "chip chip--signal"}>
                {subject.course_type_label}
              </span>
              <span className="chip">
                {subject.category} — {subject.category_label}
              </span>
              <span className="meta">Semester {roman(subject.semester_number)}</span>
            </div>
          </div>
          <div style={{ textAlign: "right" }}>
            <p className="label">Published resources</p>
            <p className="readout__value tabular">{total}</p>
          </div>
        </div>

        <dl className="factgrid">
          <Fact label="Course Code" value={subject.course_code ?? "Not specified"} />
          <Fact label="Category" value={subject.category} />
          <Fact label="Theory (L)" value={subject.l} />
          <Fact label="Tutorial (T)" value={subject.t} />
          <Fact label="Practical (P)" value={subject.p} />
          {/* Credits are emphasised: they feed GPA/CGPA. */}
          <Fact label="Credits (C)" value={subject.credits} emphasis />
        </dl>
      </section>

      <section className="stack-8">
        <SectionHead title="Academic Materials" detail="Unit-wise notes and reference material." />
        <div className="grid grid-4">{LEARNING_TYPES.map((type) => card(type, "unit"))}</div>
      </section>

      <section className="stack-8">
        <SectionHead
          title="Examination Resources"
          detail="Question papers, study material and important material."
        />
        <div className="grid grid-3">{EXAM_TYPES.map((type) => card(type, "exam"))}</div>
      </section>
    </>
  );
}

export function ResourceCategory() {
  const { subjectId, resourceType } = useParams();
  const toast = useUi((state) => state.toast);
  const type = resourceTypeFromSlug(resourceType ?? "");

  const { data, loading, error } = useAsync(
    async () => ({
      subject: await api.subjects.get(subjectId!),
      resources: type
        ? (await api.resources.list({ subject: subjectId, resource_type: type })).results
        : [],
    }),
    [subjectId, resourceType],
  );

  if (!type) return <Notice kind="crit">Unknown resource category.</Notice>;
  if (loading) return <Loading label="Loading resources..." />;
  if (error || !data) return <Notice kind="crit">{error}</Notice>;

  const label = RESOURCE_TYPE_LABELS[type];

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
    <>
      <Breadcrumbs
        items={[
          { label: "Home", to: "/departments" },
          { label: data.subject.department_code, to: "/dashboard" },
          { label: data.subject.course_code ?? data.subject.course_title, to: `/subjects/${data.subject.id}` },
          { label },
        ]}
      />
      <PageHead
        eyebrow={`${data.subject.course_code ? `${data.subject.course_code} · ` : ""}${data.subject.course_title}`}
        title={`${label} Resources`}
        actions={<Link to={`/subjects/${data.subject.id}`} className="btn">Back to subject</Link>}
      />

      {data.resources.length === 0 ? (
        <EmptyState
          icon={<FileIcon />}
          title={`No resources have been uploaded for ${label} yet.`}
          detail="Please check again later — material appears here as soon as the department publishes it."
        />
      ) : (
        <ul className="stack-3" style={{ listStyle: "none", padding: 0 }}>
          {data.resources.map((resource) => (
            <li key={resource.id}>
              <article className="panel row row--between row--top">
                <div>
                  <h3 style={{ margin: 0 }}>{resource.title}</h3>
                  {resource.description ? <p className="muted">{resource.description}</p> : null}
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
                        <button type="button" className="btn btn--sm" onClick={() => void preview(resource)}>
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
      )}
    </>
  );
}

export function Profile() {
  const user = useSession((state) => state.user);
  const department = useDepartment((state) => state.selected);
  useDocumentTitle(department?.name, "Profile");
  if (!user) return null;

  return (
    <>
      <PageHead eyebrow="Account" title="Profile" lead="Your account details for the portal." />
      <section className="panel" style={{ maxWidth: "48rem" }}>
        <dl className="factgrid">
          <Fact label="Name" value={user.name} />
          <Fact label="Email" value={user.email} />
          <Fact label="Role" value="Student" />
          <Fact label="Department" value={department?.name ?? user.department_name ?? "Not selected"} />
          <Fact label="Institution" value="Rajalakshmi Engineering College" />
          <Fact label="Member since" value={formatDate(user.created_at)} />
        </dl>
        <div className="row row--between" style={{ marginTop: "var(--s5)" }}>
          <p className="muted" style={{ margin: 0 }}>
            Students have read-only access to published academic resources.
          </p>
          <LogoutButton variant="student" className="btn" />
        </div>
      </section>
    </>
  );
}
