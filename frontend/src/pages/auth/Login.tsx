import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { Brand, COLLEGE, PORTAL_NAME, Notice } from "../../components/common";
import { ApiError } from "../../services/client";
import { useSession } from "../../stores/session";
import { useUi } from "../../stores/ui";

/** Administrator sign-in — the only account type this portal has. */
export function Login() {
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
      const user = await login(email, password);
      toast(`Signed in as ${user.name}.`, "ok");
      navigate(requested ?? "/admin", { replace: true });
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
      <Brand to="/admin/login" admin />

      <div className="panel authcard">
        <div className="stack-4">
          <span className="chip chip--data">Restricted area</span>
          <div>
            <h1 style={{ margin: 0 }}>Administrator Login</h1>
            <p className="muted">Sign in to manage subjects and publish academic resources.</p>
          </div>

          {error ? <Notice kind="crit">{error}</Notice> : null}

          <form onSubmit={onSubmit} className="stack-4" noValidate>
            <div className="field">
              <label htmlFor="email">Administrator email</label>
              <input
                id="email"
                className="input"
                type="email"
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@rec.local"
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
              {pending ? "Signing in..." : "Admin Login"}
            </button>
          </form>
        </div>
      </div>

      <p className="meta">
        {COLLEGE} · {PORTAL_NAME}
      </p>
    </div>
  );
}
