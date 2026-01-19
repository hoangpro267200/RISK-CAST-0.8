import React from "react";
import "../../static/css/tokens.css";
import "../../static/css/layout.css";
import "../../static/css/glass.css";
import "../../static/css/components/cargo.css";
import "../../static/css/components/sidebar.css";
import "../../static/css/components/header.css";
import "../../static/css/components/tabs.css";
import "../../static/css/components/kpi.css";
import Sidebar from "../../components/sidebar";
import Header from "../../components/header";
import Tabs from "../../components/tabs";
import KpiPanel from "../../components/kpiPanel";

export default function CargoPage() {
  return (
    <div className="app-shell">
      <Sidebar active="cargo" />
      <main className="main-area">
        <Header />
        <Tabs active="cargo" />
        <section className="main-scroll">
          <section className="tab-panel is-active" data-tab-panel="cargo">
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
        </section>
      </main>
      <KpiPanel />
    </div>
  );
}




