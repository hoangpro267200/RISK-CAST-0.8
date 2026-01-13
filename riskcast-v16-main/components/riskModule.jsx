import React from "react";
import "../static/css/components/analytics.css";

export default function RiskModule({ title, level = "medium", description, tooltip }) {
  return (
    <div className="risk-module glass-card-md" data-risk-level={level}>
      <div className="panel__header">
        <div className="eyebrow">Risk Module</div>
        <div className="title-sm">{title}</div>
      </div>
      <p className="body">{description}</p>
      <div className="tooltip">{tooltip}</div>
    </div>
  );
}




