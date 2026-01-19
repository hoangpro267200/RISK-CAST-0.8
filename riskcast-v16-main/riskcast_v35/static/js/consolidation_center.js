const modeButtons = document.querySelectorAll(".mode-btn");
const modePanels = document.querySelectorAll(".mode-panel");
const btnGenerate = document.getElementById("btn-generate");
const savingEl = document.getElementById("consolidation-saving");
const metaEl = document.getElementById("plan-meta");
const gridEl = document.getElementById("containers-grid");

function setMode(active) {
  modeButtons.forEach((b) => b.classList.toggle("active", b.dataset.mode === active));
  modePanels.forEach((p) => p.classList.toggle("active", p.id === `mode-${active}`));
}

modeButtons.forEach((btn) => {
  btn.addEventListener("click", () => setMode(btn.dataset.mode));
});

function collectFormData() {
  const activeMode = document.querySelector(".mode-btn.active")?.dataset.mode || "ids";
  const payload = {
    container_capacity_cbm: parseFloat(document.getElementById("container-capacity").value) || 28.0,
    lcl_rate_per_cbm: parseFloat(document.getElementById("lcl-rate").value) || 0,
    fcl_rate_per_container: parseFloat(document.getElementById("fcl-rate").value) || 0,
  };

  if (activeMode === "ids") {
    const idsRaw = document.getElementById("shipment-ids").value;
    payload.shipment_ids = idsRaw
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
  } else {
    payload.pol = document.getElementById("pol").value.trim() || null;
    payload.pod = document.getElementById("pod").value.trim() || null;
    payload.etd_from = document.getElementById("etd-from").value
      ? new Date(document.getElementById("etd-from").value).toISOString()
      : null;
    payload.etd_to = document.getElementById("etd-to").value
      ? new Date(document.getElementById("etd-to").value).toISOString()
      : null;
  }
  return payload;
}

function clearResults() {
  savingEl.innerHTML = "";
  metaEl.innerHTML = "";
  gridEl.innerHTML = `<div class="loading"><div class="spinner"></div><span>Calculating plan...</span></div>`;
}

function renderPlan(data) {
  const savingFmt = (n) => (n != null ? Number(n).toFixed(2) : "0.00");
  const savingPercent = savingFmt(data.saving_percent || data.savingPercent);
  savingEl.innerHTML = `
    <div class="saving-banner glass">
      <div class="banner-left">
        <div class="eyebrow">Plan Savings</div>
        <div class="banner-title">You saved <strong>${savingPercent}%</strong> vs LCL</div>
      </div>
      <div class="saving-pill">-${savingPercent}%</div>
    </div>
    <div class="grid-2 saving-grid">
      <div><div class="eyebrow">Baseline LCL</div><strong>$${savingFmt(data.baseline_lcl_cost || data.baselineLclCost)}</strong></div>
      <div><div class="eyebrow">Optimized FCL</div><strong>$${savingFmt(data.optimized_fcl_cost || data.optimizedFclCost)}</strong></div>
      <div><div class="eyebrow">Saving Amount</div><strong>$${savingFmt(data.saving_amount || data.savingAmount)}</strong></div>
      <div><div class="eyebrow">Saving Percent</div><strong>${savingPercent}%</strong></div>
    </div>
  `;

  metaEl.innerHTML = `
    Plan ID: ${data.plan_id || data.planId}<br>
    Lane: ${data.pol} → ${data.pod}<br>
    Created: ${data.created_at || data.createdAt || "-"}
  `;

  const containers = data.containers || [];
  gridEl.innerHTML = "";
  containers.forEach((c) => {
    const listId = `list-${c.container_id || c.containerId}`;
    const capacityCbm = c.capacity_cbm || c.capacityCbm || data.container_capacity_cbm || data.containerCapacityCbm || 28;
    const capacityWeight = c.capacity_weight || c.capacityWeight || data.capacity_weight || data.capacityWeight || 10000;
    const volUsed = Number(c.total_volume || c.totalVolume || 0);
    const weightUsed = Number(c.total_weight || c.totalWeight || 0);
    const volPercent = Math.min(100, Math.round((volUsed / (capacityCbm || 1)) * 100));
    const weightPercent = Math.min(100, Math.round((weightUsed / (capacityWeight || 1)) * 100));
    const isFull = volPercent >= 90 || weightPercent >= 90;
    const card = document.createElement("div");
    card.className = "glass card container-card";
    if (isFull) card.classList.add("full");
    card.innerHTML = `
      <div class="tag">${c.container_id || c.containerId}</div>
      <h4>Utilization</h4>
      <div class="bars">
        <div class="bar"><div class="bar-fill" style="width:${volPercent}%"></div></div>
        <div class="bar-label">Volume ${volUsed.toFixed(1)} / ${capacityCbm} cbm</div>
        <div class="bar"><div class="bar-fill weight" style="width:${weightPercent}%"></div></div>
        <div class="bar-label">Weight ${weightUsed.toFixed(1)} / ${capacityWeight} kg</div>
      </div>
      <div class="stats">
        <div><strong>Volume</strong><br>${savingFmt(c.total_volume || c.totalVolume)} cbm</div>
        <div><strong>Weight</strong><br>${savingFmt(c.total_weight || c.totalWeight)} kg</div>
        <div><strong>Shipments</strong><br>${(c.shipment_ids || c.shipmentIds || []).length}</div>
      </div>
      <div class="expander" data-target="${listId}">Toggle shipments</div>
      <ul id="${listId}" class="shipment-list">
        ${(c.shipment_ids || c.shipmentIds || [])
          .map((sid) => `<li><span class="flow-dot"></span><span class="flow-arrow">➜</span>${sid}</li>`)
          .join("")}
      </ul>
    `;
    gridEl.appendChild(card);
  });

  gridEl.querySelectorAll(".expander").forEach((exp) => {
    exp.addEventListener("click", () => {
      const target = document.getElementById(exp.dataset.target);
      target?.classList.toggle("open");
    });
  });
}

async function submitConsolidation() {
  clearResults();
  const payload = collectFormData();
  try {
    const res = await fetch("/api/v1/consolidation/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderPlan(data);
  } catch (err) {
    metaEl.innerHTML = `<span class="error">Error: ${err.message}</span>`;
  }
}

btn-generate?.addEventListener("click", (e) => {
  e.preventDefault();
  submitConsolidation();
});

setMode("ids");

