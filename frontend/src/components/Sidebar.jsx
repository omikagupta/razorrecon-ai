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

function Sidebar({ isOpen = false, onClose }) {
  return (
    <aside className={`sidebar ${isOpen ? "open" : ""}`}>
      <div className="brand">
        <div className="brand-icon">
          <ShieldCheck size={21} strokeWidth={2.2} />
        </div>

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
              end={item.path === "/"}
              onClick={onClose}
              className={({ isActive }) =>
                `nav-item ${isActive ? "active" : ""}`
              }
            >
              <Icon size={18} strokeWidth={2} />
              <span>{item.name}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="system-status">
          <span className="status-dot" />
          <span>System Operational</span>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;