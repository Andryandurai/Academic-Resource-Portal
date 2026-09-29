import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { Brand, COLLEGE, PORTAL_NAME, Notice } from "../../components/common";
import { ApiError } from "../../services/client";
import { useSession } from "../../stores/session";
import { useUi } from "../../stores/ui";

/**
 * The two accounts this deployment ships with — shown only when this is
 * meant to be a demonstration deployment, never unconditionally.
 *
 * Listed in the UI on purpose *for a demo*: the point is that a reviewer can
 * sign in without being handed credentials out of band. That also means
 * these credentials are public wherever they're shown — they end up in the
 * JavaScript bundle — so neither account should ever hold anything private,
 * and a real production deployment (one with actual student/faculty data)
 * must not ship this panel at all.
 *
 * On by default in local development (`npm run dev`), and in any build that
 * explicitly opts in with `VITE_SHOW_DEMO_ACCOUNTS=true` (e.g. a deployed
 * grading/demo instance) — off otherwise. The `false` branch below is a
 * statically-known constant once Vite inlines `import.meta.env.*` at build
 * time, so a production build with neither condition set has the ternary's
 * `true` branch (and these two credential strings) eliminated by the
 * minifier, not merely hidden at runtime — verified by grepping the built
 * bundle for both passwords after `npm run build`.
 */
const SHOW_DEMO_ACCOUNTS = import.meta.env.DEV || import.meta.env.VITE_SHOW_DEMO_ACCOUNTS === "true";
const DEMO_ACCOUNTS = SHOW_DEMO_ACCOUNTS
  ? ([
      { role: "Student", email: "student@rec.local", password: "andyandy1234", admin: false },
      { role: "Administrator", email: "admin@rec.local", password: "trial1234", admin: true },
    ] as const)
  : ([] as const);

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
      const fallback = user.is_admin ? "/faculty/dashboard" : "/departments";
      // A student must never be dropped into a faculty path by a crafted
      // redirect target.
      const target =
        requested && (user.is_admin || !requested.startsWith("/faculty")) ? requested : fallback;
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

          {/* Only rendered on a demo deployment (see SHOW_DEMO_ACCOUNTS above)
              — absent entirely from a real production build. Only the
              accounts that this form will actually accept: the admin
              endpoint refuses a student outright, so offering one there would
              be a button that always fails. */}
          {SHOW_DEMO_ACCOUNTS ? (
            <div className="demoaccounts">
              <p className="demoaccounts__title">Demonstration accounts</p>
              {DEMO_ACCOUNTS.filter((account) => !admin || account.admin).map((account) => (
                <button
                  key={account.email}
                  type="button"
                  className="demoaccount"
                  onClick={() => {
                    setEmail(account.email);
                    setPassword(account.password);
                    setError(null);
                  }}
                >
                  <span className="demoaccount__role">{account.role}</span>
                  <span className="demoaccount__creds">
                    <span>{account.email}</span>
                    <span className="demoaccount__pw">{account.password}</span>
                  </span>
                  <span className="demoaccount__action" aria-hidden="true">
                    Use
                  </span>
                </button>
              ))}
              <p className="meta demoaccounts__hint">
                Click an account to fill the form, then press
                {admin ? " Admin Login" : " Login"}.
              </p>
            </div>
          ) : null}

          {/* Self-registration is deliberately absent: accounts are
              provisioned on the server, so there is no public path to creating
              one. */}
          <div className="row row--between">
            {admin ? (
              <Link to="/login">Student login</Link>
            ) : (
              <Link to="/faculty" className="muted">
                Administrator
              </Link>
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
