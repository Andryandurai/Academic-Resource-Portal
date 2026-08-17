import type { SVGProps } from "react";

/**
 * Inline SVG icon set, carried over from the EchoSense approach: stroke-based,
 * `currentColor`, no icon library. Every icon is decorative — marked
 * aria-hidden and always paired with a visible or screen-reader label.
 */

type Props = SVGProps<SVGSVGElement>;

function Icon({ children, ...props }: Props & { children: React.ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width="20"
      height="20"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      {...props}
    >
      {children}
    </svg>
  );
}

export const GridIcon = (p: Props) => (
  <Icon {...p}>
    <rect x="3" y="3" width="7.5" height="7.5" rx="1.5" />
    <rect x="13.5" y="3" width="7.5" height="7.5" rx="1.5" />
    <rect x="3" y="13.5" width="7.5" height="7.5" rx="1.5" />
    <rect x="13.5" y="13.5" width="7.5" height="7.5" rx="1.5" />
  </Icon>
);

export const BookIcon = (p: Props) => (
  <Icon {...p}>
    <path d="M4 4.5A1.5 1.5 0 0 1 5.5 3H19v15H5.5A1.5 1.5 0 0 0 4 19.5z" />
    <path d="M4 19.5A1.5 1.5 0 0 1 5.5 18H19v3H5.5A1.5 1.5 0 0 1 4 19.5z" />
  </Icon>
);

export const LayersIcon = (p: Props) => (
  <Icon {...p}>
    <path d="m12 3 9 5-9 5-9-5z" />
    <path d="m3.5 12.5 8.5 4.7 8.5-4.7" />
    <path d="m3.5 16.8 8.5 4.7 8.5-4.7" />
  </Icon>
);

export const FileIcon = (p: Props) => (
  <Icon {...p}>
    <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
    <path d="M14 3v5h5" />
  </Icon>
);

export const UploadIcon = (p: Props) => (
  <Icon {...p}>
    <path d="M12 16V4" />
    <path d="m7.5 8.5 4.5-4.5 4.5 4.5" />
    <path d="M4 16v2.5A1.5 1.5 0 0 0 5.5 20h13a1.5 1.5 0 0 0 1.5-1.5V16" />
  </Icon>
);

export const DownloadIcon = (p: Props) => (
  <Icon {...p}>
    <path d="M12 4v12" />
    <path d="m7.5 11.5 4.5 4.5 4.5-4.5" />
    <path d="M4 16v2.5A1.5 1.5 0 0 0 5.5 20h13a1.5 1.5 0 0 0 1.5-1.5V16" />
  </Icon>
);

export const EyeIcon = (p: Props) => (
  <Icon {...p}>
    <path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12" />
    <circle cx="12" cy="12" r="3" />
  </Icon>
);

export const UsersIcon = (p: Props) => (
  <Icon {...p}>
    <circle cx="9" cy="8" r="3.25" />
    <path d="M3 20a6 6 0 0 1 12 0" />
    <path d="M16 5.4a3.25 3.25 0 0 1 0 5.2" />
    <path d="M17.5 14.6A6 6 0 0 1 21 20" />
  </Icon>
);

export const SettingsIcon = (p: Props) => (
  <Icon {...p}>
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06A1.7 1.7 0 0 0 15 19.4a1.7 1.7 0 0 0-1 1.55V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.55 1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-1.55-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.55-1.1 1.7 1.7 0 0 0-.34-1.87l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-1.55V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.55 1.7 1.7 0 0 0 1.87-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.7 1.7 0 0 0 19.4 9v.1a1.7 1.7 0 0 0 1.55 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" />
  </Icon>
);

export const SearchIcon = (p: Props) => (
  <Icon {...p}>
    <circle cx="11" cy="11" r="6.5" />
    <path d="m20 20-4.2-4.2" />
  </Icon>
);

export const LogoutIcon = (p: Props) => (
  <Icon {...p}>
    <path d="M14 4h4.5A1.5 1.5 0 0 1 20 5.5v13a1.5 1.5 0 0 1-1.5 1.5H14" />
    <path d="M10 16.5 14.5 12 10 7.5" />
    <path d="M14.5 12H4" />
  </Icon>
);

export const UserIcon = (p: Props) => (
  <Icon {...p}>
    <circle cx="12" cy="8" r="3.5" />
    <path d="M5 20a7 7 0 0 1 14 0" />
  </Icon>
);

export const PlusIcon = (p: Props) => (
  <Icon {...p}>
    <path d="M12 5v14" />
    <path d="M5 12h14" />
  </Icon>
);

export const PencilIcon = (p: Props) => (
  <Icon {...p}>
    <path d="M4 20h4L19.5 8.5a2.12 2.12 0 0 0-3-3L5 17z" />
    <path d="M14.5 6.5l3 3" />
  </Icon>
);

export const TrashIcon = (p: Props) => (
  <Icon {...p}>
    <path d="M4 7h16" />
    <path d="M9.5 7V5.5A1.5 1.5 0 0 1 11 4h2a1.5 1.5 0 0 1 1.5 1.5V7" />
    <path d="M6 7v12.5A1.5 1.5 0 0 0 7.5 21h9a1.5 1.5 0 0 0 1.5-1.5V7" />
    <path d="M10 11v6M14 11v6" />
  </Icon>
);

export const ChevronRightIcon = (p: Props) => (
  <Icon {...p}>
    <path d="m9 5 7 7-7 7" />
  </Icon>
);

export const ArrowLeftIcon = (p: Props) => (
  <Icon {...p}>
    <path d="M20 12H4" />
    <path d="m10 6-6 6 6 6" />
  </Icon>
);

export const CheckIcon = (p: Props) => (
  <Icon {...p}>
    <path d="m5 13 4.5 4.5L19 7" />
  </Icon>
);

export const AlertIcon = (p: Props) => (
  <Icon {...p}>
    <path d="M12 4.5 2.8 20h18.4z" />
    <path d="M12 10v4.5" />
    <path d="M12 17.4h.01" />
  </Icon>
);

export const InfoIcon = (p: Props) => (
  <Icon {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 11v5" />
    <path d="M12 8h.01" />
  </Icon>
);

export const MenuIcon = (p: Props) => (
  <Icon {...p}>
    <path d="M4 7h16M4 12h16M4 17h16" />
  </Icon>
);

export const CloseIcon = (p: Props) => (
  <Icon {...p}>
    <path d="m6 6 12 12M18 6 6 18" />
  </Icon>
);

export const InboxIcon = (p: Props) => (
  <Icon {...p}>
    <path d="M3.5 13.5h4l1.5 3h6l1.5-3h4" />
    <path d="M5.2 5.3 3.5 13.5v4A1.5 1.5 0 0 0 5 19h14a1.5 1.5 0 0 0 1.5-1.5v-4L18.8 5.3A1.5 1.5 0 0 0 17.4 4H6.6a1.5 1.5 0 0 0-1.4 1.3z" />
  </Icon>
);

export const ShieldIcon = (p: Props) => (
  <Icon {...p}>
    <path d="M12 3l7.5 3v5.5c0 4.6-3.1 8.4-7.5 9.5-4.4-1.1-7.5-4.9-7.5-9.5V6z" />
    <path d="m9 12 2 2 4-4" />
  </Icon>
);
