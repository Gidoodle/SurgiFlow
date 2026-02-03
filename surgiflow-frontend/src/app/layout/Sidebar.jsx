import { NavLink } from "react-router-dom";

export default function Sidebar() {
  return (
    <aside style={{ width: "220px", padding: "16px", borderRight: "1px solid #ddd" }}>
      <h2>Axiom Medical</h2>
      <nav>
        <ul style={{ listStyle: "none", padding: 0 }}>
          <li><NavLink to="/dashboard">Dashboard</NavLink></li>
          <li><NavLink to="/patients">Patients</NavLink></li>
          <li><NavLink to="/patients/new">New Patient</NavLink></li>
        </ul>
      </nav>
    </aside>
  );
}
