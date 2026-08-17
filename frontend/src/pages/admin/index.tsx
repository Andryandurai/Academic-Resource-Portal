import { useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";

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
  BookIcon,
  DownloadIcon,
  FileIcon,
  GridIcon,
  PencilIcon,
  PlusIcon,
  TrashIcon,
  UploadIcon,
  UsersIcon,
} from "../../components/Icons";
import { api } from "../../services/api";
import { ApiError } from "../../services/client";
import { useSession } from "../../stores/session";
import { useUi } from "../../stores/ui";
import {
  CATEGORY_LABELS,
  COURSE_TYPES,
  RESOURCE_TYPES,
  RESOURCE_TYPE_LABELS,
  roman,
  type Resource,
  type Semester,
  type Stats,
  type Department,
  type Subject,
  type UserRow,
} from "../../types";

function useLoad<T>(loader: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    loader()
      .then((result) => !cancelled && setData(result))
      .catch((caught) =>
        !cancelled && setError(caught instanceof ApiError ? caught.message : "Could not load."),
      )
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  return { data, error, loading, reload: () => setTick((n) => n + 1) };
}

/* ------------------------------------------------------------------------- */
export function AdminDashboard() {
  const { data, loading, error } = useLoad(
    async () => ({ stats: await api.stats(), recent: await api.resources.recent(8) }),
    [],
  );

  if (loading) return <Loading />;
  if (error || !data) return <Notice kind="crit">{error}</Notice>;

  const stats = data.stats as Stats;

  return (
    <>
      <PageHead
        eyebrow="Administration"
        title="Dashboard"
        lead="Manage the college's subject catalogue and the resources published to students."
        actions={
          <>
            <Link to="/admin/subjects/new" className="btn"><PlusIcon width={15} height={15} /> Add Subject</Link>
            <Link to="/admin/resources/new" className="btn btn--primary"><UploadIcon width={15} height={15} /> Add Resource</Link>
          </>
        }
      />

      <div className="grid grid-4 stack-8">
        <Stat value={stats.subjects} label="Total Subjects" icon={<BookIcon />} />
        <Stat value={stats.resources} label="Total Resources" icon={<FileIcon />} />
        <Stat value={stats.students ?? 0} label="Total Students" icon={<UsersIcon />} />
        <Stat
          value={stats.exam_resources}
          label="Exam Resources"
          note={`${stats.uploaded_this_month ?? 0} uploaded this month`}
          icon={<GridIcon />}
        />
      </div>

      <section className="stack-8">
        <SectionHead title="Quick Actions" />
        <div className="grid grid-3">
          {[
            {
              to: "/admin/subjects/new",
              icon: <PlusIcon width={18} height={18} />,
              title: "Add Subject",
              sub: "Add a course to a department catalogue",
            },
            {
              to: "/admin/resources/new",
              icon: <UploadIcon width={18} height={18} />,
              title: "Upload Resource",
              sub: "Publish notes or examination material",
            },
            {
              to: "/admin/resources",
              icon: <FileIcon width={18} height={18} />,
              title: "Manage Resources",
              sub: "Edit, replace or delete published files",
            },
          ].map((action) => (
            <Link key={action.to} to={action.to} className="quickcard">
              <span className="iconbadge iconbadge--signal" aria-hidden="true">
                {action.icon}
              </span>
              <span>
                <span className="quickcard__title">{action.title}</span>
                <span className="quickcard__sub">{action.sub}</span>
              </span>
            </Link>
          ))}
        </div>
      </section>

      <section>
        <SectionHead
          title="Recent Uploads"
          action={<Link to="/admin/resources" className="btn btn--sm">View all resources</Link>}
        />
        {data.recent.length === 0 ? (
          <EmptyState
            title="No resources found."
            detail="Nothing has been published yet. Upload the first unit notes or examination material."
            action={<Link to="/admin/resources/new" className="btn btn--primary">Add Resource</Link>}
          />
        ) : (
          <div className="scroll-x">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">Subject</th>
                  <th scope="col">Resource</th>
                  <th scope="col">Category</th>
                  <th scope="col">Uploaded</th>
                  <th scope="col">By</th>
                  <th scope="col"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody>
                {data.recent.map((resource) => (
                  <tr key={resource.id}>
                    <td>
                      {resource.subject_code ? <b>{resource.subject_code} </b> : null}
                      {resource.subject_title}
                      <div className="meta">Semester {roman(resource.semester_number)}</div>
                    </td>
                    <td>{resource.title}</td>
                    <td><span className="chip">{resource.resource_type_label}</span></td>
                    <td className="nowrap">{formatDate(resource.created_at)}</td>
                    <td>{resource.uploaded_by_name ?? "—"}</td>
                    <td className="actions">
                      <Link to={`/admin/resources/${resource.id}/edit`} className="btn btn--sm">Manage</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}

/* ------------------------------------------------------------------------- */
export function AdminSubjects() {
  const toast = useUi((state) => state.toast);
  const [params, setParams] = useSearchParams();
  const query = params.toString();

  const { data, loading, error, reload } = useLoad(
    async () => ({
      semesters: await api.semesters.list(),
      page: await api.subjects.list({
        search: params.get("q") ?? undefined,
        semester_number: params.get("semester") ?? undefined,
      }),
    }),
    [query],
  );

  async function remove(subject: Subject) {
    const label = `${subject.course_code ? `${subject.course_code} — ` : ""}${subject.course_title}`;
    if (!window.confirm(`Delete "${label}"? This action cannot be undone.`)) return;
    try {
      await api.subjects.remove(subject.id);
      toast(`Subject "${subject.course_title}" deleted.`, "ok");
      reload();
    } catch (caught) {
      // A 409 means the subject still holds resources — the server refuses to
      // destroy uploaded material as a side effect.
      toast(caught instanceof ApiError ? caught.message : "Could not delete.", "crit");
    }
  }

  if (loading) return <Loading />;
  if (error || !data) return <Notice kind="crit">{error}</Notice>;

  return (
    <>
      <PageHead
        eyebrow="Administration"
        title="Subject Management"
        lead="View, search and maintain the subject catalogue across departments."
        actions={<Link to="/admin/subjects/new" className="btn btn--primary"><PlusIcon width={15} height={15} /> Add Subject</Link>}
      />

      <form className="panel row row--tight" role="search" onSubmit={(e) => e.preventDefault()}>
        <input
          className="input"
          type="search"
          placeholder="Search by course code or subject name..."
          defaultValue={params.get("q") ?? ""}
          onChange={(e) => {
            const next = new URLSearchParams(params);
            if (e.target.value) next.set("q", e.target.value);
            else next.delete("q");
            setParams(next, { replace: true });
          }}
          aria-label="Search subjects"
        />
        <select
          className="input"
          value={params.get("semester") ?? ""}
          onChange={(e) => {
            const next = new URLSearchParams(params);
            if (e.target.value) next.set("semester", e.target.value);
            else next.delete("semester");
            setParams(next, { replace: true });
          }}
          aria-label="Filter by semester"
        >
          <option value="">All semesters</option>
          {data.semesters.map((s: Semester) => (
            <option key={s.id} value={String(s.semester_number)}>Semester {roman(s.semester_number)}</option>
          ))}
        </select>
      </form>

      <div className="scroll-x">
        <table className="table">
          <thead>
            <tr>
              <th scope="col">Course Code</th>
              <th scope="col">Subject</th>
              <th scope="col">Semester</th>
              <th scope="col">Category</th>
              <th scope="col">Course Type</th>
              <th scope="col">L</th>
              <th scope="col">T</th>
              <th scope="col">P</th>
              <th scope="col">Credits</th>
              <th scope="col">Actions</th>
            </tr>
          </thead>
          <tbody>
            {data.page.results.map((subject: Subject) => (
              <tr key={subject.id}>
                <td className="nowrap">
                  {subject.course_code ? <b>{subject.course_code}</b> : <i className="meta">Not specified</i>}
                </td>
                <td>{subject.course_title}</td>
                <td className="nowrap">{roman(subject.semester_number)}</td>
                <td><span className="chip">{subject.category}</span></td>
                <td className="nowrap meta">{subject.course_type_label}</td>
                <td className="tabular">{subject.l}</td>
                <td className="tabular">{subject.t}</td>
                <td className="tabular">{subject.p}</td>
                <td className="tabular"><b>{subject.credits}</b></td>
                <td className="actions">
                  <Link to={`/admin/subjects/${subject.id}/edit`} className="btn btn--sm">
                    <PencilIcon width={15} height={15} />
                    <span className="sr-only">Edit {subject.course_title}</span>
                  </Link>
                  <button type="button" className="btn btn--sm btn--danger" onClick={() => void remove(subject)}>
                    <TrashIcon width={15} height={15} />
                    <span className="sr-only">Delete {subject.course_title}</span>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

/* ------------------------------------------------------------------------- */
const EMPTY_SUBJECT = {
  semester: "",
  course_code: "",
  course_title: "",
  category: "",
  course_type: "",
  l: "0",
  t: "0",
  p: "0",
  credits: "0",
};

export function AdminSubjectForm() {
  const { subjectId } = useParams();
  const editing = Boolean(subjectId);
  const navigate = useNavigate();
  const toast = useUi((state) => state.toast);

  const [form, setForm] = useState<Record<string, string>>(EMPTY_SUBJECT);
  const [semesters, setSemesters] = useState<Semester[]>([]);
  const [fields, setFields] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    void (async () => {
      setSemesters(await api.semesters.list());
      if (subjectId) {
        const subject = await api.subjects.get(subjectId);
        setForm({
          semester: String(subject.semester),
          course_code: subject.course_code ?? "",
          course_title: subject.course_title,
          category: subject.category,
          course_type: subject.course_type,
          l: String(subject.l),
          t: String(subject.t),
          p: String(subject.p),
          credits: String(subject.credits),
        });
      }
    })();
  }, [subjectId]);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);
    setFields({});

    const body = {
      semester: Number(form.semester),
      // Empty means "no published code" and is stored as NULL — never invented.
      course_code: form.course_code.trim() || null,
      course_title: form.course_title,
      category: form.category,
      course_type: form.course_type,
      l: Number(form.l),
      t: Number(form.t),
      p: Number(form.p),
      credits: Number(form.credits),
    };

    try {
      if (editing) await api.subjects.update(subjectId!, body);
      else await api.subjects.create(body);
      toast(editing ? "Subject updated." : "Subject created.", "ok");
      navigate("/admin/subjects");
    } catch (caught) {
      if (caught instanceof ApiError) {
        setError(caught.message);
        setFields(caught.fields);
      } else setError("Could not save the subject.");
    } finally {
      setPending(false);
    }
  }

  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm({ ...form, [key]: e.target.value });

  return (
    <>
      <Breadcrumbs
        items={[
          { label: "Dashboard", to: "/admin" },
          { label: "Subjects", to: "/admin/subjects" },
          { label: editing ? "Edit Subject" : "Add Subject" },
        ]}
      />
      <PageHead eyebrow="Subject Management" title={editing ? "Edit Subject" : "Add Subject"} />

      <form className="panel stack-4" style={{ maxWidth: "48rem" }} onSubmit={onSubmit} noValidate>
        {error ? <Notice kind="crit">{error}</Notice> : null}

        <div className="grid grid-2">
          <div className="field">
            <label htmlFor="semester">Semester</label>
            <select id="semester" className="input" value={form.semester} onChange={set("semester")} required>
              <option value="">Select a semester</option>
              {semesters.map((s) => (
                <option key={s.id} value={String(s.id)}>Semester {roman(s.semester_number)}</option>
              ))}
            </select>
            {fields.semester ? <p className="meta">{fields.semester}</p> : null}
          </div>

          <div className="field">
            <label htmlFor="course_code">Course code</label>
            <input id="course_code" className="input" value={form.course_code} onChange={set("course_code")} placeholder="e.g. CS23231" />
            <p className="meta">
              Leave blank for an elective with no published code — a code is never invented.
            </p>
            {fields.course_code ? <p className="meta">{fields.course_code}</p> : null}
          </div>
        </div>

        <div className="field">
          <label htmlFor="course_title">Course title</label>
          <input id="course_title" className="input" value={form.course_title} onChange={set("course_title")} required />
          {fields.course_title ? <p className="meta">{fields.course_title}</p> : null}
        </div>

        <div className="grid grid-2">
          <div className="field">
            <label htmlFor="category">Category</label>
            <select id="category" className="input" value={form.category} onChange={set("category")} required>
              <option value="">Select a category</option>
              {Object.entries(CATEGORY_LABELS).map(([code, label]) => (
                <option key={code} value={code}>{code} — {label}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="course_type">Course type</label>
            <select id="course_type" className="input" value={form.course_type} onChange={set("course_type")} required>
              <option value="">Select a course type</option>
              {COURSE_TYPES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
        </div>

        <fieldset className="stack-2">
          <legend className="label">Periods and credits</legend>
          <div className="grid grid-4">
            {(["l", "t", "p", "credits"] as const).map((key) => (
              <div className="field" key={key}>
                <label htmlFor={key}>
                  {key === "credits" ? "Credits (C)" : `${key.toUpperCase()}`}
                </label>
                <input id={key} className="input" type="number" min={0} value={form[key]} onChange={set(key)} required />
                {fields[key] ? <p className="meta">{fields[key]}</p> : null}
              </div>
            ))}
          </div>
          <p className="meta">Credits are stored for GPA/CGPA and must match the published syllabus.</p>
        </fieldset>

        <div className="row row--end row--tight">
          <Link to="/admin/subjects" className="btn">Cancel</Link>
          <button type="submit" className="btn btn--primary" disabled={pending}>
            {pending ? "Saving..." : editing ? "Save Changes" : "Create Subject"}
          </button>
        </div>
      </form>
    </>
  );
}

/* ------------------------------------------------------------------------- */
export function AdminResources() {
  const toast = useUi((state) => state.toast);
  const [params, setParams] = useSearchParams();
  const query = params.toString();

  const { data, loading, error, reload } = useLoad(
    async () => ({
      semesters: await api.semesters.list(),
      page: await api.resources.list({
        search: params.get("q") ?? undefined,
        semester: params.get("semester") ?? undefined,
        resource_type: params.get("type") ?? undefined,
        uploaded_from: params.get("from") ?? undefined,
        uploaded_to: params.get("to") ?? undefined,
      }),
    }),
    [query],
  );

  async function remove(resource: Resource) {
    if (
      !window.confirm(
        `Are you sure you want to delete "${resource.title}"? This action cannot be undone.`,
      )
    )
      return;
    try {
      await api.resources.remove(resource.id);
      toast(`"${resource.title}" deleted.`, "ok");
      reload();
    } catch (caught) {
      toast(caught instanceof ApiError ? caught.message : "Could not delete.", "crit");
    }
  }

  function update(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next, { replace: true });
  }

  if (loading) return <Loading />;
  if (error || !data) return <Notice kind="crit">{error}</Notice>;

  return (
    <>
      <PageHead
        eyebrow="Administration"
        title="Resources"
        lead="Every file published to students, across all semesters and subjects."
        actions={<Link to="/admin/resources/new" className="btn btn--primary"><PlusIcon width={15} height={15} /> Add Resource</Link>}
      />

      <form className="panel filterbar" role="search" onSubmit={(e) => e.preventDefault()}>
        <input
          className="input"
          type="search"
          placeholder="Search by resource title, course code or subject..."
          defaultValue={params.get("q") ?? ""}
          onChange={(e) => update("q", e.target.value)}
          aria-label="Search resources"
        />
        <select className="input" value={params.get("semester") ?? ""} onChange={(e) => update("semester", e.target.value)} aria-label="Filter by semester">
          <option value="">All semesters</option>
          {data.semesters.map((s: Semester) => (
            <option key={s.id} value={String(s.id)}>Semester {roman(s.semester_number)}</option>
          ))}
        </select>
        <select className="input" value={params.get("type") ?? ""} onChange={(e) => update("type", e.target.value)} aria-label="Filter by category">
          <option value="">All categories</option>
          {RESOURCE_TYPES.map((type) => (
            <option key={type} value={type}>{RESOURCE_TYPE_LABELS[type]}</option>
          ))}
        </select>
        <input className="input" type="date" value={params.get("from") ?? ""} onChange={(e) => update("from", e.target.value)} aria-label="Uploaded from" />
        <input className="input" type="date" value={params.get("to") ?? ""} onChange={(e) => update("to", e.target.value)} aria-label="Uploaded to" />
      </form>

      {data.page.results.length === 0 ? (
        <EmptyState
          title="No resources found."
          detail="Nothing matches the current filters."
          action={<Link to="/admin/resources/new" className="btn btn--primary">Add Resource</Link>}
        />
      ) : (
        <div className="scroll-x">
          <table className="table">
            <thead>
              <tr>
                <th scope="col">Resource</th>
                <th scope="col">Subject</th>
                <th scope="col">Semester</th>
                <th scope="col">Category</th>
                <th scope="col">File Type</th>
                <th scope="col">Uploaded Date</th>
                <th scope="col">Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.page.results.map((resource: Resource) => (
                <tr key={resource.id}>
                  <td>
                    {resource.title}
                    <div className="meta">{resource.file_name} · {formatBytes(resource.file_size)}</div>
                  </td>
                  <td>
                    {resource.subject_code ? <b>{resource.subject_code} </b> : null}
                    {resource.subject_title}
                  </td>
                  <td className="nowrap">{roman(resource.semester_number)}</td>
                  <td><span className="chip">{resource.resource_type_label}</span></td>
                  <td className="nowrap meta">{resource.file_type_label}</td>
                  <td className="nowrap">{formatDate(resource.created_at)}</td>
                  <td className="actions">
                    <button
                      type="button"
                      className="btn btn--sm"
                      onClick={() => void api.resources.download(resource.id, resource.file_name)}
                    >
                      <DownloadIcon width={15} height={15} />
                      <span className="sr-only">Download {resource.title}</span>
                    </button>
                    <Link to={`/admin/resources/${resource.id}/edit`} className="btn btn--sm">
                      <PencilIcon width={15} height={15} />
                      <span className="sr-only">Edit or replace {resource.title}</span>
                    </Link>
                    <button type="button" className="btn btn--sm btn--danger" onClick={() => void remove(resource)}>
                      <TrashIcon width={15} height={15} />
                      <span className="sr-only">Delete {resource.title}</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

/* ------------------------------------------------------------------------- */
export function AdminResourceForm() {
  const { resourceId } = useParams();
  const editing = Boolean(resourceId);
  const navigate = useNavigate();
  const toast = useUi((state) => state.toast);

  const [departments, setDepartments] = useState<Department[]>([]);
  const [departmentId, setDepartmentId] = useState("");
  const [semesters, setSemesters] = useState<Semester[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [semesterId, setSemesterId] = useState("");
  const [form, setForm] = useState({ subject: "", resource_type: "", title: "", description: "" });
  const [file, setFile] = useState<File | null>(null);
  const [current, setCurrent] = useState<Resource | null>(null);
  const [fields, setFields] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    void (async () => {
      setDepartments(await api.departments.list());
      if (resourceId) {
        const resource = await api.resources.get(resourceId);
        setCurrent(resource);
        const semester = await api.semesters.get(resource.semester_id);
        setDepartmentId(String(semester.department));
        setSemesterId(String(resource.semester_id));
        setForm({
          subject: String(resource.subject),
          resource_type: resource.resource_type,
          title: resource.title,
          description: resource.description,
        });
      }
    })();
  }, [resourceId]);

  // Department → Semester → Subject → Category → File → Publish. Each step
  // narrows the next, and every list comes from the API for the chosen parent,
  // so a department added later works here with no code change.
  useEffect(() => {
    if (!departmentId) {
      setSemesters([]);
      return;
    }
    void api.semesters.list(departmentId).then(setSemesters);
  }, [departmentId]);

  useEffect(() => {
    if (!semesterId) {
      setSubjects([]);
      return;
    }
    void api.subjects.list({ semester: semesterId }).then((page) => setSubjects(page.results));
  }, [semesterId]);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);
    setFields({});

    const body = new FormData();
    body.append("subject", form.subject);
    body.append("resource_type", form.resource_type);
    body.append("title", form.title);
    body.append("description", form.description);
    if (file) body.append("file", file);

    try {
      if (editing) await api.resources.update(resourceId!, body);
      else await api.resources.create(body);
      toast(editing ? "Resource updated." : "Resource uploaded successfully.", "ok");
      navigate("/admin/resources");
    } catch (caught) {
      if (caught instanceof ApiError) {
        setError(caught.message);
        setFields(caught.fields);
      } else setError("Could not save the resource.");
    } finally {
      setPending(false);
    }
  }

  return (
    <>
      <Breadcrumbs
        items={[
          { label: "Dashboard", to: "/admin" },
          { label: "Resources", to: "/admin/resources" },
          { label: editing ? "Edit Resource" : "Upload Resource" },
        ]}
      />
      <PageHead
        eyebrow="Resource Management"
        title={editing ? "Edit Resource" : "Upload Resource"}
        lead="Select a semester and subject, choose the category, then upload the file and publish."
      />

      <form className="panel stack-4" style={{ maxWidth: "48rem" }} onSubmit={onSubmit} noValidate>
        {error ? <Notice kind="crit">{error}</Notice> : null}

        <div className="field">
          <label htmlFor="department">Department</label>
          <select
            id="department"
            className="input"
            value={departmentId}
            onChange={(e) => {
              setDepartmentId(e.target.value);
              setSemesterId("");
              setForm({ ...form, subject: "" });
            }}
            required
          >
            <option value="">Select a department</option>
            {departments.map((d) => (
              <option key={d.id} value={String(d.id)} disabled={!d.has_curriculum}>
                {d.name}
                {d.has_curriculum ? "" : " — curriculum not added yet"}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-2">
          <div className="field">
            <label htmlFor="semester">Semester</label>
            <select
              id="semester"
              className="input"
              value={semesterId}
              onChange={(e) => {
                setSemesterId(e.target.value);
                setForm({ ...form, subject: "" });
              }}
              disabled={!departmentId}
              required
            >
              <option value="">
                {departmentId ? "Select a semester" : "Select a department first"}
              </option>
              {semesters.map((s) => (
                <option key={s.id} value={String(s.id)}>
                  Semester {roman(s.semester_number)} ({s.subject_count} subjects)
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label htmlFor="subject">Subject</label>
            <select
              id="subject"
              className="input"
              value={form.subject}
              onChange={(e) => setForm({ ...form, subject: e.target.value })}
              disabled={!semesterId}
              required
            >
              <option value="">
                {!semesterId
                  ? "Select a semester first"
                  : // A semester can hold no courses at all — Food Technology's
                    // final term is project-only. Say so rather than offer an
                    // empty "Select a subject" the administrator cannot satisfy.
                    subjects.length === 0
                    ? "No subjects in this semester"
                    : "Select a subject"}
              </option>
              {subjects.map((subject) => (
                <option key={subject.id} value={String(subject.id)}>
                  {subject.course_code ? `${subject.course_code} — ` : ""}
                  {subject.course_title}
                </option>
              ))}
            </select>
            {fields.subject ? <p className="meta">{fields.subject}</p> : null}
          </div>
        </div>

        <div className="field">
          <label htmlFor="resource_type">Resource type</label>
          <select
            id="resource_type"
            className="input"
            value={form.resource_type}
            onChange={(e) => setForm({ ...form, resource_type: e.target.value })}
            required
          >
            <option value="">Select a resource category</option>
            {RESOURCE_TYPES.map((type) => (
              <option key={type} value={type}>{RESOURCE_TYPE_LABELS[type]}</option>
            ))}
          </select>
          {fields.resource_type ? <p className="meta">{fields.resource_type}</p> : null}
        </div>

        <div className="field">
          <label htmlFor="title">Resource title</label>
          <input
            id="title"
            className="input"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            placeholder="e.g. Unit 1 Complete Notes"
            required
          />
          {fields.title ? <p className="meta">{fields.title}</p> : null}
        </div>

        <div className="field">
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            className="textarea"
            rows={3}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="Optional. A short note about what this file contains."
          />
        </div>

        <div className="field">
          <label htmlFor="file">{editing ? "Replace file" : "Upload file"}</label>
          {current ? (
            <p className="meta">
              Current file: {current.file_name} · {formatBytes(current.file_size)}
            </p>
          ) : null}
          <input
            id="file"
            className="input"
            type="file"
            accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            required={!editing}
          />
          <p className="meta">
            PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX
            {editing ? " · leave empty to keep the current file" : ""}
          </p>
          {fields.file ? <p className="meta">{fields.file}</p> : null}
        </div>

        <div className="row row--end row--tight">
          <Link to="/admin/resources" className="btn">Cancel</Link>
          <button type="submit" className="btn btn--primary" disabled={pending}>
            {pending ? "Uploading..." : editing ? "Save Changes" : "Publish Resource"}
          </button>
        </div>
      </form>
    </>
  );
}

/* ------------------------------------------------------------------------- */
export function AdminUsers() {
  const { data, loading, error } = useLoad(() => api.auth.users(), []);
  if (loading) return <Loading />;
  if (error || !data) return <Notice kind="crit">{error}</Notice>;

  const students = data.filter((u: UserRow) => u.role === "STUDENT");
  const admins = data.filter((u: UserRow) => u.role === "ADMIN");

  return (
    <>
      <PageHead
        eyebrow="Administration"
        title="Users"
        lead="Accounts registered on the portal. Administrator accounts are created on the server."
      />
      <div className="grid grid-2 stack-8" style={{ maxWidth: "26rem" }}>
        <Stat value={students.length} label="Students" />
        <Stat value={admins.length} label="Administrators" />
      </div>
      <div className="scroll-x">
        <table className="table">
          <thead>
            <tr>
              <th scope="col">Name</th>
              <th scope="col">Email</th>
              <th scope="col">Role</th>
              <th scope="col">Uploads</th>
              <th scope="col">Registered</th>
            </tr>
          </thead>
          <tbody>
            {data.map((user: UserRow) => (
              <tr key={user.id}>
                <td>{user.name}</td>
                <td>{user.email}</td>
                <td>
                  <span className={user.role === "ADMIN" ? "chip chip--data" : "chip"}>
                    {user.role === "ADMIN" ? "Administrator" : "Student"}
                  </span>
                </td>
                <td className="tabular">{user.upload_count}</td>
                <td className="nowrap">{formatDate(user.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

export function AdminSettings() {
  const user = useSession((state) => state.user);
  const theme = useUi((state) => state.theme);
  const setTheme = useUi((state) => state.setTheme);
  const { data } = useLoad(() => api.stats(), []);

  return (
    <>
      <PageHead eyebrow="Administration" title="Settings" lead="Portal configuration and catalogue state." />

      <section className="stack-8">
        <SectionHead title="Your account" />
        <dl className="factgrid">
          <Fact label="Name" value={user?.name ?? "—"} />
          <Fact label="Email" value={user?.email ?? "—"} />
          <Fact label="Role" value="Administrator" />
          <Fact label="Scope" value="All departments" />
        </dl>
      </section>

      <section className="stack-8">
        <SectionHead title="Appearance" />
        <div className="row row--tight">
          {(["light", "dark"] as const).map((option) => (
            <button
              key={option}
              type="button"
              className={theme === option ? "btn btn--primary btn--sm" : "btn btn--sm"}
              onClick={() => setTheme(option)}
              aria-pressed={theme === option}
            >
              {option === "light" ? "Light" : "Dark"}
            </button>
          ))}
        </div>
      </section>

      <section className="stack-8">
        <SectionHead title="Catalogue" />
        <dl className="factgrid">
          <Fact label="Semesters" value={data?.semesters ?? "—"} />
          <Fact label="Subjects" value={data?.subjects ?? "—"} />
          <Fact label="Resources" value={data?.resources ?? "—"} />
          <Fact label="Exam resources" value={data?.exam_resources ?? "—"} />
        </dl>
      </section>

      <section>
        <SectionHead title="Security" />
        <Notice kind="warn" title="Before deploying to production">
          <ul>
            <li>Set a unique <code>REC_SECRET_KEY</code>.</li>
            <li>Change any seeded administrator password.</li>
            <li>Serve over HTTPS and set <code>REC_ALLOWED_HOSTS</code>.</li>
            <li>Back up the database and the media directory together.</li>
          </ul>
        </Notice>
      </section>
    </>
  );
}
