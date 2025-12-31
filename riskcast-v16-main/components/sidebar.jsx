import React from "react";
import "../static/css/components/sidebar.css";

const navGroups = [
  {
    label: "Core",
    items: [
      { id: "overview", label: "Overview", icon: "◎", href: "#overview" },
      { id: "transport", label: "Transport", icon: "↔", href: "#transport" },
      { id: "cargo", label: "Cargo", icon: "▣", href: "#cargo" },
    ],
  },
  {
    label: "Analytics",
    items: [{ id: "analytics", label: "Analytics", icon: "✦", href: "#analytics" }],
  },
];

export default function Sidebar({ active = "overview" }) {
  return (
    <aside className="sidebar glass-card-lg">
      <div className="sidebar__logo">RISKCAST</div>
      {navGroups.map((group) => (
        <div className="sidebar__section" key={group.label}>
          <div className="sidebar__label">{group.label}</div>
          {group.items.map((item) => (
            <a
              key={item.id}
              className={`sidebar__item ${active === item.id ? "is-active" : ""}`}
              href={item.href}
            >
              <span className="sidebar__icon" aria-hidden="true">
                {item.icon}
              </span>
              <span className="sidebar__text">{item.label}</span>
            </a>
          ))}
        </div>
      ))}
    </aside>
  );
}




