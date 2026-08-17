/**
 * The department the student is currently browsing.
 *
 * Persisted so a reload does not send them back to the picker, and cleared on
 * logout so the next person on a shared machine starts at the selection page.
 *
 * This is a *convenience*, never an authorisation boundary: every request sends
 * the department id and Django scopes the query through the
 * Subject → Semester → Department foreign keys. Editing this value in
 * localStorage changes which department you are looking at, not what you are
 * allowed to see.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { Department } from "../types";

interface DepartmentState {
  selected: Department | null;
  select(department: Department): void;
  clear(): void;
}

export const useDepartment = create<DepartmentState>()(
  persist(
    (set) => ({
      selected: null,
      select: (selected) => set({ selected }),
      clear: () => set({ selected: null }),
    }),
    { name: "rec-aids.department" },
  ),
);
