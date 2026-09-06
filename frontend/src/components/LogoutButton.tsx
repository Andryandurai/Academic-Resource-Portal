import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { LogoutIcon } from "./Icons";
import { useSession } from "../stores/session";
import { useUi } from "../stores/ui";

/**
 * Sign out of the admin portal.
 *
 * The store clears the Zustand state, the in-memory tokens and the persisted
 * copy, and blacklists the refresh token server-side. This component adds the
 * navigation half: a `replace` to the login screen so the protected page is
 * dropped from the history entry rather than left one Back press away.
 *
 * Back navigation is safe regardless — the route guard reads live store
 * state, so a restored history entry re-runs it and redirects — but replacing
 * the entry means the user never sees a protected screen flash first.
 */
export function LogoutButton({
  className = "btn btn--sm",
  label = "Logout",
  showIcon = true,
}: {
  className?: string;
  label?: string;
  showIcon?: boolean;
}) {
  const logout = useSession((state) => state.logout);
  const toast = useUi((state) => state.toast);
  const setNavOpen = useUi((state) => state.setNavOpen);
  const navigate = useNavigate();
  const [pending, setPending] = useState(false);

  async function onClick() {
    setPending(true);
    try {
      await logout();
      setNavOpen(false);
      toast("You have been signed out.", "ok");
    } finally {
      setPending(false);
      navigate("/admin/login", { replace: true });
    }
  }

  return (
    <button type="button" className={className} onClick={() => void onClick()} disabled={pending}>
      {showIcon ? <LogoutIcon width={15} height={15} aria-hidden="true" /> : null}
      {pending ? "Signing out..." : label}
    </button>
  );
}
