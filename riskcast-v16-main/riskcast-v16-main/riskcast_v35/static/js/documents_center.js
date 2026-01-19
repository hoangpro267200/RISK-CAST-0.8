const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".tab-panel");
const underline = document.querySelector(".underline");

function activateTab(idx) {
  tabs.forEach((t, i) => {
    t.classList.toggle("active", i === idx);
    panels[i].classList.toggle("active", i === idx);
  });
  underline.style.transform = `translateX(${idx * 100}%)`;
}

tabs.forEach((tab, idx) => {
  tab.addEventListener("click", () => activateTab(idx));
});

function pretty(data) {
  return JSON.stringify(data, null, 2);
}

async function fetchJson(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// SI Generator
const btnGenerateSi = document.getElementById("btn-generate-si");
btnGenerateSi?.addEventListener("click", async () => {
  const shipmentId = document.getElementById("si-shipment-id").value.trim();
  const target = document.getElementById("si-result");
  target.textContent = "Loading...";
  try {
    const data = await fetchJson(`/api/v1/documents/${shipmentId}/si`, { method: "POST" });
    target.textContent = pretty(data);
  } catch (err) {
    target.textContent = `Error: ${err.message}`;
  }
});

// Draft BL
const btnGenerateBl = document.getElementById("btn-generate-bl");
btnGenerateBl?.addEventListener("click", async () => {
  const shipmentId = document.getElementById("bl-shipment-id").value.trim();
  const target = document.getElementById("bl-draft-result");
  target.textContent = "Loading...";
  try {
    const data = await fetchJson(`/api/v1/documents/${shipmentId}/bl-draft`, { method: "POST" });
    target.textContent = pretty(data);
  } catch (err) {
    target.textContent = `Error: ${err.message}`;
  }
});

// Validation
const btnValidate = document.getElementById("btn-validate");
btnValidate?.addEventListener("click", async () => {
  const shipmentId = document.getElementById("validate-shipment-id").value.trim();
  const target = document.getElementById("bl-validate-result");
  target.textContent = "Loading...";
  try {
    const data = await fetchJson(`/api/v1/documents/${shipmentId}/validate-bl`);
    if (data.is_valid) {
      target.innerHTML = `<div class="success">SI and Draft B/L match.</div>`;
    } else {
      const diffs = data.differences || [];
      const list = diffs
        .map(
          (d) =>
            `<li><strong>${d.field}</strong>: SI="${d.si ?? "-"}" vs BL="${d.bl ?? "-"}"</li>`
        )
        .join("");
      target.innerHTML = `<div class="error">Differences found:</div><ul class="diff-list">${list}</ul>`;
    }
  } catch (err) {
    target.textContent = `Error: ${err.message}`;
  }
});

// Default underline position
activateTab(0);









