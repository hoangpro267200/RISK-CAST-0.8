(function () {
  const core = window.RISKCAST_INPUT_CORE;
  const validator = window.RISKCAST_VALIDATION_ENGINE;
  if (!core) return;

  const STORAGE_KEY = "RISKCAST_STATE";
  let state = loadState();

  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        return core.recomputeDerivedState ? core.recomputeDerivedState(parsed) : parsed;
      }
    } catch (e) {
      console.warn("Failed to load state", e);
    }
    return {
      transport: {},
      cargo: {},
      seller: {},
      buyer: {},
      kpi: {},
      risk: {},
      modules: {}
    };
  }

  function saveState(newState) {
    state = core.recomputeDerivedState ? core.recomputeDerivedState(newState) : newState;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) {
      console.warn("Failed to persist state", e);
    }
    window.RISKCAST_STATE = state;
    if (typeof window.refreshInputView === "function") {
      window.refreshInputView(state);
    }
  }

  function applyChange(section, field, rawVal) {
    const parsed = core.parseValueByField(section, field, rawVal);
    const patch = { [section]: { [field]: parsed } };

    // derived updates
    const derived = core.getDerivedUpdates(section, field, parsed, state) || {};
    Object.entries(derived).forEach(([path, val]) => {
      const [sec, fld] = path.split(".");
      if (!patch[sec]) patch[sec] = {};
      patch[sec][fld] = val;
    });

    let next = core.safeUpdateDeep ? core.safeUpdateDeep(state, patch) : { ...state, ...patch };

    // validation & fixes
    const v = validator && validator.validate ? validator.validate(`${section}.${field}`, parsed, next) : null;
    if (v && v.fixes) {
      Object.entries(v.fixes).forEach(([path, val]) => {
        const [sec, fld] = path.split(".");
        if (!next[sec]) next[sec] = {};
        next[sec][fld] = val;
      });
    }
    saveState(next);
    return v;
  }

  function bindInputs() {
    const inputs = document.querySelectorAll("[data-section][data-field]");
    inputs.forEach((el) => {
      const section = el.dataset.section;
      const field = el.dataset.field;
      if (!section || !field) return;
      el.addEventListener("change", (e) => {
        const val = el.type === "checkbox" ? el.checked : el.value;
        const result = applyChange(section, field, val);
        const errorEl = el.closest(".input-field")?.querySelector(".input-error");
        if (errorEl) {
          const err = result?.errors?.[0] || "";
          errorEl.textContent = err;
        }
      });
    });
  }

  function init() {
    window.RISKCAST_STATE = state;
    bindInputs();
    if (typeof window.refreshInputView === "function") {
      window.refreshInputView(state);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();


