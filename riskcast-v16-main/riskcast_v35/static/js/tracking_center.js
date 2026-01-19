const btnLoad = document.getElementById("btn-load");
const positionEl = document.getElementById("current-position");
const riskEl = document.getElementById("risk-summary");
const eventsEl = document.getElementById("tracking-events");
const markerEl = document.getElementById("map-marker");
const mapImg = document.getElementById("map-img");
const canvas = document.getElementById("risk-chart");

function clearUI() {
  positionEl.textContent = "No data";
  riskEl.textContent = "No data";
  eventsEl.textContent = "No events";
  markerEl.style.display = "none";
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
}

function loadTracking() {
  clearUI();
  const shipmentId = document.getElementById("shipment-id").value.trim();
  if (!shipmentId) {
    positionEl.textContent = "Please enter a shipment ID.";
    return;
  }
  fetch(`/api/v1/tracking/shipment/${shipmentId}`)
    .then((res) => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    })
    .then((data) => renderTracking(data))
    .catch((err) => {
      positionEl.textContent = `Error: ${err.message}`;
    });
}

function renderTracking(data) {
  const latestPos = data.latest_position || data.latestPosition;
  if (latestPos) {
    positionEl.innerHTML = `
      <div><strong>Status:</strong> ${latestPos.status}</div>
      <div><strong>Lat:</strong> ${latestPos.lat.toFixed(4)} | <strong>Lon:</strong> ${latestPos.lon.toFixed(4)}</div>
      <div><strong>Timestamp:</strong> ${new Date(latestPos.timestamp).toLocaleString()}</div>
      <div><strong>Source:</strong> ${latestPos.source}</div>
    `;
    placeMarker(latestPos.lat, latestPos.lon);
  } else {
    positionEl.textContent = "No position yet.";
  }

  const latestRisk = data.latest_risk || data.latestRisk;
  if (latestRisk) {
    riskEl.innerHTML = `
      <div><strong>Total Risk:</strong> ${latestRisk.total_risk ?? latestRisk.totalRisk}</div>
      <div>Weather: ${latestRisk.weather_risk ?? latestRisk.weatherRisk}</div>
      <div>Congestion: ${latestRisk.congestion_risk ?? latestRisk.congestionRisk}</div>
      <div>Carrier: ${latestRisk.carrier_risk ?? latestRisk.carrierRisk}</div>
    `;
  } else {
    riskEl.textContent = "No risk data.";
  }

  drawRiskChart(data.risk_timeline || data.riskTimeline || []);
  renderEvents(data.events || []);
}

function drawRiskChart(points) {
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (!points.length) return;

  const width = canvas.width;
  const height = canvas.height;
  const padding = 30;
  const values = points.map((p) => p.total_risk ?? p.totalRisk ?? 0);
  const times = points.map((p) => new Date(p.timestamp).getTime());
  const minV = Math.min(...values);
  const maxV = Math.max(...values);
  const minT = Math.min(...times);
  const maxT = Math.max(...times);

  const scaleX = (t) => padding + ((t - minT) / (maxT - minT || 1)) * (width - 2 * padding);
  const scaleY = (v) => height - padding - ((v - minV) / (maxV - minV || 1)) * (height - 2 * padding);

  ctx.strokeStyle = "rgba(255,255,255,0.2)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(padding, padding);
  ctx.lineTo(padding, height - padding);
  ctx.lineTo(width - padding, height - padding);
  ctx.stroke();

  ctx.strokeStyle = "#00ffc8";
  ctx.lineWidth = 2;
  ctx.beginPath();
  points.forEach((p, i) => {
    const x = scaleX(new Date(p.timestamp).getTime());
    const y = scaleY(p.total_risk ?? p.totalRisk ?? 0);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
}

function placeMarker(lat, lon) {
  const mapWidth = mapImg.clientWidth;
  const mapHeight = mapImg.clientHeight;
  if (!mapWidth || !mapHeight) return;
  const x = ((lon + 180) * (mapWidth / 360));
  const y = ((lat * -1 + 90) * (mapHeight / 180));
  markerEl.style.left = `${x}px`;
  markerEl.style.top = `${y}px`;
  markerEl.style.display = "block";
}

function renderEvents(events) {
  if (!events.length) {
    eventsEl.textContent = "No events.";
    return;
  }
  eventsEl.innerHTML = "";
  events.forEach((ev) => {
    const row = document.createElement("div");
    row.className = "event-row";
    row.innerHTML = `
      <div><strong>${new Date(ev.timestamp).toLocaleString()}</strong></div>
      <div>Status: ${ev.status} | Source: ${ev.source}</div>
      <div>Lat: ${ev.lat.toFixed(4)} | Lon: ${ev.lon.toFixed(4)}</div>
    `;
    eventsEl.appendChild(row);
  });
}

btnLoad?.addEventListener("click", (e) => {
  e.preventDefault();
  loadTracking();
});









