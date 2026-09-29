/**
 * Authentication state.
 *
 * Persisted to localStorage so a page reload does not sign the user out. Only
 * the tokens and the user object are stored — never a password, and never any
 * catalogue data, which belongs to the API and goes stale.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

import { api } from "../services/api";
import {
  ApiError,
  onSessionExpired,
  onTokensRefreshed,
  setTokens,
} from "../services/client";
import type { AuthResponse, Role, User } from "../types";

interface SessionState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  /** True while the persisted session is being re-validated on boot. */
  booting: boolean;

  isAuthenticated(): boolean;
  role(): Role | null;
  login(email: string, password: string, asAdmin?: boolean): Promise<User>;
  logout(): Promise<void>;
  hydrate(): Promise<void>;
}

export const useSession = create<SessionState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      booting: true,

      isAuthenticated: () => Boolean(get().accessToken && get().user),
      role: () => get().user?.role ?? null,

      async login(email, password, asAdmin = false) {
        const response: AuthResponse = asAdmin
          ? await api.auth.adminLogin(email, password)
          : await api.auth.login(email, password);
        applyTokens(response);
        set({
          user: response.user,
          accessToken: response.access,
          refreshToken: response.refresh,
        });
        return response.user;
      },

      async logout() {
        const { refreshToken } = get();
        // Best effort: the server blacklists the refresh token so it cannot be
        // replayed, but a network failure must not trap the user in a session
        // they asked to end.
        if (refreshToken) {
          try {
            await api.auth.logout(refreshToken);
          } catch {
            /* already expired, or offline */
          }
        }
        setTokens({ access: null, refresh: null });
        set({ user: null, accessToken: null, refreshToken: null });
      },

      /**
       * Re-validate a persisted session on boot.
       *
       * `/me/` is what makes a demoted administrator lose the admin UI
       * immediately: the role is re-read from the database rather than trusted
       * from the stored token.
       */
      async hydrate() {
        const { accessToken, refreshToken } = get();
        setTokens({ access: accessToken, refresh: refreshToken });

        if (!accessToken) {
          set({ booting: false });
          return;
        }

        try {
          const user = await api.auth.me();
          set({ user, booting: false });
        } catch (error) {
          if (error instanceof ApiError && (error.isAuth || error.isForbidden)) {
            setTokens({ access: null, refresh: null });
            set({ user: null, accessToken: null, refreshToken: null, booting: false });
          } else {
            // A network blip should not sign anyone out; keep the stored
            // session and let the next request retry.
            set({ booting: false });
          }
        }
      },
    }),
    {
      name: "rec-aids.session",
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    },
  ),
);

function applyTokens(response: AuthResponse): void {
  setTokens({ access: response.access, refresh: response.refresh });
}

// Keep the persisted copy in step when the client rotates the tokens.
onTokensRefreshed((next) => {
  useSession.setState({ accessToken: next.access, refreshToken: next.refresh });
});

// An unrecoverable session must drop the user at the login screen rather than
// leaving them staring at a page of failed requests.
onSessionExpired(() => {
  const { user } = useSession.getState();
  if (!user) return;
  setTokens({ access: null, refresh: null });
  useSession.setState({ user: null, accessToken: null, refreshToken: null });
});
