import { Link } from "react-router-dom";
import type { ReactNode } from "react";

import { useUi } from "../stores/ui";
import { AlertIcon, CheckIcon, ChevronRightIcon, CloseIcon, InboxIcon, InfoIcon } from "./Icons";

export const COLLEGE = "Rajalakshmi Engineering College";
/**
 * Deliberately no DEPARTMENT constant.
 *
 * The portal serves every department of the college; the one being browsed is
 * read from the department store or the API response, never from a constant
 * here. Hard-coding a department name in the shared layer is exactly what made
 * the whole application look like it belonged to AI&DS.
 */
export const PORTAL_NAME = "Academic Resource Portal";

/**
 * Institutional mark.
 *
 * Text only: no official REC logo asset is bundled, and an unofficial or copied
 * one must not be used. To adopt the official mark once it is supplied and
 * authorised, drop the file into `public/` and render it in place of the
 * monogram below — nothing else changes.
 */
export function Brand({ to = "/", admin = false }: { to?: string; admin?: boolean }) {
  return (
    <Link to={to} className="brand" aria-label={`${COLLEGE} ${PORTAL_NAME}`}>
      <span className="brand__mark" aria-hidden="true">
        REC
      </span>
      <span className="brand__text">
        <span className="brand__name">{admin ? "REC Faculty" : "REC"}</span>
        <span className="brand__sub">
          {admin ? "Faculty portal" : PORTAL_NAME}
        </span>
      </span>
    </Link>
  );
}

export function PageHead({
  eyebrow,
  title,
  lead,
  actions,
}: {
  eyebrow?: ReactNode;
  title: string;
  lead?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <header className="pagehead">
      <div>
        {eyebrow ? <p className="label">{eyebrow}</p> : null}
        <h1 className="pagehead__title">{title}</h1>
        {lead ? <p className="lead">{lead}</p> : null}
      </div>
      {actions ? <div className="row row--tight">{actions}</div> : null}
    </header>
  );
}

export type Crumb = { label: string; to?: string };

export function Breadcrumbs({ items }: { items: Crumb[] }) {
  return (
    <nav aria-label="Breadcrumb" className="crumbs">
      <ol>
        {items.map((item, index) => {
          const last = index === items.length - 1;
          return (
            <li key={`${item.label}-${index}`}>
              {item.to && !last ? (
                <Link to={item.to}>{item.label}</Link>
              ) : (
                <span aria-current={last ? "page" : undefined}>{item.label}</span>
              )}
              {!last ? <ChevronRightIcon width={13} height={13} aria-hidden="true" /> : null}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

export function Stat({
  value,
  label,
  note,
  icon,
}: {
  value: number | string;
  label: string;
  note?: string;
  icon?: ReactNode;
}) {
  return (
    <div className="stat">
      {icon ? <span className="iconbadge">{icon}</span> : null}
      <div>
        <p className="stat__value">{value}</p>
        <p className="stat__label">{label}</p>
        {note ? <p className="meta">{note}</p> : null}
      </div>
    </div>
  );
}

export function EmptyState({
  title,
  detail,
  action,
  icon,
}: {
  title: string;
  detail?: string;
  action?: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <div className="emptystate">
      <span className="iconbadge iconbadge--lg" aria-hidden="true">
        {icon ?? <InboxIcon />}
      </span>
      <p className="emptystate__title">{title}</p>
      {detail ? <p className="muted">{detail}</p> : null}
      {action ? <div className="stack-3">{action}</div> : null}
    </div>
  );
}

export function SectionHead({
  title,
  count,
  detail,
  action,
}: {
  title: string;
  count?: number;
  detail?: string;
  action?: ReactNode;
}) {
  return (
    <div className="sectionhead">
      <div>
        <h2>
          {title}
          {typeof count === "number" ? <span className="chip">{count}</span> : null}
        </h2>
        {detail ? <p className="muted">{detail}</p> : null}
      </div>
      {action}
    </div>
  );
}

/** Definition-list tile used for subject metadata. */
export function Fact({
  label,
  value,
  emphasis = false,
}: {
  label: string;
  value: ReactNode;
  emphasis?: boolean;
}) {
  return (
    <div className={`fact${emphasis ? " fact--emphasis" : ""}`}>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

export function Notice({
  kind = "info",
  title,
  children,
}: {
  kind?: "info" | "warn" | "crit" | "ok";
  title?: string;
  children: ReactNode;
}) {
  return (
    <div className={`notice notice--${kind}`} role={kind === "crit" ? "alert" : undefined}>
      {title ? <p className="notice__title">{title}</p> : null}
      <div>{children}</div>
    </div>
  );
}

export function Loading({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="loading" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

export function SkeletonGrid({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-3">
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="panel">
          <div className="skeleton" style={{ height: 14, width: "40%" }} />
          <div className="skeleton" style={{ height: 18, marginTop: 12 }} />
          <div className="skeleton" style={{ height: 18, marginTop: 8, width: "70%" }} />
          <div className="skeleton" style={{ height: 34, marginTop: 18 }} />
        </div>
      ))}
    </div>
  );
}

/** Toast host. Lives in an aria-live region; status is never colour alone. */
export function Toaster() {
  const toasts = useUi((state) => state.toasts);
  const dismiss = useUi((state) => state.dismissToast);

  return (
    <div className="toast-stack" role="status" aria-live="polite">
      {toasts.map((toast) => (
        <div key={toast.id} className={`toast toast--${toast.kind}`}>
          <span className="toast__icon" aria-hidden="true">
            {toast.kind === "ok" ? <CheckIcon width={15} height={15} /> : null}
            {toast.kind === "crit" ? <AlertIcon width={15} height={15} /> : null}
            {toast.kind === "info" ? <InfoIcon width={15} height={15} /> : null}
          </span>
          <p>{toast.message}</p>
          <button
            type="button"
            className="btn btn--icon btn--sm"
            onClick={() => dismiss(toast.id)}
            aria-label="Dismiss notification"
          >
            <CloseIcon width={13} height={13} />
          </button>
        </div>
      ))}
    </div>
  );
}

export function Footer() {
  return (
    <footer className="sitefoot">
      <div>
        <p className="sitefoot__name">{COLLEGE}</p>
        <p className="muted">{PORTAL_NAME}</p>
        <p className="meta">All departments</p>
      </div>
      <div className="sitefoot__right">
        <p className="meta">&copy; {new Date().getFullYear()} {COLLEGE}</p>
        {/* Honest provenance: this deployment is not presented as an official
            college service unless the operator is authorised. */}
        <p className="meta">
          Departmental academic resource portal. Not an official college service
          unless deployed with institutional authorisation.
        </p>
      </div>
    </footer>
  );
}

export function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 KB";
  if (bytes < 1024) return `${bytes} B`;
  const kb = bytes / 1024;
  if (kb < 1024) return `${Math.round(kb)} KB`;
  const mb = kb / 1024;
  return `${mb < 10 ? mb.toFixed(1) : Math.round(mb)} MB`;
}

export function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}
