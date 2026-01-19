const descEl = document.getElementById("hs-description");
const candidatesEl = document.getElementById("hs-candidates");
const selectedEl = document.getElementById("selected-hs");
const shipmentEl = document.getElementById("shipment-id");
const xmlEl = document.getElementById("xml-output");
const xmlHsEl = document.getElementById("xml-hs");
const profileEl = document.getElementById("customs-profile");
const portFlagsEl = document.getElementById("port-flags");
const copyTipEl = document.getElementById("copy-tip");
let selectedHsCode = null;
let selectedCardEl = null;

function setSelectedCard(card, code) {
  if (selectedCardEl) selectedCardEl.classList.remove("selected");
  selectedCardEl = card;
  selectedHsCode = code;
  if (card) card.classList.add("selected");
  selectedEl.textContent = selectedHsCode || "None";
}

function formatXML(xml) {
  try {
    const PADDING = "  ";
    const reg = /(>)(<)(\/*)/g;
    let xmlStr = xml.replace(reg, "$1\r\n$2$3");
    let pad = 0;
    return xmlStr
      .split("\r\n")
      .map((node) => {
        let indent = 0;
        if (node.match(/.+<\/\w[^>]*>$/)) {
          indent = 0;
        } else if (node.match(/^<\/\w/)) {
          if (pad !== 0) pad -= 1;
        } else if (node.match(/^<\w[^>]*[^\/]>.*$/)) {
          indent = 1;
        } else {
          indent = 0;
        }
        const line = PADDING.repeat(pad) + node;
        pad += indent;
        return line;
      })
      .join("\r\n");
  } catch (e) {
    return xml;
  }
}

function renderCandidates(candidates) {
  candidatesEl.innerHTML = "";
  candidates.forEach((c, idx) => {
    const card = document.createElement("div");
    card.className = "candidate-card";
    card.innerHTML = `
      <div><strong>${c.hs_code || c.hsCode}</strong> - ${c.label}</div>
      <div class="score">${((c.score || 0) * 100).toFixed(0)}%</div>
    `;
    card.onclick = () => {
      setSelectedCard(card, c.hs_code || c.hsCode);
    };
    candidatesEl.appendChild(card);
    if (idx === 0) setSelectedCard(card, c.hs_code || c.hsCode);
  });
}

async function suggestHS() {
  const description = descEl.value.trim();
  if (!description) {
    candidatesEl.innerHTML = "<em>Please enter a description.</em>";
    return;
  }
  candidatesEl.innerHTML = "Loading...";
  try {
    const res = await fetch("/api/v1/customs/hs-suggest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ description }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderCandidates(data.candidates || []);
    if (data.candidates && data.candidates.length) {
      selectedHsCode = data.candidates[0].hs_code || data.candidates[0].hsCode;
      selectedEl.textContent = selectedHsCode;
    }
  } catch (err) {
    candidatesEl.innerHTML = `Error: ${err.message}`;
  }
}

async function generateXML() {
  const shipmentId = shipmentEl.value.trim();
  if (!shipmentId) {
    xmlEl.textContent = "Please enter shipment ID.";
    return;
  }
  xmlEl.textContent = "Generating...";
  try {
    const res = await fetch(`/api/v1/customs/${shipmentId}/declaration-xml`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    xmlHsEl.textContent = data.hs_code || data.hsCode;
    xmlEl.textContent = formatXML(data.declaration_xml || data.declarationXml || "");
    profileEl.textContent = `Created at: ${data.created_at || data.createdAt}`;
    renderPorts(data);
  } catch (err) {
    xmlEl.textContent = `Error: ${err.message}`;
  }
}

async function loadExistingProfile() {
  const shipmentId = shipmentEl.value.trim();
  if (!shipmentId) {
    profileEl.textContent = "Please enter shipment ID.";
    return;
  }
  profileEl.textContent = "Loading...";
  try {
    const res = await fetch(`/api/v1/customs/${shipmentId}`);
    if (res.status === 404) {
      profileEl.textContent = "No customs profile yet.";
      return;
    }
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    xmlHsEl.textContent = data.hs_code || data.hsCode || "-";
    xmlEl.textContent = formatXML(data.declaration_xml || data.declarationXml || "");
    profileEl.textContent = `Created at: ${data.created_at || data.createdAt}`;
    renderPorts(data);
  } catch (err) {
    profileEl.textContent = `Error: ${err.message}`;
  }
}

function copyXML() {
  const text = xmlEl.textContent || "";
  navigator.clipboard.writeText(text);
  if (copyTipEl) {
    copyTipEl.classList.add("show");
    setTimeout(() => copyTipEl.classList.remove("show"), 900);
  }
}

function renderPorts(data) {
  if (!portFlagsEl) return;
  const pol = data.pol || data.pol_port || data.polPort;
  const pod = data.pod || data.pod_port || data.podPort;
  if (!pol && !pod) {
    portFlagsEl.innerHTML = "";
    return;
  }
  const pill = (label, code) => `<span class="port-pill"><span class="flag">🧭</span>${label}: ${code}</span>`;
  portFlagsEl.innerHTML = `
    ${pol ? pill("POL", pol) : ""}
    ${pod ? pill("POD", pod) : ""}
  `;
}

document.getElementById("btn-suggest")?.addEventListener("click", suggestHS);
document.getElementById("btn-generate")?.addEventListener("click", generateXML);
document.getElementById("btn-load-profile")?.addEventListener("click", loadExistingProfile);
document.getElementById("btn-copy")?.addEventListener("click", copyXML);

