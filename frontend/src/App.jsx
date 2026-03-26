import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import CalendarPage from "./pages/CalendarPage";
import ItemPage from "./pages/ItemPage";
import "./App.css";

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <nav className="sidebar">
          <div className="sidebar-logo">
            <span className="logo-field">Field</span>
            <span className="logo-pie">Pie</span>
            <span className="logo-tag">Social</span>
          </div>
          <NavLink to="/" end className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
            📅 Calendar
          </NavLink>
        </nav>
        <main className="main-content">
          <Routes>
            <Route path="/" element={<CalendarPage />} />
            <Route path="/item/:year/:month/:id" element={<ItemPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
