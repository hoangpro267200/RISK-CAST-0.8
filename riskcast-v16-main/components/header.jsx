import React from "react";
import "../static/css/components/header.css";

export default function Header() {
  return (
    <header className="app-header glass-card-md">
      <div className="header__titles">
        <div className="header__eyebrow">Shipment</div>
        <div className="header__title">FutureOS v40 Ultra Vision</div>
      </div>
      <div className="header__badges">
        <span className="badge badge--active">Active</span>
        <span className="badge badge--state">On Track</span>
      </div>
      <div className="header__actions">
        <button className="ghost-btn" data-smart-edit-open>
          Smart Edit
        </button>
        <button className="ghost-btn" data-ai-open>
          AI Assistant
        </button>
        <button className="primary-btn">Run Analysis</button>
      </div>
    </header>
  );
}




