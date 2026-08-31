import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  AlertTriangle,
  History,
  ShieldCheck,
} from "lucide-react";

const navigation = [
  {
    name: "Dashboard",
    path: "/",
    icon: LayoutDashboard,
  },
  {
    name: "Exceptions",
    path: "/exceptions",
    icon: AlertTriangle,
  },
  {
    name: "Reconciliation Runs",
    path: "/runs",
    icon: History,
  },
];

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <ShieldCheck size={30} />
        <div>
          <h2>RazorRecon</h2>
          <span>AI Intelligence</span>
        </div>
      </div>

      <nav className="navigation">
        <p className="nav-label">OPERATIONS</p>

        {navigation.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `nav-item ${isActive ? "active" : ""}`
              }
            >
              <Icon size={20} />
              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="system-status">
          <span className="status-dot" />
          System Operational
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;