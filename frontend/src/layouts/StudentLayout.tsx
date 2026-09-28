import { Link, NavLink, Outlet } from "react-router-dom";

import { Brand, Footer, Toaster } from "../components/common";
import { CloseIcon, MenuIcon } from "../components/Icons";
import { useDepartment } from "../stores/department";
import { useUi } from "../stores/ui";

const NAV = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/semesters", label: "Semesters" },
  { to: "/subjects", label: "Subjects" },
];

/** Student shell: horizontal navigation on desktop, a drawer on small screens. */
export function StudentLayout() {
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
