import { NavLink } from "react-router-dom";

import { NAV_ITEMS } from "./layoutNavigation";

export function Layout({ children }) {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Kaka_Quant</p>
          <h1 className="brand-title">轻量量化研究工作台展示壳</h1>
        </div>
        <nav className="nav-list">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="page-frame">{children}</main>
    </div>
  );
}
