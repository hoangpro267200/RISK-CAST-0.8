const submitBtn = document.getElementById("submit-btn");
const statusEl = document.getElementById("status");
const bestCard = document.getElementById("best-option-card");
const altList = document.getElementById("alternative-options");

function setStatus(msg, tone = "info") {
  statusEl.textContent = msg;
  statusEl.style.color = tone === "error" ? "#ff8f8f" : "#8fb8ff";
}

function toIso(dtInput) {
  if (!dtInput) return null;
  const d = new Date(dtInput);
  return d.toISOString();
}

function renderBest(option) {
  if (!option) {
    bestCard.classList.add("empty-state");
    bestCard.innerHTML = "<p>No option available.</p>";
    return;
  }
  bestCard.classList.remove("empty-state");
  bestCard.innerHTML = `
    <div class="card-header">
        <div class="carrier">${option.carrier}</div>
        <div class="price">${option.currency} ${option.totalCost?.toFixed(2)}</div>
    </div>
    <div class="meta">
        <div><strong>Adjusted</strong><br>${option.currency} ${option.adjustedCost?.toFixed(2)}</div>
        <div><strong>ETD</strong><br>${option.etd ? new Date(option.etd).toLocaleString() : "-"}</div>
        <div><strong>POL</strong><br>${option.pol}</div>
        <div><strong>POD</strong><br>${option.pod}</div>
    </div>
    <div class="risk-row">
        Risk — Weather: ${option.risk?.weather_risk ?? option.risk?.weatherRisk ?? 0},
        Congestion: ${option.risk?.congestion_risk ?? option.risk?.congestionRisk ?? 0},
        Carrier: ${option.risk?.carrier_risk ?? option.risk?.carrierRisk ?? 0},
        Total: ${option.risk?.total_risk ?? option.risk?.totalRisk ?? 0}
    </div>
  `;
}

function renderAlts(alts) {
  altList.innerHTML = "";
  if (!alts || !alts.length) {
    altList.innerHTML = '<div class="empty-state card">No alternatives.</div>';
    return;
  }
  alts.forEach((opt) => {
    const row = document.createElement("div");
    row.className = "alt-card";
    row.innerHTML = `
      <div>
        <div class="carrier">${opt.carrier}</div>
        <div class="meta"><span>${opt.pol} → ${opt.pod}</span></div>
      </div>
      <div class="price">${opt.currency} ${opt.adjustedCost?.toFixed(2)}</div>
    `;
    altList.appendChild(row);
  });
}

async function submitQuote() {
  setStatus("Loading...");
  bestCard.classList.add("empty-state");
  altList.innerHTML = "";

  const payload = {
    pol: document.getElementById("pol").value.trim(),
    pod: document.getElementById("pod").value.trim(),
    etd_from: toIso(document.getElementById("etd-from").value),
    etd_to: toIso(document.getElementById("etd-to").value),
    incoterm: document.getElementById("incoterm").value.trim() || null,
    cargo_description: document.getElementById("cargo-description").value.trim() || null,
    weight: parseFloat(document.getElementById("weight").value) || null,
    volume: parseFloat(document.getElementById("volume").value) || null,
  };

  try {
    const res = await fetch("/api/v1/pricing/quote", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderBest(data.best_option || data.bestOption);
    renderAlts(data.alternatives || []);
    setStatus(`Generated at ${new Date(data.generated_at || data.generatedAt).toLocaleString()}`);
  } catch (err) {
    console.error(err);
    setStatus("Failed to fetch pricing quote.", "error");
    bestCard.innerHTML = "<p>Error loading quote.</p>";
  }
}

submitBtn?.addEventListener("click", (e) => {
  e.preventDefault();
  submitQuote();
});









