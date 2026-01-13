import React from "react";
import "../static/css/components/kpi.css";

const kpis = [
  { label: "On-time", value: "94%", pill: "Stable", tone: "success" },
  { label: "ETA", value: "36h", pill: "+2h", tone: "info" },
  { label: "Temperature", value: "4.2°C", pill: "Good", tone: "success" },
  { label: "Humidity", value: "58%", pill: "Watch", tone: "warning" },
  { label: "Shock Events", value: "3", pill: "High", tone: "danger" },
  { label: "Energy Buffer", value: "72%", pill: "+8%", tone: "info" },
  { label: "CO₂e", value: "1.8t", pill: "Low", tone: "success" },
  { label: "Route Risk", value: "0.32", pill: "Monitor", tone: "warning" },
  { label: "Carrier SLA", value: "98%", pill: "Locked", tone: "success" },
  { label: "Customs Docs", value: "100%", pill: "Ready", tone: "success" },
  { label: "Insurance", value: "Full", pill: "Bound", tone: "info" },
  { label: "Cost Variance", value: "-3%", pill: "Ahead", tone: "success" },
];

export default function KpiPanel() {
  return (
    <aside className="kpi-panel glass-card-lg">
      <div className="kpi-panel__header">
        <div className="eyebrow">KPIs</div>
        <div className="title-sm">Live Metrics</div>
      </div>
      <div className="kpi-scroll">
        {kpis.map((kpi) => (
          <div className="kpi-card" key={kpi.label}>
            <div className="kpi-card__label">{kpi.label}</div>
            <div className="kpi-card__value">{kpi.value}</div>
            <span className={`pill pill--${kpi.tone}`}>{kpi.pill}</span>
          </div>
        ))}
      </div>
    </aside>
  );
}




