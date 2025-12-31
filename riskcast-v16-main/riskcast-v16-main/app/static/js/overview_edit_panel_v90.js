// Intentionally left blank. User will upload a new implementation.
// Overview Edit Panel v90 - Accessible + Core/Validator Integrated
(function () {
  const panel = document.getElementById("edit-panel") || (function () {
    const el = document.createElement("div");
    el.id = "edit-panel";
    el.className = "edit-panel hidden";
    document.body.appendChild(el);
    return el;
  })();

  const core = window.RISKCAST_INPUT_CORE;
  const validator = window.RISKCAST_VALIDATION_ENGINE;

  if (!core) {
    console.warn("RISKCAST_INPUT_CORE not found – edit panel disabled");
    return;
  }

  if (!window.RISKCAST_STATE) {
    window.RISKCAST_STATE = {
      transport: {},
      cargo: {},
      seller: {},
      buyer: {},
      kpi: {},
      risk: {},
      modules: {}
    };
  }

  // ========== SMALL HELPERS ==========
  function makeInputId(section, field) {
    return `edit-${section}-${field}`.replace(/[^a-zA-Z0-9_-]/g, "_");
  }

  function makeInputName(section, field) {
    return `${section}.${field}`;
  }

  // ------- UI builders with id + name -------
  function buildSelect(options, value, inputId, inputName) {
    const opts = Array.isArray(options) ? options : [];
    const rendered = opts
      .map(opt => {
        const val = typeof opt === "string" ? opt : opt.value;
        const label = typeof opt === "string" ? opt : opt.label;
        const selected = val == value ? "selected" : "";
        return `<option value="${val}" ${selected}>${label}</option>`;
      })
      .join("");
    return `<select class="edit-control" id="${inputId}" name="${inputName}">${rendered}</select>`;
  }

  function buildAutocomplete(portOptions, value, inputId, inputName) {
    const listId = `${inputId}-list`;
    const opts = (portOptions || [])
      .map(
        p =>
          `<option value="${p.code}" label="${p.name} (${p.country})"></option>`
      )
      .join("");

    return `
      <input
        class="edit-control"
        id="${inputId}"
        name="${inputName}"
        list="${listId}"
        value="${value || ""}"
        autocomplete="off"
      />
      <datalist id="${listId}">
        ${opts}
      </datalist>
    `;
  }

  function buildToggle(value, inputId, inputName) {
    const isTrue = value === true || value === "true";
    const hiddenVal = isTrue ? "true" : "false";
    const yesActive = isTrue ? "active" : "";
    const noActive = !isTrue ? "active" : "";

    return `
      <div class="toggle-wrapper">
        <input
          type="hidden"
          class="edit-control"
          id="${inputId}"
          name="${inputName}"
          value="${hiddenVal}"
        />
        <div class="toggle-group" role="radiogroup" aria-labelledby="${inputId}-label">
          <button type="button" class="toggle-btn ${yesActive}" data-val="true">YES</button>
          <button type="button" class="toggle-btn ${noActive}" data-val="false">NO</button>
        </div>
      </div>
    `;
  }

  function buildField(section, field, value) {
    const cfg =
      (core.getFieldConfig && core.getFieldConfig(section, field)) || {
        input: "text",
        type: "string"
      };
    const state = window.RISKCAST_STATE || {};
    const options =
      core.getOptionsForField &&
      core.getOptionsForField(section, field, state);

    const inputId = makeInputId(section, field);
    const inputName = makeInputName(section, field);
    const labelText = cfg.label || `${section}.${field}`;

    let controlHtml = "";

    if (options && options.length) {
      // select từ OPTIONS
      controlHtml = buildSelect(options, value, inputId, inputName);
    } else if (cfg.input === "autocomplete") {
      const ports = (core.OPTIONS && core.OPTIONS.ports) || [];
      controlHtml = buildAutocomplete(ports, value, inputId, inputName);
    } else if (cfg.type === "currency") {
      controlHtml = `
        <input
          class="edit-control"
          id="${inputId}"
          name="${inputName}"
          type="text"
          inputmode="decimal"
          value="${value ?? ""}"
          autocomplete="off"
        />
      `;
    } else if (
      cfg.input === "number" ||
      cfg.type === "number" ||
      cfg.type === "int"
    ) {
      controlHtml = `
        <input
          class="edit-control"
          id="${inputId}"
          name="${inputName}"
          type="number"
          step="any"
          value="${value ?? ""}"
        />
      `;
    } else if (cfg.input === "toggle" || cfg.type === "boolean") {
      controlHtml = buildToggle(value, inputId, inputName);
    } else if (cfg.input === "date" || cfg.type === "date") {
      controlHtml = `
        <input
          class="edit-control"
          id="${inputId}"
          name="${inputName}"
          type="date"
          value="${value || ""}"
        />
      `;
    } else if (cfg.input === "textarea") {
      controlHtml = `
        <textarea
          class="edit-control"
          id="${inputId}"
          name="${inputName}"
          rows="4"
        >${value ?? ""}</textarea>
      `;
    } else {
      controlHtml = `
        <input
          class="edit-control"
          id="${inputId}"
          name="${inputName}"
          type="text"
          value="${value ?? ""}"
          autocomplete="off"
        />
      `;
    }

    return `
      <div
        class="edit-field"
        data-section="${section}"
        data-field="${field}"
        data-type="${cfg.type}"
      >
        <label id="${inputId}-label" for="${inputId}">
          ${labelText}
        </label>
        ${controlHtml}
        <div class="edit-error" aria-live="polite"></div>
      </div>
    `;
  }

  // ---------- TOGGLE BIND ----------
  function bindToggle(fieldEl) {
    if (!fieldEl) return;
    const buttons = fieldEl.querySelectorAll(".toggle-btn");
    const hidden = fieldEl.querySelector("input.edit-control[type='hidden']");
    buttons.forEach(btn => {
      btn.addEventListener("click", () => {
        buttons.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        if (hidden) hidden.value = btn.getAttribute("data-val");
      });
    });
  }

  function closeEditPanel() {
    panel.classList.add("hidden");
    panel.classList.remove("visible");
    panel.innerHTML = "";
  }

  function applyPatchAndRefresh(patch) {
    if (!patch) return;

    if (typeof window.applyStatePatch === "function") {
      window.applyStatePatch(patch);
    } else if (core.safeUpdateDeep) {
      window.RISKCAST_STATE = core.safeUpdateDeep(
        window.RISKCAST_STATE,
        patch
      );
      try {
        localStorage.setItem(
          "RISKCAST_STATE",
          JSON.stringify(window.RISKCAST_STATE)
        );
      } catch (e) {
        console.warn("Failed to persist state", e);
      }
      if (typeof window.rerenderOverview === "function") {
        window.rerenderOverview();
      } else if (typeof window.refreshOverview === "function") {
        window.refreshOverview();
      }
    }

    if (core.recomputeDerivedState) {
      window.RISKCAST_STATE = core.recomputeDerivedState(
        window.RISKCAST_STATE
      );
    }
  }

  function bindPanelEvents(section, field) {
    const closeBtn = panel.querySelector(".edit-panel-close");
    const cancelBtn = panel.querySelector("#edit-cancel");
    const form = panel.querySelector("#edit-panel-form");

    if (closeBtn) closeBtn.addEventListener("click", closeEditPanel);
    if (cancelBtn) cancelBtn.addEventListener("click", closeEditPanel);

    if (form) {
      form.addEventListener("submit", e => {
        e.preventDefault();
        const fieldEl = form.querySelector(".edit-field");
        if (!fieldEl) return;

        const input = fieldEl.querySelector(".edit-control");
        const errorEl = fieldEl.querySelector(".edit-error");
        if (!input) return;

        const rawVal = input.value;
        const parsed =
          core.parseValueByField &&
          core.parseValueByField(section, field, rawVal);

        const v1 =
          core.validateField &&
          core.validateField(section, field, parsed);

        if (v1 && v1.valid === false) {
          if (errorEl) {
            errorEl.textContent = v1.error || "Invalid value";
          }
          return;
        }

        let v2 = { errors: [], fixes: {}, warnings: [] };
        if (validator && typeof validator.validate === "function") {
          v2 = validator.validate(
            `${section}.${field}`,
            parsed,
            window.RISKCAST_STATE || {}
          );
          if (v2.errors && v2.errors.length) {
            if (errorEl) errorEl.textContent = v2.errors[0];
            return;
          }
        }

        if (errorEl) errorEl.textContent = "";

        const patch = { [section]: { [field]: parsed } };

        // derived updates từ core (mode → container, tradeLane → pol/pod...)
        if (core.getDerivedUpdates) {
          const dPatch = core.getDerivedUpdates(
            section,
            field,
            parsed,
            window.RISKCAST_STATE || {}
          );
          if (dPatch && Object.keys(dPatch).length) {
            Object.entries(dPatch).forEach(([path, val]) => {
              const [sec, fld] = path.split(".");
              if (!patch[sec]) patch[sec] = {};
              patch[sec][fld] = val;
            });
          }
        }

        // fixes từ validator
        if (v2.fixes) {
          Object.entries(v2.fixes).forEach(([path, val]) => {
            const [sec, fld] = path.split(".");
            if (!patch[sec]) patch[sec] = {};
            patch[sec][fld] = val;
          });
        }

        applyPatchAndRefresh(patch);
        closeEditPanel();
      });
    }

    const tf = panel.querySelector(".edit-field");
    if (tf && tf.querySelector(".toggle-group")) {
      bindToggle(tf);
    }
  }

  // ---------- PUBLIC API ----------
  function openEditPanel(sectionOrPath, fieldMaybe) {
    if (!sectionOrPath) return;

    let section = sectionOrPath;
    let field = fieldMaybe;

    if (!field) {
      const parts = String(sectionOrPath).split(".");
      section = parts[0];
      field = parts[1];
    }
    if (!section || !field) return;

    const current = (window.RISKCAST_STATE?.[section] || {})[field];
    const displayValue =
      current ??
      (core.formatFieldValue
        ? core.formatFieldValue(section, field, current)
        : current) ??
      "";

    panel.innerHTML = `
      <div class="edit-panel-header">
        <div>
          <div class="edit-panel-title">Edit ${section}.${field}</div>
          <div class="edit-panel-sub">${section}.${field}</div>
        </div>
        <button class="edit-panel-close" aria-label="Close edit panel">&times;</button>
      </div>
      <form id="edit-panel-form">
        ${buildField(section, field, displayValue)}
        <div class="edit-panel-actions">
          <button type="button" class="edit-btn-secondary" id="edit-cancel">Cancel</button>
          <button type="submit" class="edit-btn-primary" id="edit-save">Save</button>
        </div>
      </form>
    `;

    panel.classList.remove("hidden");
    panel.classList.add("visible");

    bindPanelEvents(section, field);

    const firstInput = panel.querySelector(".edit-control");
    if (firstInput) {
      firstInput.focus();
      if (typeof firstInput.select === "function") {
        firstInput.select();
      }
    }
  }

  window.openEditPanel = openEditPanel;
  window.closeEditPanel = closeEditPanel;
})();
// Overview Edit Panel v90 - Clean version using shared core + validator
(() => {
  let panel = document.getElementById("edit-panel");
  if (!panel) {
    panel = document.createElement("div");
    panel.id = "edit-panel";
    panel.className = "edit-panel hidden";
    document.body.appendChild(panel);
  }

  const core = window.RISKCAST_INPUT_CORE;
  const validator = window.RISKCAST_VALIDATION_ENGINE;

  if (!core) {
    console.warn("RISKCAST_INPUT_CORE not found – edit panel disabled");
    return;
  }

  if (!window.RISKCAST_STATE) {
    window.RISKCAST_STATE = {
      transport: {},
      cargo: {},
      seller: {},
      buyer: {},
      kpi: {},
      risk: {},
      modules: {}
    };
  }

  // ---------- helpers ----------
  function buildSelect(options, value) {
    const opts = Array.isArray(options) ? options : [];
    const rendered = opts
      .map(opt => {
        const val = typeof opt === "string" ? opt : opt.value;
        const label = typeof opt === "string" ? opt : opt.label;
        const selected = val == value ? "selected" : "";
        return `<option value="${val}" ${selected}>${label}</option>`;
      })
      .join("");
    return `<select class="edit-control">${rendered}</select>`;
  }

  function buildAutocomplete(options, value) {
    const listId = "autocomplete-" + Math.random().toString(36).slice(2);
    const opts = (options || [])
      .map(
        p =>
          `<option value="${p.code}" label="${p.name} (${p.country})"></option>`
      )
      .join("");
    return `
      <input class="edit-control" list="${listId}" value="${value || ""}" />
      <datalist id="${listId}">
        ${opts}
      </datalist>
    `;
  }

  function buildToggle(value) {
    const isTrue = value === true || value === "true";
    const hiddenVal = isTrue ? "true" : "false";
    const yesActive = isTrue ? "active" : "";
    const noActive = !isTrue ? "active" : "";

    return `
      <div class="toggle-wrapper">
        <input type="hidden" class="edit-control" value="${hiddenVal}" />
        <div class="toggle-group">
          <button type="button" class="toggle-btn ${yesActive}" data-val="true">YES</button>
          <button type="button" class="toggle-btn ${noActive}" data-val="false">NO</button>
        </div>
      </div>
    `;
  }

  function buildField(section, field, value) {
    const cfg = core.getFieldConfig(section, field) || { input: "text", type: "string" };
    const options = core.getOptionsForField(section, field, window.RISKCAST_STATE || {});
    const inputId = `edit-${section}-${field}`;

    let control = "";

    const nameAttr = `name="${section}.${field}"`;
    const idAttr = `id="${inputId}"`;

    if (options && options.length) {
      control = `
      <select class="edit-control" ${idAttr} ${nameAttr}>
        ${options
          .map(opt => {
            const val = typeof opt === "string" ? opt : opt.value;
            const label = typeof opt === "string" ? opt : opt.label;
            const selected = val == value ? "selected" : "";
            return `<option value="${val}" ${selected}>${label}</option>`;
          })
          .join("")}
      </select>
    `;
    } else if (cfg.input === "autocomplete") {
      const listId = "autocomplete-" + Math.random().toString(36).slice(2);
      control = `
      <input class="edit-control" list="${listId}" ${idAttr} ${nameAttr} value="${value || ""}" />
      <datalist id="${listId}">
        ${(core.OPTIONS.ports || [])
          .map(p => `<option value="${p.code}" label="${p.name} (${p.country})"></option>`)
          .join("")}
      </datalist>
    `;
    } else if (cfg.input === "toggle" || cfg.type === "boolean") {
      const isTrue = value === true || value === "true";
      control = `
      <div class="toggle-wrapper">
        <input type="hidden" class="edit-control" ${idAttr} ${nameAttr} value="${isTrue ? "true" : "false"}" />
        <div class="toggle-group">
          <button type="button" class="toggle-btn ${isTrue ? "active" : ""}" data-val="true">YES</button>
          <button type="button" class="toggle-btn ${!isTrue ? "active" : ""}" data-val="false">NO</button>
        </div>
      </div>
    `;
    } else if (cfg.input === "textarea") {
      control = `<textarea class="edit-control" ${idAttr} ${nameAttr} rows="4">${value ?? ""}</textarea>`;
    } else if (cfg.type === "currency") {
      control = `<input class="edit-control" type="text" inputmode="decimal" ${idAttr} ${nameAttr} value="${value ?? ""}" />`;
    } else if (cfg.type === "number" || cfg.input === "number" || cfg.type === "int") {
      control = `<input class="edit-control" type="number" step="any" ${idAttr} ${nameAttr} value="${value ?? ""}" />`;
    } else {
      control = `<input class="edit-control" type="text" ${idAttr} ${nameAttr} value="${value ?? ""}" />`;
    }

    return `
    <div class="edit-field" data-section="${section}" data-field="${field}">
      <label for="${inputId}">${section}.${field}</label>
      ${control}
      <div class="edit-error" aria-live="polite"></div>
    </div>
  `;
  }

  function closeEditPanel() {
    panel.classList.add("hidden");
    panel.classList.remove("visible");
    panel.innerHTML = "";
  }

  function bindToggle(fieldEl) {
    if (!fieldEl) return;
    const buttons = fieldEl.querySelectorAll(".toggle-btn");
    const hidden = fieldEl.querySelector(".edit-control");
    buttons.forEach(btn => {
      btn.addEventListener("click", () => {
        buttons.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        if (hidden) hidden.value = btn.getAttribute("data-val");
      });
    });
  }

  function applyPatchAndRefresh(patch) {
    if (!patch) return;

    if (typeof window.applyStatePatch === "function") {
      window.applyStatePatch(patch);
    } else if (core.safeUpdateDeep) {
      window.RISKCAST_STATE = core.safeUpdateDeep(
        window.RISKCAST_STATE,
        patch
      );
      try {
        localStorage.setItem(
          "RISKCAST_STATE",
          JSON.stringify(window.RISKCAST_STATE)
        );
      } catch (e) {
        console.warn("Failed to persist state", e);
      }
      if (typeof window.rerenderOverview === "function") {
        window.rerenderOverview();
      } else if (typeof window.refreshOverview === "function") {
        window.refreshOverview();
      }
    }

    if (core.recomputeDerivedState) {
      window.RISKCAST_STATE = core.recomputeDerivedState(
        window.RISKCAST_STATE
      );
    }
  }

  function bindPanelEvents(section, field) {
    const closeBtn = panel.querySelector(".edit-panel-close");
    const cancelBtn = panel.querySelector("#edit-cancel");
    const form = panel.querySelector("#edit-panel-form");

    if (closeBtn) closeBtn.addEventListener("click", closeEditPanel);
    if (cancelBtn) cancelBtn.addEventListener("click", closeEditPanel);

    if (form) {
      form.addEventListener("submit", e => {
        e.preventDefault();
        const fieldEl = form.querySelector(".edit-field");
        if (!fieldEl) return;

        const input = fieldEl.querySelector(".edit-control");
        const errorEl = fieldEl.querySelector(".edit-error");
        if (!input) return;

        const rawVal = input.value;
        const parsed = core.parseValueByField(section, field, rawVal);

        // basic type validation
        const v1 = core.validateField(section, field, parsed);
        if (!v1.valid) {
          if (errorEl) errorEl.textContent = v1.error || "Invalid value";
          return;
        }

        // business rules
        let v2 = { errors: [], fixes: {}, warnings: [] };
        if (validator && typeof validator.validate === "function") {
          v2 = validator.validate(
            `${section}.${field}`,
            parsed,
            window.RISKCAST_STATE || {}
          );
          if (v2.errors && v2.errors.length) {
            if (errorEl) errorEl.textContent = v2.errors[0];
            return;
          }
        }

        if (errorEl) errorEl.textContent = "";

        // base patch = field hiện tại
        const patch = { [section]: { [field]: parsed } };

        // derived updates từ core (mode → container, tradeLane → pol/pod...)
        if (core.getDerivedUpdates) {
          const dPatch = core.getDerivedUpdates(
            section,
            field,
            parsed,
            window.RISKCAST_STATE || {}
          );
          if (dPatch && Object.keys(dPatch).length) {
            Object.entries(dPatch).forEach(([path, val]) => {
              const [sec, fld] = path.split(".");
              if (!patch[sec]) patch[sec] = {};
              patch[sec][fld] = val;
            });
          }
        }

        // fixes từ validator
        if (v2.fixes) {
          Object.entries(v2.fixes).forEach(([path, val]) => {
            const [sec, fld] = path.split(".");
            if (!patch[sec]) patch[sec] = {};
            patch[sec][fld] = val;
          });
        }

        applyPatchAndRefresh(patch);
        closeEditPanel();
      });
    }

    // bind toggle (if any)
    const tf = panel.querySelector(".edit-field");
    if (tf && tf.querySelector(".toggle-group")) {
      bindToggle(tf);
    }
  }

  // --------- PUBLIC API ----------
  function openEditPanel(sectionOrPath, fieldMaybe) {
    if (!sectionOrPath) return;

    let section = sectionOrPath;
    let field = fieldMaybe;

    if (!field) {
      const parts = String(sectionOrPath).split(".");
      section = parts[0];
      field = parts[1];
    }
    if (!section || !field) return;

    const current = (window.RISKCAST_STATE?.[section] || {})[field];
    const displayValue =
      current ??
      (core.formatFieldValue
        ? core.formatFieldValue(section, field, current)
        : current) ??
      "";

    panel.innerHTML = `
      <div class="edit-panel-header">
        <div>
          <div class="edit-panel-title">Edit ${section}.${field}</div>
          <div class="edit-panel-sub">${section}.${field}</div>
        </div>
        <button class="edit-panel-close" aria-label="Close edit panel">&times;</button>
      </div>
      <form id="edit-panel-form">
        ${buildField(section, field, displayValue)}
        <div class="edit-panel-actions">
          <button type="button" class="edit-btn-secondary" id="edit-cancel">Cancel</button>
          <button type="submit" class="edit-btn-primary" id="edit-save">Save</button>
        </div>
      </form>
    `;

    panel.classList.remove("hidden");
    panel.classList.add("visible");

    bindPanelEvents(section, field);

    const firstInput = panel.querySelector(".edit-control");
    if (firstInput) {
      firstInput.focus();
      firstInput.select?.();
    }
  }

  window.openEditPanel = openEditPanel;
  window.closeEditPanel = closeEditPanel;
})();

// Prevent bubbling inside panel
(function () {
  const panel = document.getElementById("edit-panel");
  if (panel) {
    panel.addEventListener("click", (e) => {
      e.stopPropagation();
    });
  }
})();

