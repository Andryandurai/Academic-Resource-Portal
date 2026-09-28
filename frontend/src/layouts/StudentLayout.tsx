import { Link, NavLink, Outlet } from "react-router-dom";

import { Brand, Footer, Toaster } from "../components/common";
import { CloseIcon, MenuIcon, UserIcon } from "../components/Icons";
import { LogoutButton } from "../components/LogoutButton";
import { useDepartment } from "../stores/department";
import { useSession } from "../stores/session";
import { useUi } from "../stores/ui";

const NAV = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/semesters", label: "Semesters" },
  { to: "/subjects", label: "Subjects" },
  { to: "/profile", label: "Profile" },
];

/** Student shell: horizontal navigation on desktop, a drawer on small screens. */
export function StudentLayout() {
  const user = useSession((state) => state.user);
  const department = useDepartment((state) => state.selected);
  const navOpen = useUi((state) => state.navOpen);
  const toggleNav = useUi((state) => state.toggleNav);
  const setNavOpen = useUi((state) => state.setNavOpen);

  const links = NAV.map((item) => (
    <NavLink key={item.to} to={item.to} onClick={() => setNavOpen(false)}>
      {item.label}
    </NavLink>
  ));

  return (
    <div className="appshell">
      <header className="topbar">
        <div className="topbar__inner">
          <Brand to="/dashboard" />
          {department ? (
            <Link to="/departments" className="deptbadge" title="Change department">
              <span className="deptbadge__code">{department.code}</span>
              <span className="deptbadge__name">{department.name}</span>
              <span className="deptbadge__change">Change</span>
            </Link>
          ) : null}
          <nav className="topnav topnav--desktop" aria-label="Primary">
            {links}
          </nav>
          <div className="row row--tight topbar__account">
            <span className="row row--tight muted">
              <UserIcon width={16} height={16} aria-hidden="true" />
              <span className="nowrap">{user?.name}</span>
            </span>
            <LogoutButton variant="student" />
          </div>
          <button
            type="button"
            className="btn btn--sm only-mobile"
            onClick={toggleNav}
            aria-expanded={navOpen}
            aria-controls="student-nav"
          >
            {navOpen ? <CloseIcon width={18} height={18} /> : <MenuIcon width={18} height={18} />}
            <span className="sr-only">{navOpen ? "Close menu" : "Open menu"}</span>
          </button>
        </div>
        {navOpen ? (
          <nav id="student-nav" className="topnav topnav--mobile" aria-label="Mobile">
            {links}
            <hr className="rule" />
            <LogoutButton variant="student" className="btn btn--sm btn--block" />
          </nav>
        ) : null}
      </header>

      <main id="main" className="appmain">
        <Outlet />
      </main>

      <Footer />
      <Toaster />
    </div>
  );
}
