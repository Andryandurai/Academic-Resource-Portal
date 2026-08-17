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
  GridIcon,
  LayersIcon,
  SearchIcon,
} from "../../components/Icons";
import { LogoutButton } from "../../components/LogoutButton";
import { api } from "../../services/api";
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

/** Search and filters drive the URL; filtering itself happens in the database. */
function SubjectFilters({ semesters, showSemester = true }: { semesters: Semester[]; showSemester?: boolean }) {
  const [params, setParams] = useSearchParams();
  const [term, setTerm] = useState(params.get("q") ?? "");

  useEffect(() => {
    setTerm(params.get("q") ?? "");
  }, [params]);

  useEffect(() => {
    const current = params.get("q") ?? "";
    if (term === current) return;
    const timer = window.setTimeout(() => update("q", term), 250);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [term]);

  function update(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next, { replace: true });
  }

  const hasFilters = ["q", "semester", "type", "category"].some((key) => params.get(key));

  return (
    <form className="panel filterbar" role="search" onSubmit={(e) => e.preventDefault()}>
      <div className="searchfield">
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
          placeholder="Search subjects by course code or subject name..."
        />
      </div>

      {showSemester ? (
        <>
          <label htmlFor="f-semester" className="sr-only">Filter by semester</label>
          <select
            id="f-semester"
            className="input"
            value={params.get("semester") ?? ""}
            onChange={(e) => update("semester", e.target.value)}
          >
            <option value="">All semesters</option>
            {semesters.map((s) => (
              <option key={s.id} value={String(s.semester_number)}>
                Semester {roman(s.semester_number)}
              </option>
            ))}
          </select>
        </>
      ) : null}

      <label htmlFor="f-type" className="sr-only">Filter by course type</label>
      <select
        id="f-type"
        className="input"
        value={params.get("type") ?? ""}
        onChange={(e) => update("type", e.target.value)}
      >
        <option value="">All course types</option>
        {COURSE_TYPES.map((c) => (
          <option key={c.value} value={c.value}>{c.label}</option>
        ))}
      </select>

      <label htmlFor="f-category" className="sr-only">Filter by category</label>
      <select
        id="f-category"
        className="input"
        value={params.get("category") ?? ""}
        onChange={(e) => update("category", e.target.value)}
      >
        <option value="">All categories</option>
        {Object.entries(CATEGORY_LABELS).map(([code, label]) => (
          <option key={code} value={code}>
            {code} — {label}
          </option>
        ))}
      </select>

      <button
        type="button"
        className="btn"
        disabled={!hasFilters}
        onClick={() => setParams(new URLSearchParams(), { replace: true })}
      >
        Clear
      </button>
    </form>
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

  const { data, loading, error } = useAsync(
    async () => ({
      semester: await api.semesters.get(semesterId!),
      semesters: await api.semesters.list(departmentId),
      subjects: (
        await api.subjects.list({
          department: departmentId,
          semester: semesterId,
          search: params.get("q") ?? undefined,
          course_type: params.get("type") ?? undefined,
          category: params.get("category") ?? undefined,
        })
      ).results,
    }),
    [semesterId, query],
  );

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
      <SubjectFilters semesters={data.semesters} showSemester={false} />
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

export function Subjects() {
  const selectedDepartment = useDepartment((state) => state.selected);
  const departmentId = selectedDepartment?.id;
  const departmentName = selectedDepartment?.name;
  useDocumentTitle(departmentName, "Subjects");
  const [params] = useSearchParams();
  const query = params.toString();

  const { data, loading, error } = useAsync(
    async () => ({
      semesters: await api.semesters.list(departmentId),
      page: await api.subjects.list({
        department: departmentId,
        search: params.get("q") ?? undefined,
        semester_number: params.get("semester") ?? undefined,
        course_type: params.get("type") ?? undefined,
        category: params.get("category") ?? undefined,
      }),
    }),
    [query],
  );

  const total = useMemo(
    () => data?.semesters.reduce((sum, s) => sum + s.subject_count, 0) ?? 0,
    [data],
  );

  if (loading) return <Loading label="Loading subjects..." />;
  if (error || !data) return <Notice kind="crit">{error}</Notice>;

  const filtered = Boolean(query);

  return (
    <>
      <PageHead
        eyebrow={departmentName ?? "Subjects"}
        title="Subjects"
        lead="Search and filter your department's subject catalogue."
      />
      <SubjectFilters semesters={data.semesters} />
      <p className="muted" role="status" aria-live="polite">
        {filtered
          ? `${data.page.count} of ${total} subjects match your filters.`
          : `Showing all ${total} subjects.`}
      </p>
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
                    <span className="chip">{resource.file_type_label}</span>{" "}
                    {formatBytes(resource.file_size)} · Uploaded {formatDate(resource.created_at)}
                    {resource.uploaded_by_name ? ` · By ${resource.uploaded_by_name}` : ""} ·{" "}
                    {resource.file_name}
                  </p>
                </div>
                <div className="row row--tight">
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
