function getShipmentId() {
  const root = document.getElementById("shipment-root");
  return root?.dataset.shipmentId;
}

function loadShipmentSummary() {
  const id = getShipmentId();
  if (!id) return;
  fetch(`/api/v1/shipments/${id}/summary`)
    .then((res) => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    })
    .then((data) => renderShipmentSummary(data))
    .catch((err) => {
      document.querySelectorAll(".content").forEach((c) => (c.textContent = `Error: ${err.message}`));
    });
}

function renderShipmentSummary(data) {
  const shipment = data.shipment;
  const pricing = data.pricing;
  const consolidation = data.consolidation;
  const documents = data.documents;
  const tracking = data.tracking;
  const customs = data.customs;

  const pill = document.getElementById("status-pill");
  pill.textContent = shipment.status;
  if (shipment.status?.toLowerCase().includes("active") || shipment.status?.toLowerCase().includes("in_transit")) {
    pill.classList.add("active");
  }

  document.querySelector("#shipment-core .content").innerHTML = `
    <div><strong>Ref:</strong> ${shipment.refCode}</div>
    <div><strong>Shipper:</strong> ${shipment.shipperName}</div>
    <div><strong>Consignee:</strong> ${shipment.consigneeName}</div>
    <div><strong>Lane:</strong> ${shipment.pol} → ${shipment.pod}</div>
    <div><strong>ETD:</strong> ${new Date(shipment.etd).toLocaleString()}</div>
    <div><strong>ETA:</strong> ${shipment.eta ? new Date(shipment.eta).toLocaleString() : "-"}</div>
  `;

  document.querySelector("#shipment-pricing .content").innerHTML = pricing.available && pricing.bestOption
    ? `<div><strong>Carrier:</strong> ${pricing.bestOption.carrier}</div>
       <div><strong>Total:</strong> ${pricing.bestOption.currency || "USD"} ${pricing.bestOption.totalCost ?? "-"}</div>
       <div><strong>Adjusted:</strong> ${pricing.bestOption.currency || "USD"} ${pricing.bestOption.adjustedCost ?? "-"}</div>`
    : "No pricing info yet.";

  document.querySelector("#shipment-consolidation .content").innerHTML = consolidation.available
    ? `<div><strong>Plan:</strong> ${consolidation.planId}</div>
       <div><strong>Containers:</strong> ${consolidation.containersCount ?? "-"}</div>
       <div><strong>Saving %:</strong> ${consolidation.savingPercent ?? 0}%</div>`
    : "Not consolidated yet.";

  const docsContent = document.querySelector("#shipment-documents .content");
  docsContent.innerHTML = "";
  [["SI", documents.si_exists], ["Draft B/L", documents.bl_draft_exists], ["Final B/L", documents.bl_final_exists]].forEach(([label, ok]) => {
    const span = document.createElement("span");
    span.className = `badge ${ok ? "ok" : "missing"}`;
    span.textContent = label;
    docsContent.appendChild(span);
  });

  const trackContent = document.querySelector("#shipment-tracking .content");
  if (tracking.latestPosition) {
    trackContent.innerHTML = `
      <div><strong>Status:</strong> ${tracking.latestPosition.status}</div>
      <div><strong>Lat/Lon:</strong> ${tracking.latestPosition.lat.toFixed(4)}, ${tracking.latestPosition.lon.toFixed(4)}</div>
      <div><strong>Time:</strong> ${new Date(tracking.latestPosition.timestamp).toLocaleString()}</div>
      <div><strong>Total Risk:</strong> ${tracking.latestRisk ? tracking.latestRisk.total_risk ?? tracking.latestRisk.totalRisk : "-"}</div>
    `;
  } else {
    trackContent.textContent = "No tracking data.";
  }

  document.querySelector("#shipment-customs .content").innerHTML = customs.has_customs_profile
    ? `<div><strong>HS Code:</strong> ${customs.hs_code}</div>`
    : "No customs profile.";
}

function bindNavigationButtons() {
  const id = getShipmentId();
  document.getElementById("btn-pricing")?.addEventListener("click", () => {
    window.location.href = "/pricing";
  });
  document.getElementById("btn-consolidation")?.addEventListener("click", () => {
    window.location.href = "/consolidation/ui";
  });
  document.getElementById("btn-documents")?.addEventListener("click", () => {
    window.location.href = "/documents/ui";
  });
  document.getElementById("btn-tracking")?.addEventListener("click", () => {
    window.location.href = "/tracking/ui";
  });
  document.getElementById("btn-customs")?.addEventListener("click", () => {
    window.location.href = "/customs/ui";
  });
}

document.addEventListener("DOMContentLoaded", () => {
  bindNavigationButtons();
  loadShipmentSummary();
});









