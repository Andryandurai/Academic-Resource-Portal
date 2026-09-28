import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { Brand, COLLEGE, PORTAL_NAME, Notice } from "../../components/common";
import { ApiError } from "../../services/client";
import { useSession } from "../../stores/session";
import { useUi } from "../../stores/ui";

/**
 * Student and administrator sign-in.
 *
 * One component, two modes: the administrator variant posts to the admin
 * endpoint, which refuses to issue a token to a student account even when the
 * credentials are correct.
 */
export function Login({ admin = false }: { admin?: boolean }) {
  const login = useSession((state) => state.login);
  const toast = useUi((state) => state.toast);
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const requested = (location.state as { from?: string } | null)?.from;

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setPending(true);
    try {
      const user = await login(email, password, admin);
      toast(`Signed in as ${user.name}.`, "ok");
      // A student picks their department first; no department is the default.
      const fallback = user.is_admin ? "/admin" : "/departments";
      // A student must never be dropped into an admin path by a crafted
      // redirect target.
      const target =
        requested && (user.is_admin || !requested.startsWith("/admin")) ? requested : fallback;
      navigate(target, { replace: true });
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Could not reach the server. Check your connection and try again.",
      );
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="authwrap">
      <Brand to="/" admin={admin} />

      <div className="panel authcard">
        <div className="stack-4">
          {admin ? <span className="chip chip--data">Restricted area</span> : null}
          <div>
            <h1 style={{ margin: 0 }}>{admin ? "Administrator Login" : "Student Login"}</h1>
            <p className="muted">
              {admin
                ? "Sign in to manage subjects and publish academic resources."
                : "Sign in to access your semester subjects, unit notes and examination resources."}
            </p>
          </div>

          {error ? <Notice kind="crit">{error}</Notice> : null}

          <form onSubmit={onSubmit} className="stack-4" noValidate>
            <div className="field">
              <label htmlFor="email">{admin ? "Administrator email" : "Email address"}</label>
              <input
                id="email"
                className="input"
                type="email"
                autoComplete={admin ? "username" : "email"}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={admin ? "admin@rec.local" : "you@rajalakshmi.edu.in"}
                required
              />
            </div>

            <div className="field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                className="input"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <button type="submit" className="btn btn--primary btn--block" disabled={pending}>
              {pending ? "Signing in..." : admin ? "Admin Login" : "Login"}
            </button>
          </form>

          <div className="row row--between">
            {admin ? (
              <Link to="/login">Student login</Link>
            ) : (
              <>
                <Link to="/register">Create a student account</Link>
                <Link to="/admin/login" className="muted">
                  Administrator
                </Link>
              </>
            )}
          </div>
        </div>
      </div>

      <p className="meta">
        {COLLEGE} · {PORTAL_NAME}
      </p>
    </div>
  );
}

export function Register() {
  const register = useSession((state) => state.register);
  const toast = useUi((state) => state.toast);
  const navigate = useNavigate();

  const [form, setForm] = useState({ name: "", email: "", password: "", confirm: "" });
  const [error, setError] = useState<string | null>(null);
  const [fields, setFields] = useState<Record<string, string>>({});
  const [pending, setPending] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setFields({});

    if (form.password !== form.confirm) {
      setFields({ confirm: "Passwords do not match." });
      return;
    }

    setPending(true);
    try {
      await register(form.name, form.email, form.password);
      toast("Welcome to the REC Academic Resource Portal.", "ok");
      navigate("/departments", { replace: true });
    } catch (caught) {
      if (caught instanceof ApiError) {
        setError(caught.message);
        setFields(caught.fields);
      } else {
        setError("Could not reach the server. Check your connection and try again.");
      }
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="authwrap">
      <Brand to="/" />
      <div className="panel authcard">
        <div className="stack-4">
          <div>
            <h1 style={{ margin: 0 }}>Create a student account</h1>
            <p className="muted">
              Register to browse subjects and open the material published by the department.
            </p>
          </div>

          {error ? <Notice kind="crit">{error}</Notice> : null}

          <form onSubmit={onSubmit} className="stack-4" noValidate>
            {(
              [
                ["name", "Full name", "text", "name"],
                ["email", "Email address", "email", "email"],
                ["password", "Password", "password", "new-password"],
                ["confirm", "Confirm password", "password", "new-password"],
              ] as const
            ).map(([key, label, type, autoComplete]) => (
              <div className="field" key={key}>
                <label htmlFor={key}>{label}</label>
                <input
                  id={key}
                  className="input"
                  type={type}
                  autoComplete={autoComplete}
                  value={form[key]}
                  onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                  aria-invalid={fields[key] ? true : undefined}
                  required
                />
                {fields[key] ? (
                  <p className="meta" style={{ color: "var(--crit-ink)" }}>
                    {fields[key]}
                  </p>
                ) : null}
              </div>
            ))}

            <button type="submit" className="btn btn--primary btn--block" disabled={pending}>
              {pending ? "Creating account..." : "Create account"}
            </button>
          </form>

          <p className="meta">
            Accounts created here are student accounts with read-only access to published
            resources.
          </p>
          <Link to="/login">Already registered? Sign in</Link>
        </div>
      </div>
    </div>
  );
}
