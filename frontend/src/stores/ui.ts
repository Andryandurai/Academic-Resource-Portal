/**
 * Global UI state — deliberately small.
 *
 * Only what genuinely spans routes lives here: the mobile navigation drawer, the
 * theme, and the toast queue. Catalogue data is fetched per screen and kept in
 * component state, because putting server data in a global store is how it goes
 * stale without anyone noticing.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Theme = "light" | "dark";
export type ToastKind = "ok" | "crit" | "info";

export interface Toast {
  id: number;
  message: string;
  kind: ToastKind;
}

interface UiState {
  navOpen: boolean;
  theme: Theme;
  toasts: Toast[];

  setNavOpen(open: boolean): void;
  toggleNav(): void;
  setTheme(theme: Theme): void;
  applyTheme(): void;
  toast(message: string, kind?: ToastKind): void;
  dismissToast(id: number): void;
}

let nextToastId = 0;

export const useUi = create<UiState>()(
  persist(
    (set, get) => ({
      navOpen: false,
      theme: "light",
      toasts: [],

      setNavOpen: (navOpen) => set({ navOpen }),
      toggleNav: () => set((state) => ({ navOpen: !state.navOpen })),

      setTheme(theme) {
        set({ theme });
        document.documentElement.setAttribute("data-theme", theme);
      },

      applyTheme() {
        document.documentElement.setAttribute("data-theme", get().theme);
      },

      toast(message, kind = "info") {
        const id = ++nextToastId;
        set((state) => ({ toasts: [...state.toasts, { id, message, kind }] }));
        window.setTimeout(() => get().dismissToast(id), kind === "crit" ? 7000 : 4200);
      },

      dismissToast(id) {
        set((state) => ({ toasts: state.toasts.filter((toast) => toast.id !== id) }));
      },
    }),
    {
      name: "rec-aids.ui",
      partialize: (state) => ({ theme: state.theme }),
    },
  ),
);
