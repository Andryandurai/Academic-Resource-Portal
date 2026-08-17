/**
 * Typed API client.
 *
 * One fetch wrapper so the bearer header, silent token refresh and error shaping
 * happen in exactly one place. Every DRF error carries either `detail` or a
 * field map; `ApiError` surfaces both so a form can show what actually went
 * wrong instead of "something went wrong".
 */

/**
 * Where the API lives.
 *
 * In development Vite proxies `/api` to Django (see vite.config.ts), so the base
 * is empty and the browser sees one origin. In a production build the SPA is
 * served by Django itself from the same origin, so the base is empty there too —
 * which means the deployed URL is never baked into the bundle and one build
 * works on any host. `VITE_API_BASE_URL` overrides both, for a deployment that
 * hosts the frontend separately. An empty value counts as unset.
 */
const CONFIGURED = import.meta.env.VITE_API_BASE_URL?.trim();
export const API_BASE = CONFIGURED || "";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
    readonly fields: Record<string, string> = {},
  ) {
    super(message);
    this.name = "ApiError";
  }

  get isAuth(): boolean {
    return this.status === 401;
  }

  get isForbidden(): boolean {
    return this.status === 403;
  }
}

type Tokens = { access: string | null; refresh: string | null };

let tokens: Tokens = { access: null, refresh: null };
let onTokens: ((next: Tokens) => void) | null = null;
let onAuthFailure: (() => void) | null = null;

export function setTokens(next: Tokens): void {
  tokens = next;
}

export function getAccessToken(): string | null {
  return tokens.access;
}

/** Called when a refresh produces a new access token, so the store can persist it. */
export function onTokensRefreshed(handler: (next: Tokens) => void): void {
  onTokens = handler;
}

/** Called when the session is no longer recoverable. */
export function onSessionExpired(handler: () => void): void {
  onAuthFailure = handler;
}

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  query?: Record<string, string | number | boolean | null | undefined>;
  /** FormData is sent as-is so the browser sets the multipart boundary. */
  form?: FormData;
  signal?: AbortSignal;
  auth?: boolean;
}

function buildUrl(path: string, query?: RequestOptions["query"]): string {
  const url = new URL(API_BASE + path, window.location.origin);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== null && value !== undefined && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

/** Turns a DRF error body into a message plus a per-field map. */
async function toApiError(response: Response): Promise<ApiError> {
  let message = `${response.status} ${response.statusText}`;
  const fields: Record<string, string> = {};

  try {
    const parsed = await response.json();
    if (typeof parsed?.detail === "string") {
      message = parsed.detail;
    } else if (parsed && typeof parsed === "object") {
      for (const [key, value] of Object.entries(parsed as Record<string, unknown>)) {
        const text = Array.isArray(value) ? String(value[0]) : String(value);
        fields[key] = text;
        if (key === "non_field_errors") message = text;
      }
      if (message.startsWith(String(response.status))) {
        const first = Object.values(fields)[0];
        if (first) message = first;
      }
    }
  } catch {
    /* non-JSON error body */
  }

  return new ApiError(response.status, message, fields);
}

let refreshInFlight: Promise<boolean> | null = null;

/**
 * Exchange the refresh token for a new access token.
 *
 * Deduplicated: several requests failing with 401 at once must not fire several
 * refreshes, or all but one would be rejected by rotation and the user would be
 * signed out mid-session.
 */
async function refreshAccessToken(): Promise<boolean> {
  if (!tokens.refresh) return false;
  if (refreshInFlight) return refreshInFlight;

  refreshInFlight = (async () => {
    try {
      const response = await fetch(buildUrl("/api/auth/token/refresh/"), {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ refresh: tokens.refresh }),
      });
      if (!response.ok) return false;

      const data = await response.json();
      tokens = { access: data.access, refresh: data.refresh ?? tokens.refresh };
      onTokens?.(tokens);
      return true;
    } catch {
      return false;
    } finally {
      refreshInFlight = null;
    }
  })();

  return refreshInFlight;
}

async function send(path: string, options: RequestOptions, retry: boolean): Promise<Response> {
  const { method = "GET", body, query, form, signal, auth = true } = options;

  const headers: Record<string, string> = {};
  if (auth && tokens.access) headers.Authorization = `Bearer ${tokens.access}`;
  if (body !== undefined && !form) headers["content-type"] = "application/json";

  const response = await fetch(buildUrl(path, query), {
    method,
    headers,
    body: form ?? (body === undefined ? undefined : JSON.stringify(body)),
    signal,
  });

  // An expired access token is recoverable without the user noticing.
  if (response.status === 401 && auth && retry && tokens.refresh) {
    if (await refreshAccessToken()) return send(path, options, false);
    onAuthFailure?.();
  }

  return response;
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await send(path, options, true);

  if (response.status === 204 || response.status === 205) return undefined as T;
  if (!response.ok) throw await toApiError(response);

  return (await response.json()) as T;
}

/**
 * Fetch an authenticated file and hand it to the browser as a download.
 *
 * A plain `<a href>` cannot do this: browser navigation carries no
 * Authorization header, so every download link would land on a 401 and silently
 * produce nothing. The bytes are fetched with the token attached and saved as a
 * blob; the server's own Content-Disposition filename wins when present.
 */
export async function downloadFile(path: string, fallbackName: string): Promise<void> {
  const response = await send(path, {}, true);
  if (!response.ok) throw await toApiError(response);

  const filename = filenameFrom(response.headers.get("content-disposition")) ?? fallbackName;
  saveBlob(await response.blob(), filename);
}

/** Open an authenticated file in a new tab (PDF preview). */
export async function openFile(path: string): Promise<string> {
  const response = await send(path, { query: { inline: "1" } }, true);
  if (!response.ok) throw await toApiError(response);
  return URL.createObjectURL(await response.blob());
}

function filenameFrom(header: string | null): string | null {
  if (!header) return null;
  const encoded = /filename\*=(?:UTF-8'')?([^;]+)/i.exec(header);
  if (encoded) {
    try {
      return decodeURIComponent(encoded[1].trim().replace(/^"|"$/g, ""));
    } catch {
      /* fall through to the plain form */
    }
  }
  const plain = /filename="?([^";]+)"?/i.exec(header);
  return plain ? plain[1].trim() : null;
}

function saveBlob(blob: Blob, filename: string): void {
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  anchor.rel = "noopener";
  anchor.style.display = "none";
  // Attached before clicking — Firefox ignores a detached anchor — and revoked
  // on a later task, because revoking synchronously after click() can cancel
  // the download in Chromium before it has read the blob.
  document.body.appendChild(anchor);
  anchor.click();
  window.setTimeout(() => {
    anchor.remove();
    URL.revokeObjectURL(objectUrl);
  }, 2000);
}
