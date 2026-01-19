import React from "react";
import "../../static/css/tokens.css";
import "../../static/css/layout.css";
import "../../static/css/glass.css";
import "../../static/css/components/analytics.css";
import "../../static/css/components/sidebar.css";
import "../../static/css/components/header.css";
import "../../static/css/components/tabs.css";
import "../../static/css/components/kpi.css";
import Sidebar from "../../components/sidebar";
import Header from "../../components/header";
import Tabs from "../../components/tabs";
import KpiPanel from "../../components/kpiPanel";
import RiskModule from "../../components/riskModule";

const modules = [
  { title: "Port Congestion", level: "high", description: "High congestion probability in the next 48h.", tooltip: "Neon glow scales with risk." },
  { title: "Weather", level: "medium", description: "Moderate storm window detected on day 3.", tooltip: "Hover for detail." },
  { title: "Carrier Health", level: "low", description: "Carrier SLA adherence strong.", tooltip: "Tooltip fades and slides up." },
  { title: "Security", level: "medium", description: "Route crosses moderate-risk zones.", tooltip: "Review mitigation plan." },
  { title: "Customs", level: "high", description: "Inspection likelihood elevated.", tooltip: "Prepare alternate documentation." },
  { title: "Financial", level: "low", description: "Payment terms stable.", tooltip: "Low glow for low risk." },
];

export default function AnalyticsPage() {
  return (
    <div className="app-shell">
      <Sidebar active="analytics" />
      <main className="main-area">
        <Header />
        <Tabs active="analytics" />
        <section className="main-scroll">
          <section className="tab-panel is-active" data-tab-panel="analytics">
            <div className="grid-analytics">
              {modules.map((mod) => (
                <RiskModule key={mod.title} {...mod} />
              ))}
            </div>
          </section>
        </section>
      </main>
      <KpiPanel />
    </div>
  );
}




