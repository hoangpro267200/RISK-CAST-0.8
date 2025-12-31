import React from "react";
import "../../static/css/tokens.css";
import "../../static/css/layout.css";
import "../../static/css/glass.css";
import "../../static/css/components/transport.css";
import "../../static/css/components/sidebar.css";
import "../../static/css/components/header.css";
import "../../static/css/components/tabs.css";
import "../../static/css/components/kpi.css";
import Sidebar from "../../components/sidebar";
import Header from "../../components/header";
import Tabs from "../../components/tabs";
import KpiPanel from "../../components/kpiPanel";

export default function TransportPage() {
  return (
    <div className="app-shell">
      <Sidebar active="transport" />
      <main className="main-area">
        <Header />
        <Tabs active="transport" />
        <section className="main-scroll">
          <section className="tab-panel is-active" data-tab-panel="transport">
            <div className="grid-transport">
              <div className="glass-card-lg transport__summary">
                <div className="panel__header">
                  <div className="eyebrow">Transport</div>
                  <div className="title-lg">Summary</div>
                </div>
                <p className="body">Reliability and delay risk visualized with bars in a clean grid.</p>
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
        </section>
      </main>
      <KpiPanel />
    </div>
  );
}




