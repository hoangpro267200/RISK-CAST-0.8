import React from "react";
import "../../static/css/tokens.css";
import "../../static/css/layout.css";
import "../../static/css/glass.css";
import "../../static/css/components/overview.css";
import "../../static/css/components/kpi.css";
import "../../static/css/components/sidebar.css";
import "../../static/css/components/header.css";
import "../../static/css/components/tabs.css";
import "../../static/css/components/transport.css";
import "../../static/css/components/cargo.css";
import "../../static/css/components/analytics.css";
import Sidebar from "../../components/sidebar";
import Header from "../../components/header";
import Tabs from "../../components/tabs";
import KpiPanel from "../../components/kpiPanel";
import RiskModule from "../../components/riskModule";

const quickDimensions = [
  { label: "Route Integrity", value: "92", unit: "%" },
  { label: "Carrier Reliability", value: "88", unit: "%" },
  { label: "Customs Clearance", value: "74", unit: "%" },
  { label: "Weather Buffer", value: "65", unit: "%" },
];

const routeLegs = [
  { label: "Leg 1", value: "Shanghai → Long Beach" },
  { label: "Leg 2", value: "Rail to Chicago" },
  { label: "Leg 3", value: "Final Mile Delivery" },
];

const analyticsModules = [
  { title: "Port Congestion", level: "high", description: "High congestion probability in the next 48h.", tooltip: "Neon glow scales with risk." },
  { title: "Weather", level: "medium", description: "Moderate storm window detected on day 3.", tooltip: "Hover for detail." },
  { title: "Carrier Health", level: "low", description: "Carrier SLA adherence strong.", tooltip: "Tooltip fades and slides up." },
  { title: "Security", level: "medium", description: "Route crosses moderate-risk zones.", tooltip: "Review mitigation plan." },
  { title: "Customs", level: "high", description: "Inspection likelihood elevated.", tooltip: "Prepare alternate documentation." },
  { title: "Financial", level: "low", description: "Payment terms stable.", tooltip: "Low glow for low risk." },
];

export default function OverviewPage() {
  return (
    <div className="app-shell">
      <Sidebar active="overview" />
      <main className="main-area">
        <Header />
        <Tabs active="overview" />
        <section className="main-scroll">
          <section className="tab-panel is-active" data-tab-panel="overview">
            <div className="grid-overview">
              <div className="glass-card-lg overview__risk">
                <div className="panel__header">
                  <div>
                    <div className="eyebrow">Risk Overview</div>
                    <div className="title-lg">Composite Score</div>
                  </div>
                  <span className="badge badge--state">Stable</span>
                </div>
                <div className="risk-score">
                  <div className="score-value">82</div>
                  <div className="score-meter">
                    <div className="score-meter__fill"></div>
                  </div>
                </div>
              </div>

              <div className="glass-card-md overview__quick-grid">
                <div className="panel__header">
                  <div className="eyebrow">Quick Dimensions</div>
                  <div className="title-sm">Drivers</div>
                </div>
                <div className="quick-grid">
                  {quickDimensions.map((item) => (
                    <div className="mini-card" key={item.label}>
                      <div className="label">{item.label}</div>
                      <div className="value">
                        {item.value}
                        <span className="unit">{item.unit}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="glass-card-md overview__pulse">
                <div className="panel__header">
                  <div className="eyebrow">Risk Pulse</div>
                  <div className="title-sm">Live Trend</div>
                </div>
                <div className="pulse-placeholder">Mini-chart placeholder</div>
              </div>

              <div className="glass-card-md overview__route">
                <div className="panel__header">
                  <div className="eyebrow">Route Legs</div>
                  <div className="title-sm">Preview</div>
                </div>
                <ul className="route-list">
                  {routeLegs.map((leg) => (
                    <li key={leg.label}>
                      <span className="label">{leg.label}</span>
                      <span className="value">{leg.value}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </section>

          <section className="tab-panel" data-tab-panel="transport">
            <div className="grid-transport">
              <div className="glass-card-lg transport__summary">
                <div className="panel__header">
                  <div className="eyebrow">Transport</div>
                  <div className="title-lg">Summary</div>
                </div>
                <p className="body">Clean grid with reliability and delay risk bars.</p>
                <div className="bar">
                  <div className="bar__label">Reliability</div>
                  <div className="bar__track">
                    <div className="bar__fill is-success fill-84"></div>
                  </div>
                </div>
                <div className="bar">
                  <div className="bar__label">Delay Risk</div>
                  <div className="bar__track">
                    <div className="bar__fill is-warning fill-36"></div>
                  </div>
                </div>
              </div>

              <div className="glass-card-md transport__insight">
                <div className="panel__header">
                  <div className="eyebrow">AI Insight</div>
                  <div className="title-sm">Gradient Block</div>
                </div>
                <p className="body">Potential congestion at rail hub. Recommend staggered dispatch.</p>
              </div>
            </div>
          </section>

          <section className="tab-panel" data-tab-panel="cargo">
            <div className="grid-cargo">
              <div className="glass-card-lg cargo__profile">
                <div className="panel__header">
                  <div className="eyebrow">Cargo</div>
                  <div className="title-lg">Profile</div>
                </div>
                <p className="body">Temperature, humidity, and vibration metrics displayed below.</p>
                <div className="metric-row">
                  <div className="metric-card">
                    <div className="label">Temperature</div>
                    <div className="value">
                      4.2<span className="unit">°C</span>
                    </div>
                  </div>
                  <div className="metric-card">
                    <div className="label">Humidity</div>
                    <div className="value">
                      58<span className="unit">%</span>
                    </div>
                  </div>
                  <div className="metric-card">
                    <div className="label">Vibration</div>
                    <div className="value">Low</div>
                  </div>
                </div>
              </div>

              <div className="glass-card-md cargo__sensitivity">
                <div className="panel__header">
                  <div className="eyebrow">Sensitivity</div>
                  <div className="title-sm">Alert</div>
                </div>
                <p className="body">Cargo sensitive to rapid humidity swings. Increase monitoring cadence.</p>
              </div>

              <div className="glass-card-md cargo__danger">
                <div className="panel__header">
                  <div className="eyebrow">Dangerous Goods</div>
                  <div className="title-sm">Declaration</div>
                </div>
                <p className="body">All documentation uploaded. No outstanding items.</p>
              </div>
            </div>
          </section>

          <section className="tab-panel" data-tab-panel="analytics">
            <div className="grid-analytics">
              {analyticsModules.map((mod) => (
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




