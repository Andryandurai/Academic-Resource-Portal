/** The endpoint surface, typed. Nothing else in the app builds a URL. */

import { downloadFile, openFile, request } from "./client";
import type {
  AuthResponse,
  Department,
  Paginated,
  Resource,
  ResourceCounts,
  Semester,
  Stats,
  Subject,
  User,
  UserRow,
} from "../types";

export interface SubjectQuery {
  search?: string;
  /** Scoping happens in the database — see academics/filters.py. */
  department?: number | string;
  semester?: number | string;
  semester_number?: number | string;
  course_type?: string;
  category?: string;
  page_size?: number;
}

export interface ResourceQuery {
  subject?: number | string;
  department?: number | string;
  semester?: number | string;
  resource_type?: string;
  search?: string;
  uploaded_from?: string;
  uploaded_to?: string;
  page_size?: number;
}

export const api = {
  auth: {
    adminLogin: (email: string, password: string) =>
      request<AuthResponse>("/api/auth/admin/login/", {
        method: "POST",
        body: { email, password },
        auth: false,
      }),
    me: () => request<User>("/api/auth/me/"),
    logout: (refresh: string) =>
      request<void>("/api/auth/logout/", { method: "POST", body: { refresh } }),
    users: () => request<UserRow[]>("/api/auth/users/"),
  },

  departments: {
    list: (search?: string) =>
      request<Department[]>("/api/departments/", { query: { search } }),
    get: (id: number | string) => request<Department>(`/api/departments/${id}/`),
  },

  stats: (department?: number | string) =>
    request<Stats>("/api/stats/", { query: { department } }),

  semesters: {
    list: (department?: number | string) =>
      request<Semester[]>("/api/semesters/", { query: { department } }),
    get: (id: number | string) => request<Semester>(`/api/semesters/${id}/`),
  },

  subjects: {
    list: (query: SubjectQuery = {}) =>
      request<Paginated<Subject>>("/api/subjects/", {
        query: { page_size: 200, ...query },
      }),
    get: (id: number | string) => request<Subject>(`/api/subjects/${id}/`),
    resourceCounts: (id: number | string) =>
      request<ResourceCounts>(`/api/subjects/${id}/resource-counts/`),
    create: (body: Record<string, unknown>) =>
      request<Subject>("/api/subjects/", { method: "POST", body }),
    update: (id: number | string, body: Record<string, unknown>) =>
      request<Subject>(`/api/subjects/${id}/`, { method: "PATCH", body }),
    remove: (id: number | string) =>
      request<void>(`/api/subjects/${id}/`, { method: "DELETE" }),
  },

  resources: {
    list: (query: ResourceQuery = {}) =>
      request<Paginated<Resource>>("/api/resources/", {
        query: { page_size: 200, ...query },
      }),
    get: (id: number | string) => request<Resource>(`/api/resources/${id}/`),
    recent: (limit = 8, department?: number | string) =>
      request<Resource[]>("/api/resources/recent/", { query: { limit, department } }),
    /** Multipart, so the browser sets the boundary and streams the file. */
    create: (form: FormData) =>
      request<Resource>("/api/resources/", { method: "POST", form }),
    update: (id: number | string, form: FormData) =>
      request<Resource>(`/api/resources/${id}/`, { method: "PATCH", form }),
    remove: (id: number | string) =>
      request<void>(`/api/resources/${id}/`, { method: "DELETE" }),
    download: (id: number | string, filename: string) =>
      downloadFile(`/api/resources/${id}/download/`, filename),
    preview: (id: number | string) => openFile(`/api/resources/${id}/download/`),
  },
};
