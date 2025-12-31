(function (window) {
  const validator = {};
  window.RISKCAST_VALIDATION_ENGINE = validator;

  const MODE_ALLOWED = {
    SEA: ["20GP", "40GP", "40HC", "40RF", "45HC"],
    AIR: ["ULD_AKE", "ULD_PMC"],
    TRUCK: ["FTL", "LTL"],
    RAIL: ["FCL", "LCL"]
  };

  const CAPACITY_M3 = {
    "20GP": 33,
    "40GP": 67,
    "40HC": 76,
    "40RF": 67,
    "45HC": 85,
    "ULD_AKE": 11.3,
    "ULD_PMC": 26
  };

  function pushFix(fixes, path, val) {
    if (!path) return;
    fixes[path] = val;
  }

  validator.validate = function (fieldPath, value, state) {
    const errors = [];
    const warnings = [];
    const fixes = {};
    const t = state.transport || {};
    const c = state.cargo || {};
    const path = fieldPath || "";

    // Mode vs Container
    if (path.startsWith("transport.mode") || path.startsWith("transport.containerType")) {
      const mode = path === "transport.mode" ? value : t.mode;
      const container = path === "transport.containerType" ? value : t.containerType;
      const allowed = MODE_ALLOWED[mode];
      if (mode && container && allowed && !allowed.includes(container)) {
        errors.push(`Container "${container}" is invalid for mode "${mode}".`);
        if (allowed.length) pushFix(fixes, "transport.containerType", allowed[0]);
      }
    }

    // Dangerous goods + packing
    if (path.startsWith("cargo.dangerousGoods") || path.startsWith("cargo.packingType")) {
      const dg = path === "cargo.dangerousGoods" ? value : c.dangerousGoods;
      const packing = path === "cargo.packingType" ? value : c.packingType;
      if (dg === true && packing && !/crat|drum/i.test(packing)) {
        warnings.push("Dangerous goods should use Crate or Drum packing.");
        pushFix(fixes, "cargo.packingType", "Crate");
      }
    }

    // Incoterm rules
    if (path.startsWith("transport.incoterm") || path.startsWith("transport.incotermLocation")) {
      const incoterm = path === "transport.incoterm" ? value : t.incoterm;
      const loc = path === "transport.incotermLocation" ? value : t.incotermLocation;
      if (incoterm === "EXW" && (!loc || !String(loc).trim())) {
        errors.push("EXW requires seller address/location.");
      }
      if ((incoterm === "CIF" || incoterm === "CIP") && !c.insuranceValue) {
        errors.push("CIF/CIP require cargo insurance value.");
      }
      if ((incoterm === "DAP" || incoterm === "DDP") && (!state.buyer?.address || !String(state.buyer.address).trim())) {
        errors.push("DAP/DDP require buyer address.");
      }
    }

    // POL vs POD
    if (["transport.pol", "transport.pod", "transport.tradeLane"].includes(path)) {
      const pol = path === "transport.pol" ? value : t.pol;
      const pod = path === "transport.pod" ? value : t.pod;
      if (pol && pod && pol === pod) {
        errors.push("POL and POD cannot be the same.");
      }
    }

    // Volume vs container capacity
    if (path.startsWith("cargo.volume") || path.startsWith("cargo.volumeM3") || path.startsWith("transport.containerType")) {
      const container = path === "transport.containerType" ? value : t.containerType;
      const vol = path.startsWith("cargo.volume") ? Number(value) : Number(c.volume || c.volumeM3);
      const cap = CAPACITY_M3[container];
      if (cap && vol && vol > cap) {
        warnings.push(`Volume ${vol} m³ exceeds typical capacity of ${container} (${cap} m³).`);
        if (container !== "45HC") pushFix(fixes, "transport.containerType", "45HC");
      }
    }

    // HS code sensitivity
    if (path === "cargo.hsCode") {
      const hs = String(value || "").trim();
      if (hs.startsWith("09")) pushFix(fixes, "cargo.sensitivity", "Medium");
      if (hs.startsWith("85")) pushFix(fixes, "cargo.sensitivity", "High");
    }

    // Mode vs DG (AIR block)
    if (path === "transport.mode" || path === "cargo.dangerousGoods") {
      const mode = path === "transport.mode" ? value : t.mode;
      const dg = path === "cargo.dangerousGoods" ? value : c.dangerousGoods;
      if (mode === "AIR" && dg === true) {
        errors.push("Dangerous goods are blocked for AIR in this model.");
      }
    }

    // Trade lane vs POL/POD mismatch hint
    if (path === "transport.tradeLane") {
      const lane = String(value || "").toLowerCase();
      const pod = t.pod;
      if (lane.includes("vn_cn") && pod && pod !== "CNSHA") {
        warnings.push("Trade lane vn_cn suggests POD CNSHA.");
        pushFix(fixes, "transport.pod", "CNSHA");
      }
    }

    return { errors, warnings, fixes };
  };
})(window);
