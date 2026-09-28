import { NavLink, Outlet } from "react-router-dom";

import { Brand, Toaster } from "../components/common";
import {
  BookIcon,
  FileIcon,
  GridIcon,
  SettingsIcon,
  UploadIcon,
  UsersIcon,
} from "../components/Icons";
import { LogoutButton } from "../components/LogoutButton";
import { useSession } from "../stores/session";

const NAV = [
  { to: "/admin", label: "Dashboard", icon: GridIcon, end: true },
  { to: "/admin/subjects", label: "Subjects", icon: BookIcon, end: false },
  { to: "/admin/resources", label: "Resources", icon: FileIcon, end: true },
  { to: "/admin/resources/new", label: "Upload Resource", icon: UploadIcon, end: true },
  { to: "/admin/users", label: "Users", icon: UsersIcon, end: true },
  { to: "/admin/settings", label: "Settings", icon: SettingsIcon, end: true },
];

/** Administrator shell: a persistent rail on desktop, stacked on small screens. */
export function AdminLayout() {
  const user = useSession((state) => state.user);

  return (
    <div className="adminshell">
      <aside className="adminrail">
        <Brand to="/admin" admin />
        <nav className="adminrail__nav" aria-label="Administration">
          {NAV.map((item) => {
            const ItemIcon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className="adminrail__link"
              >
                <ItemIcon width={17} height={17} />
                {item.label}
              </NavLink>
            );
          })}
        </nav>
        <div className="stack-2">
          <hr className="rule" />
          <p className="label">Signed in as</p>
          <p className="nowrap" style={{ fontWeight: 600, margin: 0 }}>{user?.name}</p>
          <p className="meta">Administrator</p>
          <LogoutButton variant="admin" className="btn btn--sm btn--block" />
        </div>
      </aside>

      <main id="main" className="adminmain">
        <Outlet />
      </main>
      <Toaster />
    </div>
  );
}
