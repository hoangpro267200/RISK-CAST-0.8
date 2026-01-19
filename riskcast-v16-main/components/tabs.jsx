import React from "react";
import "../static/css/components/tabs.css";

const tabs = [
  { id: "overview", label: "Overview" },
  { id: "transport", label: "Transport" },
  { id: "cargo", label: "Cargo" },
  { id: "analytics", label: "Analytics" },
];

export default function Tabs({ active = "overview" }) {
  return (
    <nav className="tabs glass-card-sm" data-tabs>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`tab-trigger ${active === tab.id ? "is-active" : ""}`}
          data-tab-target={tab.id}
          type="button"
        >
          {tab.label}
        </button>
      ))}
      <span className="tab-indicator" aria-hidden="true"></span>
    </nav>
  );
}




