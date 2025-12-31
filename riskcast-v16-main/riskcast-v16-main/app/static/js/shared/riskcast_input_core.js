(function (window) {
  const core = {};

  // --- OPTIONS ---
  const MODES = ['SEA', 'AIR', 'TRUCK', 'RAIL'];
  const SHIPMENT_TYPES = ['FCL', 'LCL', 'AIR_GENERAL', 'AIR_EXPRESS', 'TRUCK_FTL', 'TRUCK_LTL', 'RAIL_FCL', 'RAIL_LCL'];
  const INCOTERMS = ['EXW', 'FCA', 'FAS', 'FOB', 'CFR', 'CIF', 'CPT', 'CIP', 'DAP', 'DPU', 'DDP'];
  const CONTAINERS_SEA = ['20GP', '40GP', '40HC', '40RF', '45HC'];
  const CONTAINERS_AIR = ['ULD_AKE', 'ULD_PMC'];
  const CONTAINERS_TRUCK = ['FTL', 'LTL'];
  const CONTAINERS_RAIL = ['FCL', 'LCL'];
  const CONTAINERS = [
    ...CONTAINERS_SEA.map(v => ({ value: v, label: v })),
    ...CONTAINERS_AIR.map(v => ({ value: v, label: v })),
    ...CONTAINERS_TRUCK.map(v => ({ value: v, label: v })),
    ...CONTAINERS_RAIL.map(v => ({ value: v, label: v }))
  ];
  const PACKING = ['Palletized', 'Bulk', 'Bags', 'Carton', 'Crate', 'Drum'];
  const SENSITIVITY = ['Standard', 'Medium', 'High', 'Temperature Controlled', 'Fragile'];
  const INSURANCE = ['All Risks', 'ICC A', 'ICC B', 'ICC C'];
  const STACKABILITY = ['Stackable', 'Non-stackable'];
  const PRIORITIES = ['speed', 'balanced', 'cost'];
  const SCHEDULE = ['Daily', 'Weekly', 'Bi-weekly', 'Monthly'];
  const CARRIERS_BY_MODE = {
    SEA: ['MAERSK', 'CMA CGM', 'ONE', 'MSC'],
    AIR: ['DHL', 'FEDEX', 'UPS', 'SQ'],
    TRUCK: ['DHL Road', 'DB Schenker', 'XPO'],
    RAIL: ['DB Cargo', 'CR Express']
  };

  const PORTS = [
    { code: 'VNSGN', name: 'Sai Gon (HCMC)', country: 'VN' },
    { code: 'CMIT', name: 'Cai Mep', country: 'VN' },
    { code: 'CNSHA', name: 'Shanghai', country: 'CN' },
    { code: 'VNHPH', name: 'Hai Phong', country: 'VN' },
    { code: 'NLRTM', name: 'Rotterdam', country: 'NL' },
    { code: 'SGSIN', name: 'Singapore', country: 'SG' },
    { code: 'HKHKG', name: 'Hong Kong', country: 'HK' },
    { code: 'DEHAM', name: 'Hamburg', country: 'DE' },
    { code: 'USNYC', name: 'New York', country: 'US' },
    { code: 'JPTYO', name: 'Tokyo', country: 'JP' },
    { code: 'KRPUS', name: 'Busan', country: 'KR' },
    { code: 'AEDXB', name: 'Dubai', country: 'AE' },
    { code: 'GBLON', name: 'London', country: 'GB' },
    { code: 'USOAK', name: 'Oakland', country: 'US' },
    { code: 'USSEA', name: 'Seattle', country: 'US' }
  ];

  core.OPTIONS = {
    transport: {
      tradeLane: ['vn_cn', 'vn_kr', 'vn_us', 'vn_in', 'vn_eu'],
      mode: MODES,
      shipmentType: SHIPMENT_TYPES,
      containerTypeSea: CONTAINERS_SEA,
      containerTypeAir: CONTAINERS_AIR,
      containerTypeTruck: CONTAINERS_TRUCK,
      containerTypeRail: CONTAINERS_RAIL,
      priority: PRIORITIES,
      incoterm: INCOTERMS
    },
    cargo: {
      sensitivity: SENSITIVITY
    },
    modes: MODES,
    shipmentTypes: SHIPMENT_TYPES,
    incoterms: INCOTERMS,
    containers: CONTAINERS,
    packingTypes: PACKING,
    sensitivity: SENSITIVITY,
    insuranceCoverage: INSURANCE,
    stackability: STACKABILITY,
    priorities: PRIORITIES,
    scheduleFrequencies: SCHEDULE,
    carriersByMode: CARRIERS_BY_MODE,
    ports: PORTS,
    tradeLanes: [],
    serviceRoutes: []
  };

  // --- FIELD CONFIG ---
  core.FIELD_CONFIG = {
    transport: {
      tradeLane: { type: 'string', input: 'text' },
      mode: { type: 'string', input: 'select', optionsKey: 'modes' },
      shipmentType: { type: 'string', input: 'select', optionsKey: 'shipmentTypes' },
      carrier: { type: 'string', input: 'select', optionsKey: 'carriersByMode' },
      serviceRoute: { type: 'string', input: 'select', optionsKey: 'serviceRoutes' },
      priority: { type: 'string', input: 'select', optionsKey: 'priorities' },
      incoterm: { type: 'string', input: 'select', optionsKey: 'incoterms' },
      incotermLocation: { type: 'string', input: 'text' },
      pol: { type: 'string', input: 'autocomplete', optionsKey: 'ports' },
      pod: { type: 'string', input: 'autocomplete', optionsKey: 'ports' },
      containerType: { type: 'string', input: 'select', optionsKey: 'containers' },
      etd: { type: 'date', input: 'date' },
      eta: { type: 'date', input: 'date' },
      transitTime: { type: 'int', input: 'number' },
      scheduleFrequency: { type: 'string', input: 'select', optionsKey: 'scheduleFrequencies' },
      reliabilityScore: { type: 'int', input: 'number' }
    },
    cargo: {
      cargoType: { type: 'string', input: 'text' },
      hsCode: { type: 'string', input: 'text' },
      packingType: { type: 'string', input: 'select', optionsKey: 'packingTypes' },
      numberOfPackages: { type: 'int', input: 'number' },
      grossWeight: { type: 'number', input: 'number' },
      netWeight: { type: 'number', input: 'number' },
      volumeM3: { type: 'number', input: 'number' },
      stackability: { type: 'string', input: 'select', optionsKey: 'stackability' },
      insuranceValue: { type: 'currency', input: 'number' },
      insuranceCoverage: { type: 'string', input: 'select', optionsKey: 'insuranceCoverage' },
      dangerousGoods: { type: 'boolean', input: 'toggle' },
      description: { type: 'string', input: 'textarea' },
      specialInstructions: { type: 'string', input: 'textarea' },
      volume: { type: 'number', input: 'number' }
    },
    seller: {
      companyName: { type: 'string', input: 'text' },
      businessType: { type: 'string', input: 'text' },
      country: { type: 'string', input: 'text' },
      city: { type: 'string', input: 'text' },
      address: { type: 'string', input: 'text' },
      contactPerson: { type: 'string', input: 'text' },
      contactRole: { type: 'string', input: 'text' },
      email: { type: 'string', input: 'text' },
      phone: { type: 'string', input: 'text' },
      taxId: { type: 'string', input: 'text' }
    },
    buyer: {
      companyName: { type: 'string', input: 'text' },
      businessType: { type: 'string', input: 'text' },
      country: { type: 'string', input: 'text' },
      city: { type: 'string', input: 'text' },
      address: { type: 'string', input: 'text' },
      contactPerson: { type: 'string', input: 'text' },
      contactRole: { type: 'string', input: 'text' },
      email: { type: 'string', input: 'text' },
      phone: { type: 'string', input: 'text' },
      taxId: { type: 'string', input: 'text' }
    },
    kpi: {
      shipmentValue: { type: 'currency', input: 'number' },
      transitDaysPlanned: { type: 'int', input: 'number' },
      transitDaysProjected: { type: 'int', input: 'number' },
      onTimeProbability: { type: 'number', input: 'number' },
      carbonFootprint: { type: 'number', input: 'number' }
    },
    risk: {
      overallScore: { type: 'percent', input: 'number' },
      delayRisk: { type: 'percent', input: 'number' },
      weatherRisk: { type: 'percent', input: 'number' },
      congestionRisk: { type: 'percent', input: 'number' }
    }
  };

  // --- HELPERS ---
  core.getFieldConfig = function (section, field) {
    return (core.FIELD_CONFIG[section] && core.FIELD_CONFIG[section][field]) || null;
  };

  core.getOptionsForField = function (section, field, state = {}) {
    const OPT = core.OPTIONS;
    if (section === "transport" && field === "containerType") {
      const mode = state.transport?.mode;
      if (mode === "AIR") return OPT.transport.containerTypeAir;
      if (mode === "SEA") return OPT.transport.containerTypeSea;
      if (mode === "TRUCK") return OPT.transport.containerTypeTruck;
      if (mode === "RAIL") return OPT.transport.containerTypeRail;
    }
    if (field === "carrier" && section === "transport") {
      const mode = state.transport?.mode;
      if (mode && OPT.carriersByMode[mode]) return OPT.carriersByMode[mode];
    }
    return OPT[section]?.[field] || OPT[field] || null;
  };

  core.getFieldSchema = function (section, field) {
    const cfg = core.FIELD_CONFIG[section]?.[field] || {};
    return {
      input: cfg.input || 'text',
      type: cfg.type || 'string'
    };
  };

  core.suggestValues = function (section, field, query = "", state = {}) {
    const opts = core.getOptionsForField(section, field, state) || [];
    const q = (query || "").toLowerCase();
    if (!q) return opts;
    if (field === "pol" || field === "pod") {
      return (core.OPTIONS.ports || []).filter(p => {
        const text = `${p.code} ${p.name} ${p.country}`.toLowerCase();
        return text.includes(q);
      });
    }
    return opts.filter(opt => String(opt).toLowerCase().includes(q));
  };

  core.getDerivedUpdates = function (section, field, value, state) {
    const patch = {};
    const mode = section === "transport" && field === "mode" ? value : state.transport?.mode;

    // Container auto-fix by mode
    if (section === "transport" && field === "mode") {
      const currentCt = state.transport?.containerType;
      if (value === "AIR" && currentCt && !currentCt.toLowerCase().startsWith("uld")) {
        patch["transport.containerType"] = core.OPTIONS.transport.containerTypeAir[0];
      }
      if (value === "SEA" && currentCt && currentCt.toLowerCase().startsWith("uld")) {
        patch["transport.containerType"] = "20GP";
      }
      if (value === "TRUCK" && currentCt && !["FTL", "LTL"].includes(currentCt)) {
        patch["transport.containerType"] = "FTL";
      }
      if (value === "RAIL" && currentCt && !["FCL", "LCL"].includes(currentCt)) {
        patch["transport.containerType"] = "FCL";
      }
    }

    // Trade lane intelligence
    if (section === "transport" && field === "tradeLane") {
      const lane = String(value || "").toLowerCase();
      if (lane.includes("vn_")) patch["transport.pol"] = "VNSGN";
      if (lane.includes("_cn")) patch["transport.pod"] = "CNSHA";
      if (lane.includes("_kr")) patch["transport.pod"] = "KRPUS";
      if (lane.includes("_us")) patch["transport.pod"] = "USNYC";
      if (lane.includes("_eu")) patch["transport.pod"] = "NLRTM";
    }

    // Incoterm location auto-fill
    if (section === "transport" && field === "incoterm") {
      if (value === "CIF" || value === "CIP") {
        if (state.transport?.pod) patch["transport.incotermLocation"] = state.transport.pod;
      }
      if (value === "EXW") {
        const city = state.seller?.city;
        if (city) patch["transport.incotermLocation"] = city;
      }
    }

    // Weight sanity: net cannot exceed gross
    if (section === "cargo" && (field === "grossWeight" || field === "netWeight")) {
      const gross = field === "grossWeight" ? Number(value || 0) : Number(state.cargo?.grossWeight || 0);
      const net = field === "netWeight" ? Number(value || 0) : Number(state.cargo?.netWeight || 0);
      if (gross && net && net > gross) {
        patch["cargo.netWeight"] = gross;
      }
    }

    return patch;
  };

  core.safeUpdateDeep = function (state, patch) {
    const clone = JSON.parse(JSON.stringify(state || {}));
    Object.entries(patch || {}).forEach(([section, fields]) => {
      if (!clone[section]) clone[section] = {};
      Object.entries(fields || {}).forEach(([k, v]) => {
        clone[section][k] = v;
      });
    });
    if (core.recomputeDerivedState) {
      return core.recomputeDerivedState(clone);
    }
    return clone;
  };

  core.formatTradeLaneForTitle = function (raw) {
    if (!raw) return 'Trade Lane';
    const map = {
      vn: 'Vietnam',
      kr: 'Korea',
      jp: 'Japan',
      cn: 'China',
      us: 'United States',
      eu: 'European Union',
      uk: 'United Kingdom',
      sg: 'Singapore',
      th: 'Thailand',
      my: 'Malaysia',
      id: 'Indonesia',
      de: 'Germany',
      nl: 'Netherlands',
      fr: 'France',
      es: 'Spain',
      it: 'Italy',
      be: 'Belgium',
      ae: 'UAE',
      in: 'India',
      au: 'Australia',
      br: 'Brazil',
      ca: 'Canada',
      mx: 'Mexico'
    };
    const clean = String(raw).toLowerCase().replace(/\s+/g, '').trim();
    const parts = clean.split(/[_\-→>/]+/).filter(Boolean);
    if (parts.length >= 2) {
      const from = map[parts[0]] || parts[0].toUpperCase();
      const to = map[parts[1]] || parts[1].toUpperCase();
      return `${from} → ${to} Trade Lane`;
    }
    if (raw.includes('→') && !/trade lane/i.test(raw)) return `${raw} Trade Lane`;
    return raw.replace(/_/g, ' → ').replace(/-/g, ' → ');
  };

  core.formatFieldValue = function (section, field, value) {
    if (value === null || value === undefined) return '--';
    const cfg = core.getFieldConfig(section, field);
    if (!cfg) return String(value);
    switch (cfg.type) {
      case 'currency':
        if (section === 'cargo' && field === 'insuranceValue') {
          const num = Number(value) || 0;
          return `$${(num / 1_000_000).toFixed(1)}M`;
        }
        return '$' + Number(value || 0).toLocaleString();
      case 'percent':
        return Math.round((value > 1 ? value : value * 100)) + '%';
      case 'date':
        return value;
      case 'volume':
        return `${value || 0} m³`;
      case 'weight':
        return `${value || 0} kg`;
      default:
        return String(value);
    }
  };

  core.parseFieldValue = function (section, field, raw) {
    if (raw === null || raw === undefined || raw === '') return null;
    return core.parseValueByField(section, field, raw);
  };

  core.parseCurrency = function (v) {
    if (!v) return 0;
    return parseFloat(String(v).replace(/[^0-9.]/g, "")) || 0;
  };

  core.normalizeDate = function (v) {
    return v ? String(v).trim() : null;
  };

  core.parseValueByField = function (sectionOrPath, fieldOrValue, rawMaybe) {
    let section = sectionOrPath;
    let field = fieldOrValue;
    let raw = rawMaybe;
    if (rawMaybe === undefined) {
      const path = sectionOrPath;
      raw = fieldOrValue;
      const parts = path.split('.');
      section = parts[0];
      field = parts[1];
    }
    if (raw === null || raw === undefined) return null;
    const value = String(raw).trim();
    if (section === "cargo" && field === "insuranceValue") {
      return core.parseCurrency(value);
    }
    if (["numberOfPackages", "transitTime", "transitDaysProjected", "transitDaysPlanned"].includes(field)) {
      const num = parseInt(value, 10);
      return isNaN(num) ? 0 : num;
    }
    if (["grossWeight", "netWeight", "volume", "volumeM3"].includes(field)) {
      const num = parseFloat(value);
      return isNaN(num) ? 0 : num;
    }
    if (["etd", "eta"].includes(field)) {
      return value || null;
    }
    if (field === "dangerousGoods") {
      return value === "true" || value === true;
    }
    if (field === "insuranceCoverage") return value;
    if (field === "insuranceValue") return core.parseCurrency(value);
    return value;
  };

  core.validateField = function (section, field, value) {
    // Minimal required validation; extend as needed
    const cfg = core.getFieldConfig(section, field);
    if (!cfg) return { valid: true };
    if (cfg.type === 'int' || cfg.type === 'number' || cfg.type === 'volume' || cfg.type === 'weight' || cfg.type === 'currency') {
      if (value === '' || value === null || value === undefined) return { valid: true };
      if (isNaN(value)) return { valid: false, error: 'Must be a number' };
    }
    return { valid: true };
  };

  core.diffDays = function (start, end) {
    const s = new Date(start);
    const e = new Date(end);
    if (isNaN(s) || isNaN(e)) return 0;
    return Math.max(0, Math.round((e.getTime() - s.getTime()) / (1000 * 60 * 60 * 24)));
  };

  core.recomputeDerivedState = function (state) {
    if (!state || typeof state !== 'object') return state;
    const transitTime = state.transport?.transitTime || state.transport?.transitTimeDays || 0;
    const projected = state.kpi?.transitDaysProjected || core.diffDays(state.transport?.etd, state.transport?.eta) || transitTime;
    const reliability = state.transport?.reliabilityScore || 0;
    const delayRisk = state.risk?.delayRisk != null ? state.risk.delayRisk : Math.max(0, 1 - reliability / 100);
    const onTime = state.kpi?.onTimeProbability != null ? state.kpi.onTimeProbability : Math.max(0, Math.min(1, (reliability / 100) * (1 - delayRisk)));
    const grossWeight = state.cargo?.grossWeight || state.cargo?.grossWeightKg || 0;
    const emissionFactor = 0.00008;
    const carbonFootprint = state.kpi?.carbonFootprint || state.shipment?.carbonFootprintTons || +(grossWeight * emissionFactor).toFixed(2);

    state.kpi = state.kpi || {};
    state.shipment = state.shipment || {};
    state.risk = state.risk || {};

    state.kpi.transitDaysPlanned = transitTime;
    state.kpi.transitDaysProjected = projected;
    state.kpi.onTimeProbability = onTime;
    state.kpi.carbonFootprint = carbonFootprint;

    state.shipment.transitPlannedDays = transitTime;
    state.shipment.transitActualDays = projected;
    state.shipment.onTimeProbability = onTime;
    state.shipment.carbonFootprintTons = carbonFootprint;

    if (!state.risk.overallScore) {
      state.risk.overallScore = Math.round((delayRisk || 0) * 100);
    }
    if (!state.risk.delayRisk) state.risk.delayRisk = delayRisk;
    return state;
  };

  core.formatTradeLaneForTitle = function (raw) {
    if (!raw) return 'Trade Lane';
    const map = {
      vn: 'Vietnam',
      kr: 'Korea',
      jp: 'Japan',
      cn: 'China',
      us: 'United States',
      eu: 'European Union',
      uk: 'United Kingdom',
      sg: 'Singapore',
      th: 'Thailand',
      my: 'Malaysia',
      id: 'Indonesia',
      de: 'Germany',
      nl: 'Netherlands',
      fr: 'France',
      es: 'Spain',
      it: 'Italy',
      be: 'Belgium',
      ae: 'UAE',
      in: 'India',
      au: 'Australia',
      br: 'Brazil',
      ca: 'Canada',
      mx: 'Mexico'
    };
    const clean = String(raw).toLowerCase().replace(/\s+/g, '').trim();
    const parts = clean.split(/[_\-→>/]+/).filter(Boolean);
    if (parts.length >= 2) {
      const from = map[parts[0]] || parts[0].toUpperCase();
      const to = map[parts[1]] || parts[1].toUpperCase();
      return `${from} → ${to} Trade Lane`;
    }
    if (raw.includes('→') && !/trade lane/i.test(raw)) return `${raw} Trade Lane`;
    return raw.replace(/_/g, ' → ').replace(/-/g, ' → ');
  };

  window.RISKCAST_INPUT_CORE = core;
})(window);

