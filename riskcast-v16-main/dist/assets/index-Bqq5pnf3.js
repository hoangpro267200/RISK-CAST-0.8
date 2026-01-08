import { r as requireReact, a as requireReactDom } from "./vendor-react-BoEpX7VO.js";
import { r as reactExports, R as RadarChart, P as PolarGrid, a as PolarAngleAxis, b as PolarRadiusAxis, T as Tooltip, c as Radar, d as React, B as BarChart, C as CartesianGrid, X as XAxis, Y as YAxis, e as Bar, f as Cell, A as AreaChart, g as ReferenceLine, h as Area, L as LabelList, S as ScatterChart, i as Scatter } from "./vendor-charts-CurshXyw.js";
(function polyfill() {
  const relList = document.createElement("link").relList;
  if (relList && relList.supports && relList.supports("modulepreload")) return;
  for (const link of document.querySelectorAll('link[rel="modulepreload"]')) processPreload(link);
  new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (mutation.type !== "childList") continue;
      for (const node of mutation.addedNodes) if (node.tagName === "LINK" && node.rel === "modulepreload") processPreload(node);
    }
  }).observe(document, {
    childList: true,
    subtree: true
  });
  function getFetchOpts(link) {
    const fetchOpts = {};
    if (link.integrity) fetchOpts.integrity = link.integrity;
    if (link.referrerPolicy) fetchOpts.referrerPolicy = link.referrerPolicy;
    if (link.crossOrigin === "use-credentials") fetchOpts.credentials = "include";
    else if (link.crossOrigin === "anonymous") fetchOpts.credentials = "omit";
    else fetchOpts.credentials = "same-origin";
    return fetchOpts;
  }
  function processPreload(link) {
    if (link.ep) return;
    link.ep = true;
    const fetchOpts = getFetchOpts(link);
    fetch(link.href, fetchOpts);
  }
})();
var jsxRuntime = { exports: {} };
var reactJsxRuntime_production_min = {};
var hasRequiredReactJsxRuntime_production_min;
function requireReactJsxRuntime_production_min() {
  if (hasRequiredReactJsxRuntime_production_min) return reactJsxRuntime_production_min;
  hasRequiredReactJsxRuntime_production_min = 1;
  var f = requireReact(), k = /* @__PURE__ */ Symbol.for("react.element"), l = /* @__PURE__ */ Symbol.for("react.fragment"), m = Object.prototype.hasOwnProperty, n = f.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED.ReactCurrentOwner, p = { key: true, ref: true, __self: true, __source: true };
  function q(c, a, g) {
    var b, d = {}, e = null, h = null;
    void 0 !== g && (e = "" + g);
    void 0 !== a.key && (e = "" + a.key);
    void 0 !== a.ref && (h = a.ref);
    for (b in a) m.call(a, b) && !p.hasOwnProperty(b) && (d[b] = a[b]);
    if (c && c.defaultProps) for (b in a = c.defaultProps, a) void 0 === d[b] && (d[b] = a[b]);
    return { $$typeof: k, type: c, key: e, ref: h, props: d, _owner: n.current };
  }
  reactJsxRuntime_production_min.Fragment = l;
  reactJsxRuntime_production_min.jsx = q;
  reactJsxRuntime_production_min.jsxs = q;
  return reactJsxRuntime_production_min;
}
var hasRequiredJsxRuntime;
function requireJsxRuntime() {
  if (hasRequiredJsxRuntime) return jsxRuntime.exports;
  hasRequiredJsxRuntime = 1;
  {
    jsxRuntime.exports = requireReactJsxRuntime_production_min();
  }
  return jsxRuntime.exports;
}
var jsxRuntimeExports = requireJsxRuntime();
var client = {};
var hasRequiredClient;
function requireClient() {
  if (hasRequiredClient) return client;
  hasRequiredClient = 1;
  var m = requireReactDom();
  {
    client.createRoot = m.createRoot;
    client.hydrateRoot = m.hydrateRoot;
  }
  return client;
}
var clientExports = requireClient();
function toNumber(value, fallback = 0) {
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : fallback;
  }
  if (typeof value === "string") {
    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }
  if (value === null || value === void 0) {
    return fallback;
  }
  return fallback;
}
function clamp(num, min, max) {
  if (!Number.isFinite(num)) {
    return min;
  }
  return Math.min(max, Math.max(min, num));
}
function toPercent(value) {
  const num = toNumber(value, 0);
  if (num > 1 && num <= 100) {
    return clamp(num, 0, 100);
  }
  const normalized = num * 100;
  return clamp(normalized, 0, 100);
}
function round(num, decimals) {
  if (!Number.isFinite(num)) {
    return 0;
  }
  const factor = 10 ** decimals;
  return Math.round(num * factor) / factor;
}
function isValidISODate(str) {
  if (typeof str !== "string" || str.trim() === "") {
    return false;
  }
  const date = new Date(str);
  if (!Number.isFinite(date.getTime())) {
    return false;
  }
  const isoPattern = /^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d{3})?(Z|[+-]\d{2}:\d{2})?)?$/;
  return isoPattern.test(str.trim());
}
function slugify(str) {
  if (typeof str !== "string") {
    return "";
  }
  return str.toLowerCase().trim().replace(/[^\w\s-]/g, "").replace(/[\s_-]+/g, "-").replace(/^-+|-+$/g, "");
}
function toString(value, fallback = "") {
  if (typeof value === "string") {
    return value;
  }
  if (value === null || value === void 0) {
    return fallback;
  }
  return String(value);
}
function toArray(value, fallback = []) {
  return Array.isArray(value) ? value : fallback;
}
function normalizeRiskLevel(level) {
  const str = toString(level).trim();
  const normalized = str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
  if (normalized === "Low" || normalized === "Medium" || normalized === "High" || normalized === "Critical") {
    return normalized;
  }
  return "Unknown";
}
function adaptResultV2(raw) {
  if (typeof raw !== "object" || raw === null) {
    return createDefaultViewModel(["Invalid input: expected object"]);
  }
  const data = raw;
  const warnings = [];
  const hasData = data.risk_score !== void 0 && data.risk_score !== null || data.profile?.score !== void 0 && data.profile?.score !== null || data.overall_risk !== void 0 && data.overall_risk !== null || Object.keys(data).length > 0 && Object.keys(data).some(
    (key) => key !== "timestamp" && key !== "engine_version" && key !== "language"
  );
  if (!hasData) {
    warnings.push("Empty or invalid data received from backend");
  }
  let canonicalRiskScore = 0;
  let canonicalRiskScoreFrom = "default";
  const profileScore = data.profile?.score;
  const riskScore = data.risk_score;
  const overallRisk = data.overall_risk;
  if (profileScore !== null && profileScore !== void 0) {
    canonicalRiskScore = toPercent(profileScore);
    canonicalRiskScoreFrom = "profile.score";
  } else if (riskScore !== null && riskScore !== void 0) {
    canonicalRiskScore = toPercent(riskScore);
    canonicalRiskScoreFrom = "risk_score";
  } else if (overallRisk !== null && overallRisk !== void 0) {
    canonicalRiskScore = toPercent(overallRisk);
    canonicalRiskScoreFrom = "overall_risk";
  } else {
    warnings.push("Risk score missing - using default 0");
  }
  canonicalRiskScore = round(canonicalRiskScore, 1);
  let canonicalRiskLevel = normalizeRiskLevel(
    data.profile?.level ?? data.risk_level ?? "Unknown"
  );
  let canonicalConfidence = 0;
  const profileConfidence = data.profile?.confidence;
  const confidence = data.confidence;
  if (profileConfidence !== null && profileConfidence !== void 0) {
    canonicalConfidence = toPercent(profileConfidence);
  } else if (confidence !== null && confidence !== void 0) {
    canonicalConfidence = toPercent(confidence);
  }
  canonicalConfidence = Math.round(canonicalConfidence);
  let canonicalDrivers = [];
  let canonicalDriversFrom = "empty";
  if (Array.isArray(data.drivers)) {
    canonicalDrivers = data.drivers;
    canonicalDriversFrom = "drivers";
  } else {
    if (Array.isArray(data.risk_factors) && data.risk_factors.length > 0) {
      canonicalDrivers = data.risk_factors;
      canonicalDriversFrom = "risk_factors";
    } else if (Array.isArray(data.factors) && data.factors.length > 0) {
      canonicalDrivers = data.factors;
      canonicalDriversFrom = "factors";
    }
  }
  const normalizedDrivers = [];
  for (const driver of canonicalDrivers) {
    const driverName = driver?.name;
    if (!driverName || typeof driverName !== "string" || driverName.trim() === "") {
      continue;
    }
    const placeholderNames = ["unknown", "other", "misc", "n/a", "none"];
    if (placeholderNames.includes(driverName.toLowerCase().trim())) {
      continue;
    }
    let impact = toNumber(driver?.impact, 0);
    if (impact <= 1 && impact > 0) {
      impact = impact * 100;
    }
    impact = round(clamp(impact, 0, 100), 1);
    if (impact <= 0) {
      continue;
    }
    normalizedDrivers.push({
      name: driverName.trim(),
      impact,
      description: toString(driver?.description, "")
    });
  }
  if (normalizedDrivers.length > 3) {
    warnings.push(`Driver count exceeds Engine v3 limit (${normalizedDrivers.length} > 3) - this violates engine contract`);
  }
  const impactSum = normalizedDrivers.reduce((sum, d) => sum + d.impact, 0);
  if (normalizedDrivers.length > 0) {
    if (impactSum < 95 || impactSum > 105) {
      warnings.push(
        `Driver impact sum (${impactSum.toFixed(1)}%) is outside expected range [95%, 105%] - relative logic may be violated`
      );
    }
  }
  const shipment = data.shipment ?? {};
  const etd = shipment.etd;
  const eta = shipment.eta;
  const validEtd = isValidISODate(etd) ? toString(etd) : void 0;
  const validEta = isValidISODate(eta) ? toString(eta) : void 0;
  if (etd && !validEtd) {
    warnings.push(`Invalid ETD date: ${etd}`);
  }
  if (eta && !validEta) {
    warnings.push(`Invalid ETA date: ${eta}`);
  }
  const shipmentViewModel = {
    id: toString(shipment.id, `SH-${Date.now()}`),
    route: toString(shipment.route, ""),
    pol: toString(shipment.pol_code ?? shipment.origin, ""),
    pod: toString(shipment.pod_code ?? shipment.destination, ""),
    carrier: toString(shipment.carrier, ""),
    etd: validEtd,
    eta: validEta,
    transitTime: round(toNumber(shipment.transit_time, 0), 0),
    container: toString(shipment.container, ""),
    cargo: toString(shipment.cargo, ""),
    incoterm: toString(shipment.incoterm, ""),
    cargoValue: round(toNumber(shipment.cargo_value ?? shipment.value, 0), 2)
  };
  const riskScoreViewModel = {
    score: canonicalRiskScore,
    level: canonicalRiskLevel,
    confidence: canonicalConfidence
  };
  const profileData = data.profile ?? {};
  const profileFactors = profileData.factors ?? {};
  const normalizedFactors = {};
  for (const [key, value] of Object.entries(profileFactors)) {
    normalizedFactors[key] = round(toPercent(value), 0);
  }
  const profileViewModel = {
    score: round(toPercent(profileData.score ?? canonicalRiskScore), 1),
    level: normalizeRiskLevel(profileData.level ?? canonicalRiskLevel),
    confidence: round(toPercent(profileData.confidence ?? canonicalConfidence), 0),
    explanation: toArray(profileData.explanation, []),
    factors: normalizedFactors,
    matrix: {
      probability: clamp(Math.round(toNumber(profileData.matrix?.probability, 5)), 1, 9),
      severity: clamp(Math.round(toNumber(profileData.matrix?.severity, 5)), 1, 9),
      quadrant: toString(profileData.matrix?.quadrant, "Medium-Medium"),
      description: toString(profileData.matrix?.description, "")
    }
  };
  const reasoningData = data.reasoning ?? {};
  const reasoningExplanation = toString(reasoningData.explanation, "");
  const reasoningViewModel = {
    explanation: reasoningExplanation
  };
  const layers = toArray(data.layers, []);
  const normalizedLayers = layers.map((layer) => ({
    name: toString(layer?.name, "Unknown Layer"),
    score: round(toPercent(layer?.score), 1),
    contribution: round(toPercent(layer?.contribution), 0),
    category: toString(layer?.category, "UNKNOWN"),
    enabled: layer?.enabled !== false
    // Default to true if not specified
  }));
  const projections = toArray(data.riskScenarioProjections, []);
  const normalizedProjections = projections.map((proj) => {
    const p10 = round(toPercent(proj?.p10), 1);
    const p50 = round(toPercent(proj?.p50), 1);
    const p90 = round(toPercent(proj?.p90), 1);
    const sorted = [p10, p50, p90].sort((a, b) => a - b);
    const repaired = {
      p10: sorted[0],
      p50: sorted[1],
      p90: sorted[2]
    };
    const projDate = proj?.date;
    if (p10 > p50 || p50 > p90) {
      warnings.push(`Timeline projection ordering violation at ${projDate ? toString(projDate) : "unknown date"} - repaired`);
    }
    const dateStr = isValidISODate(projDate) ? toString(projDate) : (/* @__PURE__ */ new Date()).toISOString().split("T")[0];
    return {
      date: dateStr,
      p10: repaired.p10,
      p50: repaired.p50,
      p90: repaired.p90,
      phase: toString(proj?.phase, "Unknown")
    };
  });
  const timelineViewModel = {
    projections: normalizedProjections,
    hasData: normalizedProjections.length > 0
  };
  let lossViewModel = null;
  if (data.loss) {
    const loss = data.loss;
    const p95 = toNumber(loss.p95 ?? loss.var95 ?? loss.var_95 ?? loss.VaR95, 0);
    const p99 = toNumber(loss.p99 ?? loss.cvar99 ?? loss.cvar_99 ?? loss.CVaR99, 0);
    const expectedLoss = toNumber(loss.expectedLoss ?? loss.expected_loss ?? loss.el ?? loss.EL, 0);
    const rawTailContribution = loss.tailContribution ?? loss.tail_contribution;
    const tailContribution = rawTailContribution !== void 0 && rawTailContribution !== null ? round(toPercent(rawTailContribution), 1) : 0;
    if (p95 < 0 || p99 < 0 || expectedLoss < 0) {
      warnings.push("Loss metrics contain negative values - clamped to 0");
    }
    lossViewModel = {
      p95: round(Math.max(0, p95), 2),
      p99: round(Math.max(0, p99), 2),
      expectedLoss: round(Math.max(0, expectedLoss), 2),
      tailContribution
    };
  }
  const scenarios = toArray(data.scenarios, []);
  const normalizedScenarios = scenarios.map((scenario, index) => {
    let id = toString(scenario?.id, "");
    if (!id) {
      const title = toString(scenario?.title, "");
      id = title ? slugify(title) : `scenario-${index}`;
    }
    return {
      id,
      title: toString(scenario?.title, "Untitled Scenario"),
      category: toString(scenario?.category, "UNKNOWN"),
      riskReduction: round(toNumber(scenario?.riskReduction, 0), 1),
      costImpact: round(toNumber(scenario?.costImpact, 0), 2),
      isRecommended: Boolean(scenario?.isRecommended),
      rank: Math.round(toNumber(scenario?.rank, 99)),
      description: toString(scenario?.description, "")
    };
  });
  const decisionSummary = data.decision_summary ?? {};
  const insurance = decisionSummary.insurance ?? {};
  const insuranceViewModel = {
    status: toString(insurance.status, "UNKNOWN") || "UNKNOWN",
    recommendation: toString(insurance.recommendation, "N/A") || "N/A",
    rationale: toString(insurance.rationale, "No rationale provided"),
    riskDeltaPoints: insurance.risk_delta_points !== null && insurance.risk_delta_points !== void 0 ? round(toNumber(insurance.risk_delta_points), 1) : null,
    costImpactUsd: insurance.cost_impact_usd !== null && insurance.cost_impact_usd !== void 0 ? round(toNumber(insurance.cost_impact_usd), 2) : null,
    providers: toArray(insurance.providers, [])
  };
  const timing = decisionSummary.timing ?? {};
  const optimalWindow = timing.optimal_window;
  let timingOptimalWindow = null;
  if (optimalWindow && optimalWindow.start && optimalWindow.end) {
    const start = toString(optimalWindow.start);
    const end = toString(optimalWindow.end);
    if (isValidISODate(start) && isValidISODate(end)) {
      timingOptimalWindow = { start, end };
    } else {
      warnings.push(`Invalid timing optimal window dates: ${start}, ${end}`);
    }
  }
  const topLevelTiming = data.timing;
  if (topLevelTiming?.optimalWindow) {
    const window2 = topLevelTiming.optimalWindow;
    if (window2?.start && window2?.end) {
      const start = toString(window2.start);
      const end = toString(window2.end);
      if (isValidISODate(start) && isValidISODate(end)) {
        timingOptimalWindow = { start, end };
      }
    }
  }
  const timingViewModel = {
    status: toString(timing.status, "UNKNOWN") || "UNKNOWN",
    recommendation: toString(timing.recommendation, "N/A") || "N/A",
    rationale: toString(timing.rationale, "No rationale provided"),
    optimalWindow: timingOptimalWindow,
    riskReductionPoints: timing.risk_reduction_points !== null && timing.risk_reduction_points !== void 0 ? round(toNumber(timing.risk_reduction_points), 1) : null,
    costImpactUsd: timing.cost_impact_usd !== null && timing.cost_impact_usd !== void 0 ? round(toNumber(timing.cost_impact_usd), 2) : null
  };
  const routing = decisionSummary.routing ?? {};
  const routingViewModel = {
    status: toString(routing.status, "UNKNOWN") || "UNKNOWN",
    recommendation: toString(routing.recommendation, "N/A") || "N/A",
    rationale: toString(routing.rationale, "No rationale provided"),
    bestAlternative: routing.best_alternative !== null && routing.best_alternative !== void 0 ? toString(routing.best_alternative) : null,
    tradeoff: routing.tradeoff !== null && routing.tradeoff !== void 0 ? toString(routing.tradeoff) : null,
    riskReductionPoints: routing.risk_reduction_points !== null && routing.risk_reduction_points !== void 0 ? round(toNumber(routing.risk_reduction_points), 1) : null,
    costImpactUsd: routing.cost_impact_usd !== null && routing.cost_impact_usd !== void 0 ? round(toNumber(routing.cost_impact_usd), 2) : null
  };
  const decisionsViewModel = {
    insurance: insuranceViewModel,
    timing: timingViewModel,
    routing: routingViewModel
  };
  const metaViewModel = {
    warnings,
    source: {
      canonicalRiskScoreFrom,
      canonicalDriversFrom
    },
    engineVersion: toString(data.engine_version, "v2"),
    language: toString(data.language, "en"),
    timestamp: isValidISODate(data.timestamp) ? toString(data.timestamp) : void 0
  };
  return {
    overview: {
      shipment: shipmentViewModel,
      riskScore: riskScoreViewModel,
      profile: profileViewModel,
      reasoning: reasoningViewModel
    },
    breakdown: {
      layers: normalizedLayers,
      factors: normalizedFactors
    },
    timeline: timelineViewModel,
    decisions: decisionsViewModel,
    loss: lossViewModel,
    scenarios: normalizedScenarios,
    drivers: normalizedDrivers,
    meta: metaViewModel
  };
}
function createDefaultViewModel(warnings) {
  return {
    overview: {
      shipment: {
        id: `SH-${Date.now()}`,
        route: "",
        pol: "",
        pod: "",
        carrier: "",
        etd: void 0,
        eta: void 0,
        transitTime: 0,
        container: "",
        cargo: "",
        incoterm: "",
        cargoValue: 0
      },
      riskScore: {
        score: 0,
        level: "Unknown",
        confidence: 0
      },
      profile: {
        score: 0,
        level: "Unknown",
        confidence: 0,
        explanation: [],
        factors: {},
        matrix: {
          probability: 5,
          severity: 5,
          quadrant: "Medium-Medium",
          description: ""
        }
      },
      reasoning: {
        explanation: ""
      }
    },
    breakdown: {
      layers: [],
      factors: {}
    },
    timeline: {
      projections: [],
      hasData: false
    },
    loss: null,
    scenarios: [],
    drivers: [],
    decisions: {
      insurance: {
        status: "UNKNOWN",
        recommendation: "N/A",
        rationale: "No data available",
        riskDeltaPoints: null,
        costImpactUsd: null,
        providers: []
      },
      timing: {
        status: "UNKNOWN",
        recommendation: "N/A",
        rationale: "No data available",
        optimalWindow: null,
        riskReductionPoints: null,
        costImpactUsd: null
      },
      routing: {
        status: "UNKNOWN",
        recommendation: "N/A",
        rationale: "No data available",
        bestAlternative: null,
        tradeoff: null,
        riskReductionPoints: null,
        costImpactUsd: null
      }
    },
    meta: {
      warnings,
      source: {
        canonicalRiskScoreFrom: "default",
        canonicalDriversFrom: "empty"
      },
      engineVersion: "v2",
      language: "en",
      timestamp: void 0
    }
  };
}
function safeNumber(value, fallback = 0) {
  const n = typeof value === "number" ? value : Number(value);
  return Number.isFinite(n) ? n : fallback;
}
function safeString(value, fallback = "") {
  if (typeof value === "string") return value;
  if (value === null || value === void 0) return fallback;
  return String(value);
}
function safeArray(value, fallback = []) {
  return Array.isArray(value) ? value : fallback;
}
function clampNumber(n, min, max) {
  if (!Number.isFinite(n)) return min;
  return Math.min(max, Math.max(min, n));
}
function safeRatio01(value, fallback = 0) {
  const n = safeNumber(value, fallback);
  return clampNumber(n, 0, 1);
}
function getRiskColor(level) {
  switch (level) {
    case "HIGH":
      return "#ef4444";
    // red-500
    case "MEDIUM":
      return "#f59e0b";
    // amber-500
    case "LOW":
      return "#10b981";
    // emerald-500
    default:
      return "#6b7280";
  }
}
function getRiskGradient(level) {
  switch (level) {
    case "HIGH":
      return ["#dc2626", "#ef4444"];
    // red-600 to red-500
    case "MEDIUM":
      return ["#d97706", "#f59e0b"];
    // amber-600 to amber-500
    case "LOW":
      return ["#059669", "#10b981"];
    // emerald-600 to emerald-500
    default:
      return ["#4b5563", "#6b7280"];
  }
}
const RiskOrbPremium = ({
  score,
  riskLevel = "MEDIUM",
  className = ""
}) => {
  const normalizedScore = reactExports.useMemo(() => clampNumber(safeNumber(score, 0), 0, 100), [score]);
  const color = reactExports.useMemo(() => getRiskColor(riskLevel), [riskLevel]);
  const [gradientStart, gradientEnd] = reactExports.useMemo(() => getRiskGradient(riskLevel), [riskLevel]);
  const pulseIntensity = reactExports.useMemo(() => {
    if (riskLevel === "HIGH") return 1.15;
    if (riskLevel === "MEDIUM") return 1.08;
    return 1.05;
  }, [riskLevel]);
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: `relative flex items-center justify-center ${className}`, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        className: "absolute inset-0 rounded-full opacity-20 blur-3xl",
        style: {
          background: `radial-gradient(circle, ${color}, transparent 70%)`,
          animation: "pulse 3s ease-in-out infinite"
        }
      }
    ),
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        className: "absolute inset-4 rounded-full opacity-30 blur-2xl",
        style: {
          background: `radial-gradient(circle, ${gradientEnd}, transparent 60%)`,
          animation: "pulse 2s ease-in-out infinite"
        }
      }
    ),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "svg",
      {
        width: "280",
        height: "280",
        viewBox: "0 0 280 280",
        className: "relative",
        role: "img",
        "aria-label": `Risk score: ${normalizedScore} out of 100, ${riskLevel.toLowerCase()} risk`,
        children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("defs", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("radialGradient", { id: "orbGradient", cx: "40%", cy: "40%", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("stop", { offset: "0%", stopColor: gradientEnd, stopOpacity: "0.9" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("stop", { offset: "50%", stopColor: color, stopOpacity: "0.7" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("stop", { offset: "100%", stopColor: gradientStart, stopOpacity: "0.5" })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("radialGradient", { id: "shineGradient", cx: "35%", cy: "35%", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("stop", { offset: "0%", stopColor: "white", stopOpacity: "0.4" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("stop", { offset: "50%", stopColor: "white", stopOpacity: "0.1" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("stop", { offset: "100%", stopColor: "white", stopOpacity: "0" })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("filter", { id: "orbShadow", children: /* @__PURE__ */ jsxRuntimeExports.jsx("feDropShadow", { dx: "0", dy: "8", stdDeviation: "12", floodColor: color, floodOpacity: "0.3" }) })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "circle",
            {
              cx: "140",
              cy: "140",
              r: "120",
              fill: "url(#orbGradient)",
              filter: "url(#orbShadow)",
              style: {
                animation: `orbPulse 3s ease-in-out infinite`,
                transformOrigin: "center"
              }
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx("circle", { cx: "140", cy: "140", r: "120", fill: "url(#shineGradient)", opacity: "0.6" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("circle", { cx: "140", cy: "140", r: "100", fill: color, opacity: "0.1" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "text",
            {
              x: "140",
              y: "150",
              textAnchor: "middle",
              fontSize: "56",
              fontWeight: "700",
              fill: "white",
              style: { userSelect: "none" },
              children: normalizedScore
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "text",
            {
              x: "140",
              y: "190",
              textAnchor: "middle",
              fontSize: "16",
              fontWeight: "500",
              fill: "white",
              opacity: "0.8",
              style: { userSelect: "none", letterSpacing: "0.1em" },
              children: riskLevel
            }
          )
        ]
      }
    ),
    /* @__PURE__ */ jsxRuntimeExports.jsx("style", { children: `
        @keyframes orbPulse {
          0%, 100% {
            transform: scale(1);
            opacity: 1;
          }
          50% {
            transform: scale(${pulseIntensity});
            opacity: 0.9;
          }
        }

        @keyframes pulse {
          0%, 100% {
            opacity: 0.2;
            transform: scale(1);
          }
          50% {
            opacity: 0.3;
            transform: scale(1.05);
          }
        }

        @media (prefers-reduced-motion: reduce) {
          @keyframes orbPulse {
            0%, 100% {
              transform: scale(1);
              opacity: 1;
            }
          }
          @keyframes pulse {
            0%, 100% {
              opacity: 0.2;
              transform: scale(1);
            }
          }
        }
      ` })
  ] });
};
const GlassCard = ({
  children,
  padding = "md",
  variant = "default",
  glowColor,
  interactive = false,
  className = ""
}) => {
  const paddingClass = typeof padding === "string" && !["sm", "md", "lg"].includes(padding) ? padding : padding === "sm" ? "p-4" : padding === "lg" ? "p-8" : "p-6";
  const variantClass = variant === "hero" ? "backdrop-blur-3xl bg-white/8 border border-white/15 rounded-3xl shadow-2xl" : variant === "compact" ? "backdrop-blur-lg bg-white/5 border border-white/10 rounded-xl shadow-xl" : "backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl shadow-2xl";
  const interactiveClass = interactive ? "cursor-pointer hover:bg-white/10 hover:border-white/20 transition-all" : "";
  const glowStyle = glowColor ? {
    boxShadow: `0 0 20px ${glowColor}, 0 0 40px ${glowColor}80, 0 0 60px ${glowColor}40`
  } : void 0;
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      className: `${variantClass} ${interactiveClass} ${paddingClass} relative overflow-hidden ${className}`,
      style: glowStyle,
      children: [
        glowColor && /* @__PURE__ */ jsxRuntimeExports.jsx(
          "div",
          {
            className: "absolute inset-0 opacity-20 pointer-events-none",
            style: {
              boxShadow: `0 0 20px ${glowColor}, 0 0 40px ${glowColor}80, 0 0 60px ${glowColor}40`
            }
          }
        ),
        children
      ]
    }
  );
};
function normalizeConfidence(value) {
  const safe = safeRatio01(value > 1 ? value / 100 : value);
  return safe;
}
function getConfidenceColor(confidence) {
  if (confidence >= 0.8) return { main: "#10b981", glow: "rgba(16, 185, 129, 0.4)" };
  if (confidence >= 0.6) return { main: "#f59e0b", glow: "rgba(245, 158, 11, 0.4)" };
  return { main: "#ef4444", glow: "rgba(239, 68, 68, 0.4)" };
}
function getConfidenceLabel(confidence) {
  if (confidence >= 0.8) return "High Confidence";
  if (confidence >= 0.6) return "Medium Confidence";
  return "Low Confidence";
}
const ConfidenceGauge = ({
  confidence,
  label,
  className = "",
  showPercentage = true
}) => {
  const normalized = reactExports.useMemo(() => normalizeConfidence(confidence), [confidence]);
  const percentage = reactExports.useMemo(() => Math.round(normalized * 100), [normalized]);
  const colors = reactExports.useMemo(() => getConfidenceColor(normalized), [normalized]);
  const confidenceLabel = reactExports.useMemo(
    () => label || getConfidenceLabel(normalized),
    [label, normalized]
  );
  const size = 180;
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const center = size / 2;
  const circumference = 2 * Math.PI * radius;
  const arcLength = circumference * 0.75;
  const progressOffset = arcLength - normalized * arcLength;
  return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: `flex flex-col items-center ${className}`, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "relative", style: { width: size, height: size }, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        className: "absolute inset-4 rounded-full blur-xl opacity-30",
        style: { backgroundColor: colors.glow }
      }
    ),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("svg", { width: size, height: size, className: "relative z-10", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("defs", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("linearGradient", { id: "confidenceGradient", x1: "0%", y1: "0%", x2: "100%", y2: "100%", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("stop", { offset: "0%", stopColor: colors.main, stopOpacity: "0.8" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("stop", { offset: "100%", stopColor: colors.main, stopOpacity: "1" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("filter", { id: "dropShadow", x: "-20%", y: "-20%", width: "140%", height: "140%", children: /* @__PURE__ */ jsxRuntimeExports.jsx("feDropShadow", { dx: "0", dy: "0", stdDeviation: "4", floodColor: colors.main, floodOpacity: "0.5" }) })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "circle",
        {
          cx: center,
          cy: center,
          r: radius,
          fill: "none",
          stroke: "rgba(255,255,255,0.1)",
          strokeWidth,
          strokeLinecap: "round",
          strokeDasharray: `${arcLength} ${circumference}`,
          transform: `rotate(135 ${center} ${center})`
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "circle",
        {
          cx: center,
          cy: center,
          r: radius,
          fill: "none",
          stroke: "url(#confidenceGradient)",
          strokeWidth,
          strokeLinecap: "round",
          strokeDasharray: `${arcLength} ${circumference}`,
          strokeDashoffset: progressOffset,
          transform: `rotate(135 ${center} ${center})`,
          filter: "url(#dropShadow)",
          style: {
            transition: "stroke-dashoffset 0.8s ease-out"
          }
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "circle",
        {
          cx: center + radius * Math.cos((135 + normalized * 270) * Math.PI / 180),
          cy: center + radius * Math.sin((135 + normalized * 270) * Math.PI / 180),
          r: strokeWidth / 2 + 2,
          fill: colors.main,
          filter: "url(#dropShadow)"
        }
      )
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "absolute inset-0 flex flex-col items-center justify-center", children: [
      showPercentage && /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "div",
        {
          className: "text-5xl font-bold tracking-tight",
          style: { color: colors.main },
          children: [
            percentage,
            "%"
          ]
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-sm font-medium text-white/80 mt-1", children: confidenceLabel }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs text-white/40 mt-0.5", children: "Data Confidence" })
    ] })
  ] }) });
};
const ChartSkeleton = ({
  height = 400,
  className = ""
}) => {
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    "div",
    {
      className: `flex items-center justify-center ${className}`,
      style: { height: `${height}px`, minHeight: `${height}px` },
      children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex flex-col items-center gap-3 text-white/40", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-8 h-8 border-2 border-white/20 border-t-white/60 rounded-full animate-spin" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs", children: "Loading chart..." })
      ] })
    }
  );
};
function useContainerSize(enabled = true) {
  const ref = reactExports.useRef(null);
  const [size, setSize] = reactExports.useState({
    width: 0,
    height: 0,
    ready: false
  });
  reactExports.useEffect(() => {
    if (!enabled) {
      setSize({ width: 0, height: 0, ready: false });
      return;
    }
    const element = ref.current;
    if (!element) {
      setSize({ width: 0, height: 0, ready: false });
      return;
    }
    const updateSize = () => {
      const rect = element.getBoundingClientRect();
      const width = Math.max(0, Math.floor(rect.width));
      const height = Math.max(0, Math.floor(rect.height));
      const ready = width > 0 && height > 0;
      setSize({ width, height, ready });
    };
    updateSize();
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.target === element) {
          updateSize();
          break;
        }
      }
    });
    resizeObserver.observe(element);
    const intersectionObserver = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.target === element && entry.isIntersecting) {
            requestAnimationFrame(() => {
              requestAnimationFrame(updateSize);
            });
          }
        }
      },
      { threshold: 0.01 }
      // Trigger when any part becomes visible
    );
    intersectionObserver.observe(element);
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        requestAnimationFrame(() => {
          requestAnimationFrame(updateSize);
        });
      }
    };
    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => {
      resizeObserver.disconnect();
      intersectionObserver.disconnect();
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [enabled]);
  return [ref, size];
}
const toKebabCase = (string) => string.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
const mergeClasses = (...classes) => classes.filter((className, index, array) => {
  return Boolean(className) && className.trim() !== "" && array.indexOf(className) === index;
}).join(" ").trim();
var defaultAttributes = {
  xmlns: "http://www.w3.org/2000/svg",
  width: 24,
  height: 24,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round",
  strokeLinejoin: "round"
};
const Icon = reactExports.forwardRef(
  ({
    color = "currentColor",
    size = 24,
    strokeWidth = 2,
    absoluteStrokeWidth,
    className = "",
    children,
    iconNode,
    ...rest
  }, ref) => {
    return reactExports.createElement(
      "svg",
      {
        ref,
        ...defaultAttributes,
        width: size,
        height: size,
        stroke: color,
        strokeWidth: absoluteStrokeWidth ? Number(strokeWidth) * 24 / Number(size) : strokeWidth,
        className: mergeClasses("lucide", className),
        ...rest
      },
      [
        ...iconNode.map(([tag, attrs]) => reactExports.createElement(tag, attrs)),
        ...Array.isArray(children) ? children : [children]
      ]
    );
  }
);
const createLucideIcon = (iconName, iconNode) => {
  const Component = reactExports.forwardRef(
    ({ className, ...props }, ref) => reactExports.createElement(Icon, {
      ref,
      iconNode,
      className: mergeClasses(`lucide-${toKebabCase(iconName)}`, className),
      ...props
    })
  );
  Component.displayName = `${iconName}`;
  return Component;
};
const Activity = createLucideIcon("Activity", [
  [
    "path",
    {
      d: "M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2",
      key: "169zse"
    }
  ]
]);
const Anchor = createLucideIcon("Anchor", [
  ["path", { d: "M12 22V8", key: "qkxhtm" }],
  ["path", { d: "M5 12H2a10 10 0 0 0 20 0h-3", key: "1hv3nh" }],
  ["circle", { cx: "12", cy: "5", r: "3", key: "rqqgnr" }]
]);
const ArrowLeft = createLucideIcon("ArrowLeft", [
  ["path", { d: "m12 19-7-7 7-7", key: "1l729n" }],
  ["path", { d: "M19 12H5", key: "x3x0zl" }]
]);
const ArrowRight = createLucideIcon("ArrowRight", [
  ["path", { d: "M5 12h14", key: "1ays0h" }],
  ["path", { d: "m12 5 7 7-7 7", key: "xquz4c" }]
]);
const ArrowUpDown = createLucideIcon("ArrowUpDown", [
  ["path", { d: "m21 16-4 4-4-4", key: "f6ql7i" }],
  ["path", { d: "M17 20V4", key: "1ejh1v" }],
  ["path", { d: "m3 8 4-4 4 4", key: "11wl7u" }],
  ["path", { d: "M7 4v16", key: "1glfcx" }]
]);
const Award = createLucideIcon("Award", [
  [
    "path",
    {
      d: "m15.477 12.89 1.515 8.526a.5.5 0 0 1-.81.47l-3.58-2.687a1 1 0 0 0-1.197 0l-3.586 2.686a.5.5 0 0 1-.81-.469l1.514-8.526",
      key: "1yiouv"
    }
  ],
  ["circle", { cx: "12", cy: "8", r: "6", key: "1vp47v" }]
]);
const Brain = createLucideIcon("Brain", [
  [
    "path",
    {
      d: "M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z",
      key: "l5xja"
    }
  ],
  [
    "path",
    {
      d: "M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z",
      key: "ep3f8r"
    }
  ],
  ["path", { d: "M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4", key: "1p4c4q" }],
  ["path", { d: "M17.599 6.5a3 3 0 0 0 .399-1.375", key: "tmeiqw" }],
  ["path", { d: "M6.003 5.125A3 3 0 0 0 6.401 6.5", key: "105sqy" }],
  ["path", { d: "M3.477 10.896a4 4 0 0 1 .585-.396", key: "ql3yin" }],
  ["path", { d: "M19.938 10.5a4 4 0 0 1 .585.396", key: "1qfode" }],
  ["path", { d: "M6 18a4 4 0 0 1-1.967-.516", key: "2e4loj" }],
  ["path", { d: "M19.967 17.484A4 4 0 0 1 18 18", key: "159ez6" }]
]);
const Building2 = createLucideIcon("Building2", [
  ["path", { d: "M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z", key: "1b4qmf" }],
  ["path", { d: "M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2", key: "i71pzd" }],
  ["path", { d: "M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2", key: "10jefs" }],
  ["path", { d: "M10 6h4", key: "1itunk" }],
  ["path", { d: "M10 10h4", key: "tcdvrf" }],
  ["path", { d: "M10 14h4", key: "kelpxr" }],
  ["path", { d: "M10 18h4", key: "1ulq68" }]
]);
const Calendar = createLucideIcon("Calendar", [
  ["path", { d: "M8 2v4", key: "1cmpym" }],
  ["path", { d: "M16 2v4", key: "4m81vk" }],
  ["rect", { width: "18", height: "18", x: "3", y: "4", rx: "2", key: "1hopcy" }],
  ["path", { d: "M3 10h18", key: "8toen8" }]
]);
const ChartColumn = createLucideIcon("ChartColumn", [
  ["path", { d: "M3 3v16a2 2 0 0 0 2 2h16", key: "c24i48" }],
  ["path", { d: "M18 17V9", key: "2bz60n" }],
  ["path", { d: "M13 17V5", key: "1frdt8" }],
  ["path", { d: "M8 17v-3", key: "17ska0" }]
]);
const ChartLine = createLucideIcon("ChartLine", [
  ["path", { d: "M3 3v16a2 2 0 0 0 2 2h16", key: "c24i48" }],
  ["path", { d: "m19 9-5 5-4-4-3 3", key: "2osh9i" }]
]);
const Check = createLucideIcon("Check", [["path", { d: "M20 6 9 17l-5-5", key: "1gmf2c" }]]);
const ChevronRight = createLucideIcon("ChevronRight", [
  ["path", { d: "m9 18 6-6-6-6", key: "mthhwq" }]
]);
const CircleAlert = createLucideIcon("CircleAlert", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  ["line", { x1: "12", x2: "12", y1: "8", y2: "12", key: "1pkeuh" }],
  ["line", { x1: "12", x2: "12.01", y1: "16", y2: "16", key: "4dfq90" }]
]);
const CircleCheckBig = createLucideIcon("CircleCheckBig", [
  ["path", { d: "M21.801 10A10 10 0 1 1 17 3.335", key: "yps3ct" }],
  ["path", { d: "m9 11 3 3L22 4", key: "1pflzl" }]
]);
const CircleCheck = createLucideIcon("CircleCheck", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  ["path", { d: "m9 12 2 2 4-4", key: "dzmm74" }]
]);
const CircleX = createLucideIcon("CircleX", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  ["path", { d: "m15 9-6 6", key: "1uzhvr" }],
  ["path", { d: "m9 9 6 6", key: "z0biqf" }]
]);
const Clock = createLucideIcon("Clock", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  ["polyline", { points: "12 6 12 12 16 14", key: "68esgv" }]
]);
const Cloud = createLucideIcon("Cloud", [
  ["path", { d: "M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z", key: "p7xjir" }]
]);
const DollarSign = createLucideIcon("DollarSign", [
  ["line", { x1: "12", x2: "12", y1: "2", y2: "22", key: "7eqyqh" }],
  ["path", { d: "M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6", key: "1b0p4s" }]
]);
const Globe = createLucideIcon("Globe", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  ["path", { d: "M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20", key: "13o1zl" }],
  ["path", { d: "M2 12h20", key: "9i4pu4" }]
]);
const Layers = createLucideIcon("Layers", [
  [
    "path",
    {
      d: "M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83z",
      key: "zw3jo"
    }
  ],
  [
    "path",
    {
      d: "M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12",
      key: "1wduqc"
    }
  ],
  [
    "path",
    {
      d: "M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17",
      key: "kqbvx6"
    }
  ]
]);
const Leaf = createLucideIcon("Leaf", [
  [
    "path",
    {
      d: "M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z",
      key: "nnexq3"
    }
  ],
  ["path", { d: "M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12", key: "mt58a7" }]
]);
const Lightbulb = createLucideIcon("Lightbulb", [
  [
    "path",
    {
      d: "M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5",
      key: "1gvzjb"
    }
  ],
  ["path", { d: "M9 18h6", key: "x1upvd" }],
  ["path", { d: "M10 22h4", key: "ceow96" }]
]);
const MapPin = createLucideIcon("MapPin", [
  [
    "path",
    {
      d: "M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0",
      key: "1r0f0z"
    }
  ],
  ["circle", { cx: "12", cy: "10", r: "3", key: "ilqhr7" }]
]);
const Package = createLucideIcon("Package", [
  [
    "path",
    {
      d: "M11 21.73a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73z",
      key: "1a0edw"
    }
  ],
  ["path", { d: "M12 22V12", key: "d0xqtd" }],
  ["path", { d: "m3.3 7 7.703 4.734a2 2 0 0 0 1.994 0L20.7 7", key: "yx3hmr" }],
  ["path", { d: "m7.5 4.27 9 5.15", key: "1c824w" }]
]);
const Plane = createLucideIcon("Plane", [
  [
    "path",
    {
      d: "M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z",
      key: "1v9wt8"
    }
  ]
]);
const RefreshCw = createLucideIcon("RefreshCw", [
  ["path", { d: "M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8", key: "v9h5vc" }],
  ["path", { d: "M21 3v5h-5", key: "1q7to0" }],
  ["path", { d: "M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16", key: "3uifl3" }],
  ["path", { d: "M8 16H3v5", key: "1cv678" }]
]);
const Save = createLucideIcon("Save", [
  [
    "path",
    {
      d: "M15.2 3a2 2 0 0 1 1.4.6l3.8 3.8a2 2 0 0 1 .6 1.4V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z",
      key: "1c8476"
    }
  ],
  ["path", { d: "M17 21v-7a1 1 0 0 0-1-1H8a1 1 0 0 0-1 1v7", key: "1ydtos" }],
  ["path", { d: "M7 3v4a1 1 0 0 0 1 1h7", key: "t51u73" }]
]);
const Search = createLucideIcon("Search", [
  ["circle", { cx: "11", cy: "11", r: "8", key: "4ej97u" }],
  ["path", { d: "m21 21-4.3-4.3", key: "1qie3q" }]
]);
const Shield = createLucideIcon("Shield", [
  [
    "path",
    {
      d: "M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z",
      key: "oel41y"
    }
  ]
]);
const Ship = createLucideIcon("Ship", [
  ["path", { d: "M12 10.189V14", key: "1p8cqu" }],
  ["path", { d: "M12 2v3", key: "qbqxhf" }],
  ["path", { d: "M19 13V7a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v6", key: "qpkstq" }],
  [
    "path",
    {
      d: "M19.38 20A11.6 11.6 0 0 0 21 14l-8.188-3.639a2 2 0 0 0-1.624 0L3 14a11.6 11.6 0 0 0 2.81 7.76",
      key: "7tigtc"
    }
  ],
  [
    "path",
    {
      d: "M2 21c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1s1.2 1 2.5 1c2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1",
      key: "1924j5"
    }
  ]
]);
const Target = createLucideIcon("Target", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  ["circle", { cx: "12", cy: "12", r: "6", key: "1vlfrh" }],
  ["circle", { cx: "12", cy: "12", r: "2", key: "1c9p78" }]
]);
const TramFront = createLucideIcon("TramFront", [
  ["rect", { width: "16", height: "16", x: "4", y: "3", rx: "2", key: "1wxw4b" }],
  ["path", { d: "M4 11h16", key: "mpoxn0" }],
  ["path", { d: "M12 3v8", key: "1h2ygw" }],
  ["path", { d: "m8 19-2 3", key: "13i0xs" }],
  ["path", { d: "m18 22-2-3", key: "1p0ohu" }],
  ["path", { d: "M8 15h.01", key: "a7atzg" }],
  ["path", { d: "M16 15h.01", key: "rnfrdf" }]
]);
const TrendingDown = createLucideIcon("TrendingDown", [
  ["polyline", { points: "22 17 13.5 8.5 8.5 13.5 2 7", key: "1r2t7k" }],
  ["polyline", { points: "16 17 22 17 22 11", key: "11uiuu" }]
]);
const TrendingUp = createLucideIcon("TrendingUp", [
  ["polyline", { points: "22 7 13.5 15.5 8.5 10.5 2 17", key: "126l90" }],
  ["polyline", { points: "16 7 22 7 22 13", key: "kwv8wd" }]
]);
const TriangleAlert = createLucideIcon("TriangleAlert", [
  [
    "path",
    {
      d: "m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3",
      key: "wmoenq"
    }
  ],
  ["path", { d: "M12 9v4", key: "juzpu7" }],
  ["path", { d: "M12 17h.01", key: "p32p05" }]
]);
const Truck = createLucideIcon("Truck", [
  ["path", { d: "M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2", key: "wrbu53" }],
  ["path", { d: "M15 18H9", key: "1lyqi6" }],
  [
    "path",
    {
      d: "M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14",
      key: "lysw3i"
    }
  ],
  ["circle", { cx: "17", cy: "18", r: "2", key: "332jqn" }],
  ["circle", { cx: "7", cy: "18", r: "2", key: "19iecd" }]
]);
const User = createLucideIcon("User", [
  ["path", { d: "M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2", key: "975kel" }],
  ["circle", { cx: "12", cy: "7", r: "4", key: "17ys0d" }]
]);
const X = createLucideIcon("X", [
  ["path", { d: "M18 6 6 18", key: "1bl5f8" }],
  ["path", { d: "m6 6 12 12", key: "d8bk6v" }]
]);
const Zap = createLucideIcon("Zap", [
  [
    "path",
    {
      d: "M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z",
      key: "1xq2db"
    }
  ]
]);
const CustomTooltip$3 = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const score = data.value;
    const riskLevel = score >= 70 ? "High" : score >= 40 ? "Medium" : "Low";
    const riskColor = score >= 70 ? "text-red-400" : score >= 40 ? "text-amber-400" : "text-emerald-400";
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "bg-black/95 backdrop-blur-xl border border-white/20 rounded-xl p-4 shadow-2xl min-w-[180px]", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "font-medium text-white mb-2 pb-2 border-b border-white/10", children: data.name }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-2", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex justify-between items-center", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/60 text-sm", children: "Score" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: `font-bold ${riskColor}`, children: score })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex justify-between items-center", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/60 text-sm", children: "Risk Level" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: `text-sm font-medium ${riskColor}`, children: riskLevel })
        ] }),
        data.category && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex justify-between items-center", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/60 text-sm", children: "Category" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/80 text-sm", children: data.category })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "mt-3 pt-2 border-t border-white/10", children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "h-1.5 bg-white/10 rounded-full overflow-hidden", children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        "div",
        {
          className: `h-full rounded-full transition-all duration-500 ${score >= 70 ? "bg-gradient-to-r from-red-500 to-red-400" : score >= 40 ? "bg-gradient-to-r from-amber-500 to-amber-400" : "bg-gradient-to-r from-emerald-500 to-emerald-400"}`,
          style: { width: `${score}%` }
        }
      ) }) })
    ] });
  }
  return null;
};
const RiskBadge = ({ score, label }) => {
  const Icon2 = score >= 70 ? CircleAlert : score >= 40 ? TrendingUp : CircleCheckBig;
  const colors = score >= 70 ? "bg-red-500/20 text-red-400 border-red-500/30" : score >= 40 ? "bg-amber-500/20 text-amber-400 border-amber-500/30" : "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: `flex items-center gap-1.5 px-2.5 py-1 rounded-full border ${colors} text-xs font-medium`, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(Icon2, { className: "w-3 h-3" }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: label })
  ] });
};
const RiskRadar = ({ layers }) => {
  const [containerRef, containerSize] = useContainerSize();
  if (!layers || layers.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(GlassCard, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-center py-12 text-white/60", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Target, { className: "w-12 h-12 mx-auto mb-4 opacity-30" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm", children: "No layer data available" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-white/30 mt-1", children: "Layer data is required for this chart" })
    ] }) });
  }
  const data = layers.filter((layer) => layer != null).map((layer) => ({
    name: (layer.name || "Unknown").replace(" Risk", ""),
    value: layer.score ?? 0,
    fullMark: 100,
    category: layer.category || "Unknown"
  }));
  const avgScore = Math.round(data.reduce((sum, d) => sum + d.value, 0) / data.length);
  const maxScore = Math.max(...data.map((d) => d.value));
  const minScore = Math.min(...data.map((d) => d.value));
  const highRiskCount = data.filter((d) => d.value >= 70).length;
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { className: "overflow-hidden", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between mb-4", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-3", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "p-2 rounded-lg bg-gradient-to-br from-blue-500/20 to-cyan-500/20 border border-blue-500/30", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Target, { className: "w-5 h-5 text-blue-400" }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-lg font-semibold text-white", children: "Risk Profile Radar" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: "text-xs text-white/50", children: [
            data.length,
            " risk dimensions analyzed"
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        RiskBadge,
        {
          score: avgScore,
          label: avgScore >= 70 ? "High Risk" : avgScore >= 40 ? "Moderate" : "Low Risk"
        }
      )
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-4 gap-3 mb-4", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-center p-2 rounded-lg bg-white/5 border border-white/10", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-lg font-bold text-white", children: avgScore }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-[10px] text-white/40 uppercase", children: "Average" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-center p-2 rounded-lg bg-white/5 border border-white/10", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-lg font-bold text-red-400", children: maxScore }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-[10px] text-white/40 uppercase", children: "Highest" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-center p-2 rounded-lg bg-white/5 border border-white/10", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-lg font-bold text-emerald-400", children: minScore }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-[10px] text-white/40 uppercase", children: "Lowest" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-center p-2 rounded-lg bg-white/5 border border-white/10", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-lg font-bold text-amber-400", children: highRiskCount }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-[10px] text-white/40 uppercase", children: "High Risk" })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        ref: containerRef,
        className: "relative",
        style: { height: "350px", minHeight: "350px", minWidth: "300px", width: "100%" },
        children: containerSize.ready && containerSize.width > 0 && containerSize.height > 0 ? /* @__PURE__ */ jsxRuntimeExports.jsxs(
          RadarChart,
          {
            width: containerSize.width,
            height: containerSize.height,
            data,
            margin: { top: 20, right: 30, bottom: 20, left: 30 },
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("defs", { children: [
                /* @__PURE__ */ jsxRuntimeExports.jsxs("linearGradient", { id: "radarGradient", x1: "0", y1: "0", x2: "0", y2: "1", children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("stop", { offset: "0%", stopColor: "#3B82F6", stopOpacity: 0.8 }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("stop", { offset: "100%", stopColor: "#06B6D4", stopOpacity: 0.2 })
                ] }),
                /* @__PURE__ */ jsxRuntimeExports.jsxs("filter", { id: "radarGlow", children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("feGaussianBlur", { stdDeviation: "2", result: "coloredBlur" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsxs("feMerge", { children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx("feMergeNode", { in: "coloredBlur" }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("feMergeNode", { in: "SourceGraphic" })
                  ] })
                ] })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                PolarGrid,
                {
                  stroke: "rgba(255,255,255,0.1)",
                  gridType: "polygon"
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                PolarAngleAxis,
                {
                  dataKey: "name",
                  tick: {
                    fill: "rgba(255,255,255,0.7)",
                    fontSize: 11,
                    fontWeight: 500
                  },
                  tickLine: false
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                PolarRadiusAxis,
                {
                  angle: 90,
                  domain: [0, 100],
                  tick: { fill: "rgba(255,255,255,0.4)", fontSize: 9 },
                  tickCount: 5,
                  axisLine: false
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(Tooltip, { content: /* @__PURE__ */ jsxRuntimeExports.jsx(CustomTooltip$3, {}) }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                Radar,
                {
                  name: "High Risk Zone",
                  dataKey: "fullMark",
                  stroke: "none",
                  fill: "rgba(239, 68, 68, 0.05)",
                  fillOpacity: 1
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                Radar,
                {
                  name: "Risk Score",
                  dataKey: "value",
                  stroke: "#3B82F6",
                  fill: "url(#radarGradient)",
                  fillOpacity: 0.6,
                  strokeWidth: 2,
                  filter: "url(#radarGlow)",
                  animationDuration: 1500,
                  animationEasing: "ease-out",
                  dot: {
                    r: 4,
                    fill: "#3B82F6",
                    stroke: "#fff",
                    strokeWidth: 2
                  },
                  activeDot: {
                    r: 6,
                    fill: "#3B82F6",
                    stroke: "#fff",
                    strokeWidth: 2
                  }
                }
              )
            ]
          }
        ) : /* @__PURE__ */ jsxRuntimeExports.jsx(ChartSkeleton, { height: 350 })
      }
    ),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-center gap-6 mt-2 pt-3 border-t border-white/10", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-3 h-3 rounded-full bg-emerald-500" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-white/50", children: "Low (<40)" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-3 h-3 rounded-full bg-amber-500" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-white/50", children: "Medium (40-69)" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-3 h-3 rounded-full bg-red-500" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-white/50", children: "High (≥70)" })
      ] })
    ] })
  ] });
};
const CATEGORY_COLORS = {
  "TRANSPORT": { primary: "#3B82F6", gradient: "from-blue-500 to-blue-600" },
  "CARGO": { primary: "#8B5CF6", gradient: "from-violet-500 to-purple-600" },
  "COMMERCIAL": { primary: "#10B981", gradient: "from-emerald-500 to-green-600" },
  "COMPLIANCE": { primary: "#F59E0B", gradient: "from-amber-500 to-orange-600" },
  "EXTERNAL": { primary: "#EC4899", gradient: "from-pink-500 to-rose-600" }
};
const CustomTooltip$2 = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const categoryColor = CATEGORY_COLORS[data.category]?.primary || "#6B7280";
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "bg-black/95 backdrop-blur-xl border border-white/20 rounded-xl p-4 shadow-2xl min-w-[200px]", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 mb-3 pb-2 border-b border-white/10", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "div",
          {
            className: "w-3 h-3 rounded-full",
            style: { backgroundColor: categoryColor }
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "font-medium text-white", children: data.name })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-2", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex justify-between", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/60 text-sm", children: "Contribution" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "font-bold text-cyan-400", children: [
            data.contribution,
            "%"
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex justify-between", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/60 text-sm", children: "Layer Score" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: `font-semibold ${data.score >= 70 ? "text-red-400" : data.score >= 40 ? "text-amber-400" : "text-emerald-400"}`, children: data.score })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex justify-between", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/60 text-sm", children: "Category" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/80 text-sm", children: data.category })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex justify-between", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/60 text-sm", children: "Cumulative" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "text-white/80 text-sm", children: [
            data.cumulative.toFixed(1),
            "%"
          ] })
        ] })
      ] })
    ] });
  }
  return null;
};
function RiskContributionWaterfall({ layers, overallScore, onBarClick }) {
  const [containerRef, containerSize] = useContainerSize();
  const [hoveredBar, setHoveredBar] = reactExports.useState(null);
  const sortedLayers = React.useMemo(() => {
    if (!layers || layers.length === 0) return [];
    return layers.slice().sort((a, b) => (b.contribution ?? 0) - (a.contribution ?? 0));
  }, [layers]);
  const waterfallData = React.useMemo(() => {
    if (sortedLayers.length === 0) return [];
    return sortedLayers.reduce((acc, layer, idx) => {
      const prevValue = idx === 0 ? 0 : acc[idx - 1]?.cumulative ?? 0;
      const contribution = layer.contribution ?? 0;
      acc.push({
        name: (layer.name || "").replace(" Risk", ""),
        value: contribution,
        cumulative: prevValue + contribution,
        contribution,
        score: layer.score ?? 0,
        layerName: layer.name || "",
        category: layer.category || "UNKNOWN"
      });
      return acc;
    }, []);
  }, [sortedLayers]);
  const categoryStats = React.useMemo(() => {
    const stats = {};
    waterfallData.forEach((d) => {
      if (!stats[d.category]) stats[d.category] = { count: 0, total: 0 };
      stats[d.category].count++;
      stats[d.category].total += d.contribution;
    });
    return stats;
  }, [waterfallData]);
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { className: "overflow-hidden", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex items-center justify-between mb-4", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-3", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "p-2 rounded-lg bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-500/30", children: /* @__PURE__ */ jsxRuntimeExports.jsx(ChartColumn, { className: "w-5 h-5 text-cyan-400" }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-lg font-semibold text-white", children: "Risk Layer Distribution" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: "text-xs text-white/50", children: [
          waterfallData.length,
          " layers analyzed"
        ] })
      ] })
    ] }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex flex-wrap gap-3 mb-4", children: Object.entries(categoryStats).map(([cat, stats]) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "div",
      {
        className: "flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10",
        children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              className: "w-2.5 h-2.5 rounded-full",
              style: { backgroundColor: CATEGORY_COLORS[cat]?.primary || "#6B7280" }
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-white/70", children: cat }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "text-xs font-semibold text-white/90", children: [
            stats.total.toFixed(0),
            "%"
          ] })
        ]
      },
      cat
    )) }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        ref: containerRef,
        className: "relative",
        style: { height: "400px", minHeight: "400px", minWidth: "300px", width: "100%" },
        children: waterfallData.length === 0 ? /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "h-full flex items-center justify-center text-white/40", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-center", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Layers, { className: "w-12 h-12 mx-auto mb-4 opacity-30" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm", children: "No layer data available" })
        ] }) }) : containerSize.ready && containerSize.width > 0 && containerSize.height > 0 ? /* @__PURE__ */ jsxRuntimeExports.jsxs(
          BarChart,
          {
            width: containerSize.width,
            height: containerSize.height,
            data: waterfallData,
            margin: { top: 30, right: 20, left: 20, bottom: 100 },
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("defs", { children: Object.entries(CATEGORY_COLORS).map(([cat, colors]) => /* @__PURE__ */ jsxRuntimeExports.jsxs("linearGradient", { id: `gradient-${cat}`, x1: "0", y1: "0", x2: "0", y2: "1", children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("stop", { offset: "0%", stopColor: colors.primary, stopOpacity: 1 }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("stop", { offset: "100%", stopColor: colors.primary, stopOpacity: 0.6 })
              ] }, cat)) }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                CartesianGrid,
                {
                  strokeDasharray: "3 3",
                  stroke: "rgba(255,255,255,0.08)",
                  vertical: false
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                XAxis,
                {
                  dataKey: "name",
                  angle: -55,
                  textAnchor: "end",
                  height: 100,
                  tick: { fill: "rgba(255,255,255,0.7)", fontSize: 10 },
                  tickLine: false,
                  axisLine: { stroke: "rgba(255,255,255,0.15)" },
                  interval: 0
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                YAxis,
                {
                  tick: { fill: "rgba(255,255,255,0.6)", fontSize: 11 },
                  tickLine: false,
                  axisLine: { stroke: "rgba(255,255,255,0.15)" },
                  tickFormatter: (v) => `${v}%`,
                  domain: [0, 15],
                  ticks: [0, 5, 10, 15]
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(Tooltip, { content: /* @__PURE__ */ jsxRuntimeExports.jsx(CustomTooltip$2, {}), cursor: { fill: "rgba(255,255,255,0.03)" } }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                Bar,
                {
                  dataKey: "value",
                  radius: [4, 4, 0, 0],
                  animationDuration: 1200,
                  animationEasing: "ease-out",
                  maxBarSize: 45,
                  children: waterfallData.map((entry) => /* @__PURE__ */ jsxRuntimeExports.jsx(
                    Cell,
                    {
                      fill: `url(#gradient-${entry.category})`,
                      style: { cursor: onBarClick ? "pointer" : "default" },
                      onClick: () => onBarClick?.(entry.layerName),
                      onMouseEnter: () => setHoveredBar(entry.layerName),
                      onMouseLeave: () => setHoveredBar(null)
                    },
                    entry.layerName
                  ))
                }
              )
            ]
          }
        ) : /* @__PURE__ */ jsxRuntimeExports.jsx(ChartSkeleton, { height: 400 })
      }
    ),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-center gap-2 mt-2 pt-3 border-t border-white/10", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-white/40", children: "Hover for details" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/20", children: "•" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-white/40", children: "Sorted by contribution" })
    ] })
  ] });
}
const ExecutiveNarrative = ({
  narrative,
  className = ""
}) => {
  if (!narrative) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(GlassCard, { className, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-4", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 mb-3", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(TrendingUp, { className: "w-5 h-5 text-blue-400" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-sm font-semibold text-white/90 uppercase tracking-wide", children: "Executive Summary" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-white/60 text-sm leading-relaxed", children: "AI narrative analysis is being generated. Please check back shortly for detailed insights." })
    ] }) });
  }
  const summary = safeString(narrative.executiveSummary, "No summary available");
  const insights = safeArray(narrative.keyInsights);
  const actions = safeArray(narrative.actionItems);
  const drivers = safeArray(narrative.riskDrivers);
  const notes = safeString(narrative.confidenceNotes, "");
  return /* @__PURE__ */ jsxRuntimeExports.jsx(GlassCard, { className, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-6", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 mb-3", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(TrendingUp, { className: "w-5 h-5 text-blue-400" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-sm font-semibold text-white/90 uppercase tracking-wide", children: "Executive Summary" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-white/80 leading-relaxed", children: summary })
    ] }),
    insights.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 mb-3", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Lightbulb, { className: "w-5 h-5 text-amber-400" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-sm font-semibold text-white/90 uppercase tracking-wide", children: "Key Insights" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("ul", { className: "space-y-2", children: insights.slice(0, 5).map((insight, idx) => /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { className: "flex items-start gap-3", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-amber-400/60 mt-1", children: "•" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/70 text-sm leading-relaxed flex-1", children: insight })
      ] }, idx)) })
    ] }),
    actions.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 mb-3", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(CircleCheck, { className: "w-5 h-5 text-emerald-400" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-sm font-semibold text-white/90 uppercase tracking-wide", children: "Recommended Actions" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("ul", { className: "space-y-2", children: actions.slice(0, 5).map((action, idx) => /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { className: "flex items-start gap-3", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "flex-shrink-0 w-5 h-5 rounded-full bg-emerald-400/20 border border-emerald-400/30 flex items-center justify-center text-emerald-400 text-xs font-semibold mt-0.5", children: idx + 1 }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/70 text-sm leading-relaxed flex-1", children: action })
      ] }, idx)) })
    ] }),
    drivers.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 mb-3", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(CircleAlert, { className: "w-5 h-5 text-red-400" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-sm font-semibold text-white/90 uppercase tracking-wide", children: "Primary Risk Drivers" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex flex-wrap gap-2", children: drivers.slice(0, 8).map((driver, idx) => /* @__PURE__ */ jsxRuntimeExports.jsx(
        "span",
        {
          className: "px-3 py-1.5 rounded-full bg-red-400/10 border border-red-400/20 text-red-400 text-xs font-medium",
          children: driver
        },
        idx
      )) })
    ] }),
    notes && /* @__PURE__ */ jsxRuntimeExports.jsx("section", { className: "pt-4 border-t border-white/10", children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-white/40 italic", children: notes }) })
  ] }) });
};
const CustomTooltip$1 = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const p10 = payload.find((p) => p.dataKey === "p10")?.value || 0;
    const p50 = payload.find((p) => p.dataKey === "p50")?.value || 0;
    const p90 = payload.find((p) => p.dataKey === "p90")?.value || 0;
    const phase = payload[0]?.payload?.phase || "Transit";
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "bg-black/95 backdrop-blur-xl border border-white/20 rounded-xl p-4 shadow-2xl min-w-[200px]", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 mb-3 pb-2 border-b border-white/10", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Calendar, { className: "w-4 h-4 text-cyan-400" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "font-medium text-white", children: label }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "ml-auto text-xs px-2 py-0.5 rounded-full bg-white/10 text-white/70", children: phase })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-2", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex justify-between items-center", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/60 text-sm", children: "Best Case (P10)" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "font-semibold text-emerald-400", children: p10.toFixed(1) })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex justify-between items-center", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/60 text-sm", children: "Expected (P50)" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "font-bold text-cyan-400", children: p50.toFixed(1) })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex justify-between items-center", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/60 text-sm", children: "Worst Case (P90)" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "font-semibold text-red-400", children: p90.toFixed(1) })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mt-3 pt-2 border-t border-white/10", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs text-white/40 mb-1", children: "80% Confidence Interval" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "h-2 bg-white/10 rounded-full overflow-hidden relative", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              className: "absolute h-full bg-gradient-to-r from-emerald-500/50 via-cyan-500/50 to-red-500/50",
              style: {
                left: `${p10}%`,
                width: `${p90 - p10}%`
              }
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              className: "absolute w-1 h-full bg-cyan-400",
              style: { left: `${p50}%` }
            }
          )
        ] })
      ] })
    ] });
  }
  return null;
};
const RiskScenarioFanChart = ({ data, etd, eta }) => {
  const [containerRef, containerSize] = useContainerSize();
  if (!data || data.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(GlassCard, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-center py-12 text-white/60", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Activity, { className: "w-12 h-12 mx-auto mb-4 opacity-30" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm", children: "No scenario projection data available" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-white/30 mt-1", children: "Scenario projection data is required for this chart" })
    ] }) });
  }
  const currentP50 = data[0]?.p50 || 0;
  const finalP50 = data[data.length - 1]?.p50 || 0;
  const trend = finalP50 - currentP50;
  const maxP90 = Math.max(...data.map((d) => d.p90 || 0));
  const minP10 = Math.min(...data.map((d) => d.p10 || 0));
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { className: "overflow-hidden", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-start justify-between mb-4", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-3", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "p-2 rounded-lg bg-gradient-to-br from-violet-500/20 to-purple-500/20 border border-violet-500/30", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Activity, { className: "w-5 h-5 text-violet-400" }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-lg font-semibold text-white", children: "Risk Scenario Projections" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-white/50", children: "Monte Carlo simulation with 80% confidence bands" })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: `flex items-center gap-2 px-3 py-1.5 rounded-lg ${trend > 5 ? "bg-red-500/20 border border-red-500/30" : trend < -5 ? "bg-emerald-500/20 border border-emerald-500/30" : "bg-white/10 border border-white/20"}`, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: `text-xs font-medium ${trend > 5 ? "text-red-400" : trend < -5 ? "text-emerald-400" : "text-white/60"}`, children: [
        trend > 0 ? "↑" : trend < 0 ? "↓" : "→",
        " ",
        Math.abs(trend).toFixed(1),
        " pts"
      ] }) })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 mb-4 p-3 rounded-xl bg-white/5 border border-white/10", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Ship, { className: "w-4 h-4 text-cyan-400" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs text-white/40", children: "ETD" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-sm font-medium text-white", children: etd || "N/A" })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex-1 flex items-center justify-center", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex-1 h-0.5 bg-gradient-to-r from-cyan-500/50 to-violet-500/50" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(ArrowRight, { className: "w-4 h-4 text-white/30 mx-2" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex-1 h-0.5 bg-gradient-to-r from-violet-500/50 to-emerald-500/50" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Plane, { className: "w-4 h-4 text-emerald-400" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs text-white/40", children: "ETA" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-sm font-medium text-white", children: eta || "N/A" })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-3 gap-3 mb-4", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-center p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-lg font-bold text-emerald-400", children: minP10.toFixed(0) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-[10px] text-white/40 uppercase", children: "Best Case" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-center p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-lg font-bold text-cyan-400", children: currentP50.toFixed(0) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-[10px] text-white/40 uppercase", children: "Expected" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-center p-2 rounded-lg bg-red-500/10 border border-red-500/20", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-lg font-bold text-red-400", children: maxP90.toFixed(0) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-[10px] text-white/40 uppercase", children: "Worst Case" })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        ref: containerRef,
        className: "relative",
        style: { height: "350px", minHeight: "350px", minWidth: "300px", width: "100%" },
        children: containerSize.ready && containerSize.width > 0 && containerSize.height > 0 ? /* @__PURE__ */ jsxRuntimeExports.jsxs(
          AreaChart,
          {
            width: containerSize.width,
            height: containerSize.height,
            data,
            margin: { top: 10, right: 20, left: 10, bottom: 20 },
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("defs", { children: [
                /* @__PURE__ */ jsxRuntimeExports.jsxs("linearGradient", { id: "fanGradient", x1: "0", y1: "0", x2: "0", y2: "1", children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("stop", { offset: "0%", stopColor: "#8B5CF6", stopOpacity: 0.4 }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("stop", { offset: "50%", stopColor: "#06B6D4", stopOpacity: 0.2 }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("stop", { offset: "100%", stopColor: "#10B981", stopOpacity: 0.1 })
                ] }),
                /* @__PURE__ */ jsxRuntimeExports.jsxs("linearGradient", { id: "medianGradient", x1: "0", y1: "0", x2: "1", y2: "0", children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("stop", { offset: "0%", stopColor: "#06B6D4" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("stop", { offset: "100%", stopColor: "#8B5CF6" })
                ] }),
                /* @__PURE__ */ jsxRuntimeExports.jsxs("filter", { id: "fanGlow", children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("feGaussianBlur", { stdDeviation: "3", result: "coloredBlur" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsxs("feMerge", { children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx("feMergeNode", { in: "coloredBlur" }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("feMergeNode", { in: "SourceGraphic" })
                  ] })
                ] })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                CartesianGrid,
                {
                  strokeDasharray: "3 3",
                  stroke: "rgba(255,255,255,0.05)",
                  vertical: false
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                XAxis,
                {
                  dataKey: "date",
                  tick: { fill: "rgba(255,255,255,0.5)", fontSize: 11 },
                  tickLine: false,
                  axisLine: { stroke: "rgba(255,255,255,0.1)" }
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                YAxis,
                {
                  tick: { fill: "rgba(255,255,255,0.5)", fontSize: 11 },
                  tickLine: false,
                  axisLine: { stroke: "rgba(255,255,255,0.1)" },
                  domain: [0, 100]
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(Tooltip, { content: /* @__PURE__ */ jsxRuntimeExports.jsx(CustomTooltip$1, {}) }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                ReferenceLine,
                {
                  y: 70,
                  stroke: "#EF4444",
                  strokeDasharray: "5 5",
                  strokeWidth: 1,
                  label: {
                    value: "High Risk",
                    fill: "#EF4444",
                    fontSize: 10,
                    position: "right"
                  }
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                Area,
                {
                  type: "monotone",
                  dataKey: "p90",
                  stroke: "rgba(239, 68, 68, 0.5)",
                  strokeWidth: 1,
                  fill: "url(#fanGradient)",
                  name: "90th Percentile",
                  animationDuration: 1500
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                Area,
                {
                  type: "monotone",
                  dataKey: "p10",
                  stroke: "rgba(16, 185, 129, 0.5)",
                  strokeWidth: 1,
                  fill: "#0a1628",
                  name: "10th Percentile",
                  animationDuration: 1500
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                Area,
                {
                  type: "monotone",
                  dataKey: "p50",
                  stroke: "url(#medianGradient)",
                  strokeWidth: 3,
                  fill: "none",
                  name: "Median",
                  filter: "url(#fanGlow)",
                  animationDuration: 1500,
                  dot: { fill: "#06B6D4", strokeWidth: 0, r: 3 },
                  activeDot: { fill: "#06B6D4", stroke: "#fff", strokeWidth: 2, r: 5 }
                }
              )
            ]
          }
        ) : /* @__PURE__ */ jsxRuntimeExports.jsx(ChartSkeleton, { height: 350 })
      }
    ),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-center gap-6 mt-2 pt-3 border-t border-white/10", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-3 h-3 rounded-full bg-gradient-to-r from-cyan-500 to-violet-500" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-white/50", children: "Expected Path" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-6 h-3 rounded bg-gradient-to-b from-violet-500/40 to-transparent" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-white/50", children: "80% Confidence" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-4 h-0.5 border-dashed border-t-2 border-red-400" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-white/50", children: "High Risk Threshold" })
      ] })
    ] })
  ] });
};
function ShipmentHeader({ data }) {
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between p-6 bg-black/20 rounded-2xl border border-white/10 backdrop-blur-sm", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-6", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "p-3 rounded-xl bg-blue-500/10 border border-blue-500/20", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Package, { className: "w-6 h-6 text-blue-400" }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("h1", { className: "text-2xl font-semibold text-white", children: [
          "Shipment ",
          data.shipmentId
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-4 mt-2 text-sm text-white/60", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-1", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(MapPin, { className: "w-4 h-4" }),
            data.route.pol,
            " → ",
            data.route.pod
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-1", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Ship, { className: "w-4 h-4" }),
            data.carrier
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-1", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Calendar, { className: "w-4 h-4" }),
            "ETD: ",
            data.etd
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-1", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Clock, { className: "w-4 h-4" }),
            "ETA: ",
            data.eta
          ] })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-right", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-sm text-white/60", children: "Data Confidence" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-2xl font-semibold text-white mt-1", children: [
        Math.round((data.dataConfidence ?? 0) * 100),
        "%"
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-xs text-white/40 mt-1", children: [
        "Last updated: ",
        data.lastUpdated
      ] })
    ] })
  ] });
}
const formatPercentage = (value) => {
  const absValue = Math.abs(value);
  if (absValue % 1 === 0) {
    return `${absValue}%`;
  }
  return `${absValue.toFixed(1)}%`;
};
const CustomLabel = ({ x, y, width, value, viewBox }) => {
  if (value === void 0 || value === null || width === void 0 || x === void 0 || y === void 0) {
    return null;
  }
  const formattedValue = formatPercentage(value);
  const barEnd = x + width;
  const chartWidth = viewBox?.width || 0;
  const marginRight = 60;
  const maxX = chartWidth - marginRight;
  const minBarWidthForInsideLabel = 60;
  const hasSpaceInside = width >= minBarWidthForInsideLabel && barEnd < maxX - 40;
  const labelX = hasSpaceInside ? barEnd - 6 : barEnd + 10;
  const textAnchor = hasSpaceInside ? "end" : "start";
  const fillColor = hasSpaceInside ? "#FFFFFF" : "#E5E7EB";
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    "text",
    {
      x: labelX,
      y,
      fill: fillColor,
      textAnchor,
      dominantBaseline: "middle",
      fontSize: "12",
      fontWeight: "600",
      style: {
        textShadow: "0 1px 3px rgba(0,0,0,0.9)",
        pointerEvents: "none",
        userSelect: "none",
        transition: "font-size 0.2s ease"
      },
      children: formattedValue
    }
  );
};
const RiskSensitivityTornado = ({ drivers }) => {
  const [containerRef, containerSize] = useContainerSize();
  const data = (drivers || []).filter((d) => d != null && d.name).map((d) => ({
    name: d.name || "Unknown",
    impact: d.impact ?? 0,
    absImpact: Math.abs(d.impact ?? 0)
  })).filter((d) => d.absImpact > 0);
  if (data.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-lg font-medium text-white mb-4", children: "Sensitivity Analysis" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-center py-12 text-white/60", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-16 h-16 mx-auto mb-4 rounded-full bg-emerald-500/10 flex items-center justify-center", children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: "w-8 h-8 text-emerald-400", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M5 13l4 4L19 7" }) }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm font-medium text-emerald-400", children: "Low Risk - No Significant Drivers" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-white/40 mt-2 max-w-xs mx-auto", children: "Risk score is below threshold. No significant risk drivers detected that require attention." })
      ] })
    ] });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-lg font-medium text-white mb-4", children: "Sensitivity Analysis" }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        ref: containerRef,
        style: { height: "400px", minHeight: "400px", minWidth: "300px", width: "100%", position: "relative" },
        children: containerSize.ready && containerSize.width > 0 && containerSize.height > 0 ? /* @__PURE__ */ jsxRuntimeExports.jsxs(
          BarChart,
          {
            width: containerSize.width,
            height: containerSize.height,
            data,
            layout: "vertical",
            margin: { top: 20, right: 60, left: 100, bottom: 20 },
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(CartesianGrid, { strokeDasharray: "3 3", stroke: "rgba(255,255,255,0.1)" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                XAxis,
                {
                  type: "number",
                  tick: { fill: "rgba(255,255,255,0.6)", fontSize: 11 },
                  domain: [0, "dataMax"]
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(YAxis, { dataKey: "name", type: "category", tick: { fill: "rgba(255,255,255,0.6)", fontSize: 12 }, width: 90 }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                Tooltip,
                {
                  contentStyle: {
                    backgroundColor: "rgba(0,0,0,0.95)",
                    border: "1px solid rgba(255,255,255,0.2)",
                    borderRadius: "12px",
                    padding: "12px"
                  },
                  formatter: (value) => [
                    value !== void 0 ? formatPercentage(value) : "0%",
                    "Impact"
                  ],
                  labelStyle: {
                    color: "#FFFFFF",
                    fontWeight: "600",
                    marginBottom: "4px"
                  },
                  itemStyle: {
                    color: "#F3F4F6",
                    fontSize: "13px"
                  }
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsxs(Bar, { dataKey: "impact", radius: [0, 4, 4, 0], children: [
                data.map((entry, index) => /* @__PURE__ */ jsxRuntimeExports.jsx(
                  Cell,
                  {
                    fill: entry.impact >= 0 ? "#EF4444" : "#10B981"
                  },
                  `cell-${index}`
                )),
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  LabelList,
                  {
                    dataKey: "impact",
                    content: /* @__PURE__ */ jsxRuntimeExports.jsx(CustomLabel, {}),
                    position: "right"
                  }
                )
              ] })
            ]
          }
        ) : /* @__PURE__ */ jsxRuntimeExports.jsx(ChartSkeleton, { height: 400 })
      }
    )
  ] });
};
function RiskCostEfficiencyFrontier({
  scenarios,
  baselineRisk,
  highlightedScenario
}) {
  const [containerRef, containerSize] = useContainerSize();
  if (!scenarios || scenarios.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(GlassCard, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-center py-12 text-white/60", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm", children: "No scenario data available" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-white/30 mt-1", children: "Scenario data is required for this chart" })
    ] }) });
  }
  const isParetoOptimal = (point, allPoints) => {
    if (!allPoints || allPoints.length === 0) return false;
    return !allPoints.some(
      (other) => other !== point && (other.riskReduction ?? 0) >= (point.riskReduction ?? 0) && (other.costImpact ?? 0) <= (point.costImpact ?? 0) && ((other.riskReduction ?? 0) > (point.riskReduction ?? 0) || (other.costImpact ?? 0) < (point.costImpact ?? 0))
    );
  };
  const chartData = scenarios.filter((s) => s != null).map((scenario) => ({
    name: scenario.title || "Unknown",
    x: scenario.costImpact ?? 0,
    // cost
    y: scenario.riskReduction ?? 0,
    // risk reduction
    z: (scenario.feasibility ?? 0) * 100,
    // feasibility as size
    description: scenario.description,
    isPareto: isParetoOptimal(scenario, scenarios)
  }));
  const riskReductions = scenarios.map((s) => s.riskReduction ?? 0).filter((v) => !isNaN(v));
  const costImpacts = scenarios.map((s) => s.costImpact ?? 0).filter((v) => !isNaN(v));
  const maxRiskReduction = riskReductions.length > 0 ? Math.max(...riskReductions) : 0;
  const maxCost = costImpacts.length > 0 ? Math.max(...costImpacts) : 1;
  const efficiencyThreshold = maxCost > 0 ? maxRiskReduction / maxCost * 0.7 : 0;
  const CustomTooltip2 = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "bg-black/90 border border-white/20 rounded-lg p-4 shadow-xl", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-white font-medium mb-2", children: data.name }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-1 text-sm", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex justify-between gap-4", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/60", children: "Cost Impact:" }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "text-white", children: [
              data.x.toFixed(1),
              "%"
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex justify-between gap-4", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/60", children: "Risk Reduction:" }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "text-white", children: [
              data.y.toFixed(0),
              " pts"
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex justify-between gap-4", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/60", children: "Feasibility:" }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "text-white", children: [
              data.z.toFixed(0),
              "%"
            ] })
          ] }),
          data.isPareto && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "mt-2 px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs font-medium", children: "Pareto Optimal" })
        ] }),
        data.description && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "mt-3 pt-3 border-t border-white/10 text-xs text-white/60", children: data.description })
      ] });
    }
    return null;
  };
  const getPointColor = (point) => {
    if (point.name === highlightedScenario) return "#8B5CF6";
    if (point.isPareto) return "#10B981";
    if (point.y / Math.max(point.x, 0.1) > efficiencyThreshold) return "#3B82F6";
    return "#6B7280";
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between mb-6", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-xl font-medium text-white", children: "Cost-Efficiency Frontier" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-white/40 mt-1", children: "Risk reduction vs cost impact for mitigation strategies" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-4 text-xs", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-3 h-3 rounded-full bg-green-500" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/60", children: "Pareto Optimal" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-3 h-3 rounded-full bg-blue-500" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/60", children: "Efficient" })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-1 md:grid-cols-3 gap-4 mb-6", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "p-4 rounded-xl bg-white/5 border border-white/10", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 mb-2", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Award, { className: "w-4 h-4 text-green-400" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-sm font-medium text-white", children: "Best Value" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-xs text-white/60", children: [
          chartData.filter((d) => d.isPareto).length,
          " strategies on optimal frontier"
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "p-4 rounded-xl bg-white/5 border border-white/10", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 mb-2", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(TrendingUp, { className: "w-4 h-4 text-blue-400" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-sm font-medium text-white", children: "Max Impact" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs text-white/60", children: maxRiskReduction > 0 ? `Up to ${maxRiskReduction.toFixed(0)} points risk reduction available` : baselineRisk < 30 ? "Risk already optimal - no further reduction needed" : "Maintain current plan - stable risk profile" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "p-4 rounded-xl bg-white/5 border border-white/10", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 mb-2", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Zap, { className: "w-4 h-4 text-purple-400" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-sm font-medium text-white", children: "Efficiency" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-xs text-white/60", children: [
          "Baseline risk: ",
          baselineRisk,
          " points"
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        ref: containerRef,
        style: { height: "400px", minHeight: "400px", minWidth: "300px", width: "100%", position: "relative" },
        children: containerSize.ready && containerSize.width > 0 && containerSize.height > 0 ? /* @__PURE__ */ jsxRuntimeExports.jsxs(
          ScatterChart,
          {
            width: containerSize.width,
            height: containerSize.height,
            margin: { top: 20, right: 30, left: 20, bottom: 20 },
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(CartesianGrid, { strokeDasharray: "3 3", stroke: "rgba(255,255,255,0.1)" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                XAxis,
                {
                  type: "number",
                  dataKey: "x",
                  name: "Cost Impact",
                  unit: "%",
                  tick: { fill: "rgba(255,255,255,0.6)", fontSize: 12 },
                  tickLine: { stroke: "rgba(255,255,255,0.2)" },
                  axisLine: { stroke: "rgba(255,255,255,0.2)" },
                  label: {
                    value: "Cost Impact (%)",
                    position: "insideBottom",
                    offset: -10,
                    style: { fill: "rgba(255,255,255,0.6)" }
                  }
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                YAxis,
                {
                  type: "number",
                  dataKey: "y",
                  name: "Risk Reduction",
                  unit: "pts",
                  tick: { fill: "rgba(255,255,255,0.6)", fontSize: 12 },
                  tickLine: { stroke: "rgba(255,255,255,0.2)" },
                  axisLine: { stroke: "rgba(255,255,255,0.2)" },
                  label: {
                    value: "Risk Reduction (points)",
                    angle: -90,
                    position: "insideLeft",
                    style: { fill: "rgba(255,255,255,0.6)" }
                  }
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(Tooltip, { content: /* @__PURE__ */ jsxRuntimeExports.jsx(CustomTooltip2, {}) }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                Scatter,
                {
                  data: chartData,
                  fill: "#3B82F6",
                  shape: "circle",
                  children: chartData.map((entry, index) => /* @__PURE__ */ jsxRuntimeExports.jsx(
                    Cell,
                    {
                      fill: getPointColor(entry),
                      stroke: entry.name === highlightedScenario ? "#FFFFFF" : "none",
                      strokeWidth: entry.name === highlightedScenario ? 2 : 0
                    },
                    `cell-${index}`
                  ))
                }
              )
            ]
          }
        ) : /* @__PURE__ */ jsxRuntimeExports.jsx(ChartSkeleton, { height: 400 })
      }
    ),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "mt-4 text-xs text-white/40 text-center", children: "Point size represents feasibility • Colors indicate efficiency classification" })
  ] });
}
const DataReliabilityMatrix = ({ domains }) => {
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-lg font-medium text-white mb-4", children: "Data Reliability Matrix" }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "space-y-3", children: domains.map((domain) => /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between p-3 bg-white/5 rounded-lg", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-sm font-medium text-white", children: domain.domain }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs text-white/60 mt-1", children: domain.notes })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-right", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs text-white/60", children: "Confidence" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-sm font-semibold text-white", children: [
            Math.round(domain.confidence * 100),
            "%"
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-right", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs text-white/60", children: "Completeness" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-sm font-semibold text-white", children: [
            Math.round(domain.completeness * 100),
            "%"
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-right", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs text-white/60", children: "Freshness" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-sm font-semibold text-white", children: [
            Math.round(domain.freshness * 100),
            "%"
          ] })
        ] })
      ] })
    ] }, domain.domain)) })
  ] });
};
const BadgeRisk = ({ level, size = "md" }) => {
  const colorMap = {
    LOW: "bg-green-500/20 text-green-400",
    MEDIUM: "bg-amber-500/20 text-amber-400",
    HIGH: "bg-red-500/20 text-red-400"
  };
  const sizeMap = {
    sm: "text-xs px-2 py-0.5",
    md: "text-sm px-3 py-1",
    lg: "text-base px-4 py-1.5"
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: `rounded-full font-medium ${colorMap[level]} ${sizeMap[size]}`, children: level });
};
function getRiskLevel(score) {
  if (score < 40) return "LOW";
  if (score < 70) return "MEDIUM";
  return "HIGH";
}
function LayersTable({ layers, onSelectLayer }) {
  const [sortByScoreDesc, setSortByScoreDesc] = reactExports.useState(true);
  const sortedLayers = reactExports.useMemo(() => {
    const copy = (layers || []).slice();
    copy.sort((a, b) => {
      const diff = (b.score ?? 0) - (a.score ?? 0);
      return sortByScoreDesc ? diff : -diff;
    });
    return copy;
  }, [layers, sortByScoreDesc]);
  const onRowActivate = (layerName) => {
    if (!onSelectLayer) return;
    onSelectLayer(layerName);
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between mb-6", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-xl", children: "Risk Layers Detail" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "button",
        {
          type: "button",
          onClick: () => setSortByScoreDesc((v) => !v),
          className: "flex items-center gap-1 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent-primary)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-bg-primary)]",
          "aria-label": `Sort by score ${sortByScoreDesc ? "ascending" : "descending"}`,
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(ArrowUpDown, { className: "w-4 h-4" }),
            "Sort"
          ]
        }
      )
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "overflow-x-auto", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("table", { className: "w-full", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("thead", { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("tr", { className: "border-b border-white/10", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { className: "text-left py-3 px-4 text-sm font-medium text-[var(--color-text-muted)]", children: "Layer" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { className: "text-left py-3 px-4 text-sm font-medium text-[var(--color-text-muted)]", children: "Contribution" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { className: "text-left py-3 px-4 text-sm font-medium text-[var(--color-text-muted)]", children: "Status" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { className: "text-left py-3 px-4 text-sm font-medium text-[var(--color-text-muted)]", children: "Score" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { className: "text-left py-3 px-4 text-sm font-medium text-[var(--color-text-muted)]", children: "Notes" })
      ] }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("tbody", { children: sortedLayers.length === 0 ? /* @__PURE__ */ jsxRuntimeExports.jsx("tr", { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("td", { colSpan: 5, className: "py-8 text-center text-white/40", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-sm", children: "No layer data available" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs text-white/30 mt-1", children: "Layer data is required for this table" })
      ] }) }) : sortedLayers.map((layer) => {
        const clickable = Boolean(onSelectLayer);
        return /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "tr",
          {
            className: `border-b border-white/5 hover:bg-white/5 transition-colors ${clickable ? "cursor-pointer" : ""}`,
            role: clickable ? "button" : void 0,
            tabIndex: clickable ? 0 : -1,
            onClick: () => clickable && onRowActivate(layer.name),
            onKeyDown: (e) => {
              if (!clickable) return;
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onRowActivate(layer.name);
              }
            },
            "aria-label": clickable ? `Open trace for ${layer.name}` : void 0,
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("td", { className: "py-4 px-4 text-sm font-medium text-white", children: layer.name }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("td", { className: "py-4 px-4 text-sm text-[var(--color-text-secondary)]", children: [
                layer.contribution,
                "%"
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("td", { className: "py-4 px-4", children: /* @__PURE__ */ jsxRuntimeExports.jsx(
                "span",
                {
                  className: `text-xs px-2 py-1 rounded-full ${layer.status === "ALERT" ? "bg-red-500/20 text-red-400" : layer.status === "WARNING" ? "bg-amber-500/20 text-amber-400" : "bg-green-500/20 text-green-400"}`,
                  children: layer.status
                }
              ) }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("td", { className: "py-4 px-4 flex items-center", children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx(BadgeRisk, { level: getRiskLevel(layer.score), size: "sm" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "ml-2 text-sm", children: layer.score })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("td", { className: "py-4 px-4 text-sm text-[var(--color-text-secondary)]", children: layer.notes })
            ]
          },
          layer.name
        );
      }) })
    ] }) })
  ] });
}
const PrimaryRecommendationCard = ({
  title,
  badge,
  riskReduction,
  costImpact,
  confidence,
  rationale,
  currentRisk,
  newRisk
}) => {
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { padding: "lg", className: "border-2 border-blue-500/30", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-start justify-between mb-4", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs text-blue-400 font-medium mb-1", children: badge }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-2xl font-bold text-white", children: title })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-right", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-sm text-white/60", children: "Confidence" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-lg font-semibold text-white", children: [
          Math.round(confidence * 100),
          "%"
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-2 gap-4 mb-4", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-sm text-white/60", children: "Risk Reduction" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: `text-2xl font-bold ${riskReduction > 0 ? "text-green-400" : "text-emerald-400/70"}`, children: riskReduction > 0 ? `-${riskReduction} pts` : "—" }),
        riskReduction === 0 && currentRisk < 30 && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs text-emerald-400/60 mt-1", children: "Already optimal" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-sm text-white/60", children: "Cost Impact" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xl font-semibold text-white", children: costImpact })
      ] })
    ] }),
    newRisk !== void 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mb-4 p-3 bg-white/5 rounded-lg border border-white/10", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs text-white/60 mb-1", children: "Projected Risk Score" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-3", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/60", children: currentRisk }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/40", children: "→" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xl font-bold text-white", children: newRisk })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "pt-4 border-t border-white/10", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-sm font-medium text-white/80 mb-2", children: "Rationale" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-white/60", children: rationale })
    ] })
  ] });
};
const SecondaryRecommendationCard = ({
  category,
  badge,
  metric,
  context,
  confidence
}) => {
  const badgeColor = badge.type === "consider" ? "blue" : "purple";
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { padding: "md", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-start justify-between mb-3", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs text-white/60", children: category }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "div",
        {
          className: `px-2 py-1 rounded text-xs font-medium ${badgeColor === "blue" ? "bg-blue-500/20 text-blue-400" : "bg-purple-500/20 text-purple-400"}`,
          children: badge.text
        }
      )
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mb-3", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-lg font-semibold text-white", children: metric }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-sm text-white/60 mt-1", children: context })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "pt-3 border-t border-white/10", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-white/60", children: "Confidence" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "text-sm font-medium text-white", children: [
        Math.round(confidence * 100),
        "%"
      ] })
    ] }) })
  ] });
};
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "bg-black/95 backdrop-blur-xl border border-white/20 rounded-xl p-4 shadow-2xl", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 mb-2", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(DollarSign, { className: "w-4 h-4 text-emerald-400" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "text-white font-medium", children: [
          "Loss: $",
          Number(label).toLocaleString()
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-sm", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/60", children: "Probability Density: " }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "text-cyan-400 font-semibold", children: [
          (payload[0].value * 100).toFixed(2),
          "%"
        ] })
      ] })
    ] });
  }
  return null;
};
const MetricCard = ({
  icon: Icon2,
  label,
  value,
  color,
  description
}) => /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: `relative overflow-hidden rounded-xl p-4 border ${color} bg-gradient-to-br from-white/5 to-transparent`, children: [
  /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "absolute top-0 right-0 w-20 h-20 opacity-10", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Icon2, { className: "w-full h-full" }) }),
  /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "relative z-10", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 mb-1", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Icon2, { className: `w-4 h-4 ${color.includes("emerald") ? "text-emerald-400" : color.includes("amber") ? "text-amber-400" : "text-red-400"}` }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-white/50 uppercase tracking-wider", children: label })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: `text-2xl font-bold ${color.includes("emerald") ? "text-emerald-400" : color.includes("amber") ? "text-amber-400" : "text-red-400"}`, children: value }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs text-white/40 mt-1", children: description })
  ] })
] });
const FinancialModule = ({ financial }) => {
  const [containerRef, containerSize] = useContainerSize();
  if (!financial.lossCurve || financial.lossCurve.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(GlassCard, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-center py-12 text-white/60", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(DollarSign, { className: "w-12 h-12 mx-auto mb-4 opacity-30" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm", children: "No loss distribution data available" })
    ] }) });
  }
  const maxProbability = Math.max(...financial.lossCurve.map((d) => d.probability || 0));
  const riskSeverity = financial.expectedLoss > 1e4 ? "high" : financial.expectedLoss > 5e3 ? "medium" : "low";
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { className: "overflow-hidden", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "relative mb-6", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "absolute inset-0 bg-gradient-to-r from-red-500/10 via-amber-500/10 to-emerald-500/10 blur-xl" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "relative", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between mb-2", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-3", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "p-2 rounded-lg bg-gradient-to-br from-red-500/20 to-amber-500/20 border border-red-500/30", children: /* @__PURE__ */ jsxRuntimeExports.jsx(TrendingDown, { className: "w-5 h-5 text-red-400" }) }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-lg font-semibold text-white", children: "Financial Loss Distribution" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-white/50", children: "Probability density function of potential losses" })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: `px-3 py-1 rounded-full text-xs font-medium ${riskSeverity === "high" ? "bg-red-500/20 text-red-400 border border-red-500/30" : riskSeverity === "medium" ? "bg-amber-500/20 text-amber-400 border border-amber-500/30" : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"}`, children: riskSeverity === "high" ? "⚠️ High Exposure" : riskSeverity === "medium" ? "⚡ Moderate" : "✓ Low Risk" })
      ] }) })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-3 gap-4 mb-6", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        MetricCard,
        {
          icon: DollarSign,
          label: "Expected Loss",
          value: `$${(financial.expectedLoss / 1e3).toFixed(1)}K`,
          color: "border-emerald-500/30",
          description: "Most likely outcome"
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        MetricCard,
        {
          icon: TriangleAlert,
          label: "VaR 95%",
          value: `$${(financial.var95 / 1e3).toFixed(1)}K`,
          color: "border-amber-500/30",
          description: "Severe but plausible"
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        MetricCard,
        {
          icon: Shield,
          label: "CVaR 95%",
          value: `$${(financial.cvar95 / 1e3).toFixed(1)}K`,
          color: "border-red-500/30",
          description: "Tail risk average"
        }
      )
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        ref: containerRef,
        className: "relative",
        style: { height: "350px", minHeight: "350px", minWidth: "300px", width: "100%" },
        children: containerSize.ready && containerSize.width > 0 && containerSize.height > 0 ? /* @__PURE__ */ jsxRuntimeExports.jsxs(
          AreaChart,
          {
            width: containerSize.width,
            height: containerSize.height,
            data: financial.lossCurve,
            margin: { top: 20, right: 30, left: 20, bottom: 20 },
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("defs", { children: [
                /* @__PURE__ */ jsxRuntimeExports.jsxs("linearGradient", { id: "lossGradient", x1: "0", y1: "0", x2: "0", y2: "1", children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("stop", { offset: "0%", stopColor: "#EF4444", stopOpacity: 0.6 }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("stop", { offset: "50%", stopColor: "#F59E0B", stopOpacity: 0.3 }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("stop", { offset: "100%", stopColor: "#10B981", stopOpacity: 0.1 })
                ] }),
                /* @__PURE__ */ jsxRuntimeExports.jsxs("linearGradient", { id: "strokeGradient", x1: "0", y1: "0", x2: "1", y2: "0", children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("stop", { offset: "0%", stopColor: "#10B981" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("stop", { offset: "50%", stopColor: "#F59E0B" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("stop", { offset: "100%", stopColor: "#EF4444" })
                ] }),
                /* @__PURE__ */ jsxRuntimeExports.jsxs("filter", { id: "glow", children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("feGaussianBlur", { stdDeviation: "3", result: "coloredBlur" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsxs("feMerge", { children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx("feMergeNode", { in: "coloredBlur" }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("feMergeNode", { in: "SourceGraphic" })
                  ] })
                ] })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                CartesianGrid,
                {
                  strokeDasharray: "3 3",
                  stroke: "rgba(255,255,255,0.05)",
                  vertical: false
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                XAxis,
                {
                  dataKey: "loss",
                  tick: { fill: "rgba(255,255,255,0.5)", fontSize: 11 },
                  tickFormatter: (value) => `$${(value / 1e3).toFixed(0)}K`,
                  axisLine: { stroke: "rgba(255,255,255,0.1)" },
                  tickLine: { stroke: "rgba(255,255,255,0.1)" }
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                YAxis,
                {
                  tick: { fill: "rgba(255,255,255,0.5)", fontSize: 11 },
                  tickFormatter: (value) => `${(value * 100).toFixed(1)}%`,
                  axisLine: { stroke: "rgba(255,255,255,0.1)" },
                  tickLine: { stroke: "rgba(255,255,255,0.1)" },
                  domain: [0, maxProbability * 1.1]
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(Tooltip, { content: /* @__PURE__ */ jsxRuntimeExports.jsx(CustomTooltip, {}) }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                ReferenceLine,
                {
                  x: financial.expectedLoss,
                  stroke: "#10B981",
                  strokeDasharray: "5 5",
                  strokeWidth: 2,
                  label: {
                    value: "E[L]",
                    fill: "#10B981",
                    fontSize: 10,
                    position: "top"
                  }
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                ReferenceLine,
                {
                  x: financial.var95,
                  stroke: "#F59E0B",
                  strokeDasharray: "5 5",
                  strokeWidth: 2,
                  label: {
                    value: "VaR",
                    fill: "#F59E0B",
                    fontSize: 10,
                    position: "top"
                  }
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                ReferenceLine,
                {
                  x: financial.cvar95,
                  stroke: "#EF4444",
                  strokeDasharray: "5 5",
                  strokeWidth: 2,
                  label: {
                    value: "CVaR",
                    fill: "#EF4444",
                    fontSize: 10,
                    position: "top"
                  }
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                Area,
                {
                  type: "monotone",
                  dataKey: "probability",
                  stroke: "url(#strokeGradient)",
                  strokeWidth: 3,
                  fill: "url(#lossGradient)",
                  filter: "url(#glow)",
                  animationDuration: 1500,
                  animationEasing: "ease-out"
                }
              )
            ]
          }
        ) : /* @__PURE__ */ jsxRuntimeExports.jsx(ChartSkeleton, { height: 350 })
      }
    ),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-center gap-6 mt-4 pt-4 border-t border-white/10", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-3 h-0.5 bg-emerald-400" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-white/50", children: "Expected Loss" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-3 h-0.5 bg-amber-400" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-white/50", children: "Value at Risk (95%)" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-3 h-0.5 bg-red-400" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-white/50", children: "Conditional VaR (95%)" })
      ] })
    ] })
  ] });
};
const LANGUAGES = [
  { code: "vi", name: "Tiếng Việt", flag: "🇻🇳", shortName: "VI" },
  { code: "en", name: "English", flag: "🇺🇸", shortName: "EN" }
];
const STORAGE_KEY = "riskcast_lang";
const TRANSLATIONS = {
  vi: {
    overview: "Tổng quan",
    analytics: "Phân tích",
    decisions: "Quyết định",
    refresh: "Làm mới",
    riskScore: "Điểm rủi ro",
    confidence: "Độ tin cậy",
    riskLevel: "Mức rủi ro",
    dataConfidence: "Độ tin cậy dữ liệu",
    lastUpdated: "Cập nhật lần cuối",
    engineV2: "Engine v2",
    shipment: "Lô hàng",
    route: "Tuyến đường",
    carrier: "Hãng vận chuyển",
    etd: "Ngày gửi dự kiến",
    eta: "Ngày đến dự kiến",
    riskProfileRadar: "Radar Hồ Sơ Rủi Ro",
    loading: "Đang phân tích dữ liệu rủi ro...",
    noData: "Không có dữ liệu. Vui lòng chạy phân tích trước.",
    error: "Lỗi phân tích",
    retry: "Thử lại"
  },
  en: {
    overview: "Overview",
    analytics: "Analytics",
    decisions: "Decisions",
    refresh: "Refresh",
    riskScore: "Risk Score",
    confidence: "Confidence",
    riskLevel: "Risk Level",
    dataConfidence: "Data Confidence",
    lastUpdated: "Last updated",
    engineV2: "Engine v2",
    shipment: "Shipment",
    route: "Route",
    carrier: "Carrier",
    etd: "ETD",
    eta: "ETA",
    riskProfileRadar: "Risk Profile Radar",
    loading: "Analyzing Risk Data...",
    noData: "No data available. Please run analysis first.",
    error: "Analysis Error",
    retry: "Retry"
  }
};
function useTranslation() {
  const [lang, setLang] = reactExports.useState(() => localStorage.getItem(STORAGE_KEY) || "vi");
  reactExports.useEffect(() => {
    const handleLangChange = (e) => {
      setLang(e.detail.language);
    };
    window.addEventListener("languageChanged", handleLangChange);
    return () => window.removeEventListener("languageChanged", handleLangChange);
  }, []);
  const t = (key) => {
    return TRANSLATIONS[lang]?.[key] || TRANSLATIONS["en"][key] || key;
  };
  return { t, lang, setLang };
}
function HeaderLangSwitcher() {
  const [isOpen, setIsOpen] = reactExports.useState(false);
  const [currentLang, setCurrentLang] = reactExports.useState("vi");
  const containerRef = reactExports.useRef(null);
  reactExports.useEffect(() => {
    const savedLang = localStorage.getItem(STORAGE_KEY) || "vi";
    setCurrentLang(savedLang);
    document.documentElement.lang = savedLang;
  }, []);
  reactExports.useEffect(() => {
    function handleClickOutside(event) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);
  const handleLanguageChange = (langCode) => {
    setCurrentLang(langCode);
    localStorage.setItem(STORAGE_KEY, langCode);
    document.documentElement.lang = langCode;
    window.dispatchEvent(new CustomEvent("languageChanged", {
      detail: { language: langCode }
    }));
    setIsOpen(false);
    window.dispatchEvent(new StorageEvent("storage", {
      key: STORAGE_KEY,
      newValue: langCode
    }));
  };
  const currentLangData = LANGUAGES.find((l) => l.code === currentLang) || LANGUAGES[0];
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { ref: containerRef, className: "relative", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "button",
      {
        onClick: () => setIsOpen(!isOpen),
        className: "flex items-center gap-2 px-3 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition-all",
        title: "Change Language",
        children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Globe, { className: "w-4 h-4 text-cyan-400" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "text-sm font-medium text-white", children: [
            currentLangData.flag,
            " ",
            currentLangData.shortName
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { className: `w-3 h-3 text-white/50 transition-transform ${isOpen ? "rotate-180" : ""}`, fill: "none", viewBox: "0 0 24 24", stroke: "currentColor", children: /* @__PURE__ */ jsxRuntimeExports.jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M19 9l-7 7-7-7" }) })
        ]
      }
    ),
    isOpen && /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        className: "absolute top-full right-0 mt-2 w-44 rounded-xl overflow-hidden z-50 animate-in fade-in slide-in-from-top-2 duration-200",
        style: {
          background: "linear-gradient(135deg, rgba(20, 25, 30, 0.98), rgba(10, 15, 20, 0.99))",
          border: "1px solid rgba(255, 255, 255, 0.1)",
          backdropFilter: "blur(20px)",
          boxShadow: "0 8px 32px rgba(0, 0, 0, 0.5)"
        },
        children: LANGUAGES.map((lang) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "button",
          {
            onClick: () => handleLanguageChange(lang.code),
            className: `w-full flex items-center gap-3 px-4 py-3 text-left transition-all ${lang.code === currentLang ? "bg-cyan-500/10 text-cyan-400" : "text-white/70 hover:bg-white/5 hover:text-white"}`,
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-lg", children: lang.flag }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex-1", children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-sm font-medium", children: lang.shortName }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs text-white/40 ml-2", children: lang.name })
              ] }),
              lang.code === currentLang && /* @__PURE__ */ jsxRuntimeExports.jsx(Check, { className: "w-4 h-4 text-cyan-400" })
            ]
          },
          lang.code
        ))
      }
    )
  ] });
}
function ResultsPage() {
  const [viewModel, setViewModel] = reactExports.useState(null);
  const [loading, setLoading] = reactExports.useState(true);
  const [error, setError] = reactExports.useState(null);
  const [activeTab, setActiveTab] = reactExports.useState("overview");
  const { t } = useTranslation();
  const fetchResults = async (showLoading = true) => {
    try {
      if (showLoading) setLoading(true);
      setError(null);
      const savedResults = localStorage.getItem("RISKCAST_RESULTS_V2");
      if (savedResults) {
        try {
          const parsed = JSON.parse(savedResults);
          console.log("[ResultsPage] Loaded results from localStorage:", parsed);
          const normalized = adaptResultV2(parsed);
          console.log("[ResultsPage] Normalized from localStorage:", normalized);
          setViewModel(normalized);
          setLoading(false);
          return;
        } catch (parseErr) {
          console.warn("[ResultsPage] Failed to parse localStorage results:", parseErr);
        }
      }
      try {
        const timestamp = `?t=${Date.now()}&_=${Math.random().toString(36).substr(2, 9)}`;
        const response = await fetch(`/results/data${timestamp}`, {
          method: "GET",
          headers: {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Accept": "application/json"
          }
        });
        if (response.ok) {
          const _rawResult = await response.json();
          console.log("[ResultsPage] Raw result from backend:", _rawResult);
          const normalized = adaptResultV2(_rawResult);
          console.log("[ResultsPage] Normalized view model:", normalized);
          setViewModel(normalized);
          return;
        }
      } catch (apiErr) {
        console.warn("[ResultsPage] API fetch failed, using fallback:", apiErr);
      }
      const savedState = localStorage.getItem("RISKCAST_STATE");
      if (savedState) {
        try {
          const state = JSON.parse(savedState);
          console.log("[ResultsPage] Generating results from RISKCAST_STATE:", state);
          const mockResults = {
            shipment: state,
            riskScore: Math.floor(Math.random() * 30) + 65,
            riskLevel: "MODERATE",
            confidence: 85,
            layers: [],
            insights: [
              { type: "info", message: "Risk analysis completed" }
            ],
            analyzedAt: (/* @__PURE__ */ new Date()).toISOString()
          };
          const normalized = adaptResultV2(mockResults);
          setViewModel(normalized);
          return;
        } catch (stateErr) {
          console.warn("[ResultsPage] Failed to process RISKCAST_STATE:", stateErr);
        }
      }
      setError("No analysis results found. Please run analysis from the Summary page.");
    } catch (err) {
      const message = err instanceof Error ? err.message : "An unexpected error occurred";
      setError(message);
      console.error("[ResultsPage] Fetch error:", err);
    } finally {
      setLoading(false);
    }
  };
  reactExports.useEffect(() => {
    fetchResults(true);
    const intervalId = setInterval(() => fetchResults(false), 15e3);
    return () => clearInterval(intervalId);
  }, []);
  if (loading) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8", children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "max-w-7xl mx-auto", children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex items-center justify-center min-h-[80vh]", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-center", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "relative w-32 h-32 mx-auto mb-8", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "absolute inset-0 rounded-full border-4 border-blue-500/20" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "absolute inset-0 rounded-full border-4 border-transparent border-t-blue-500 animate-spin" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "absolute inset-4 rounded-full border-4 border-transparent border-t-purple-500 animate-spin", style: { animationDuration: "1.5s", animationDirection: "reverse" } }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "absolute inset-8 rounded-full border-4 border-transparent border-t-cyan-500 animate-spin", style: { animationDuration: "2s" } })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-2xl font-bold text-white mb-2", children: "Analyzing Risk Data" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-white/50", children: "Processing shipment intelligence..." })
    ] }) }) }) });
  }
  if (error) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8 flex items-center justify-center", children: /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { className: "max-w-md text-center", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-20 h-20 mx-auto mb-6 rounded-full bg-red-500/10 flex items-center justify-center", children: /* @__PURE__ */ jsxRuntimeExports.jsx(CircleX, { className: "w-10 h-10 text-red-400" }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-2xl font-bold text-white mb-2", children: "Analysis Error" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-white/60 mb-6", children: error }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "button",
        {
          onClick: () => fetchResults(true),
          className: "px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white rounded-xl font-medium transition-all flex items-center gap-2 mx-auto shadow-lg shadow-blue-500/25",
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(RefreshCw, { className: "w-5 h-5" }),
            "Retry Analysis"
          ]
        }
      )
    ] }) });
  }
  if (!viewModel) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8 flex items-center justify-center", children: /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { className: "max-w-md text-center", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-20 h-20 mx-auto mb-6 rounded-full bg-amber-500/10 flex items-center justify-center", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Package, { className: "w-10 h-10 text-amber-400" }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-2xl font-bold text-white mb-2", children: "No Analysis Data" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-white/60 mb-6", children: "Run a risk analysis from the Input page to see results." }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "a",
        {
          href: "/input_v20",
          className: "inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-medium transition-all shadow-lg shadow-blue-500/25",
          children: [
            "Start Analysis",
            /* @__PURE__ */ jsxRuntimeExports.jsx(ArrowRight, { className: "w-5 h-5" })
          ]
        }
      )
    ] }) });
  }
  const isEmptyData = viewModel.overview.riskScore.score === 0 && viewModel.overview.riskScore.level === "Unknown";
  if (isEmptyData) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8 flex items-center justify-center", children: /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { className: "max-w-md text-center", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-20 h-20 mx-auto mb-6 rounded-full bg-blue-500/10 flex items-center justify-center", children: /* @__PURE__ */ jsxRuntimeExports.jsx(TrendingUp, { className: "w-10 h-10 text-blue-400" }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-2xl font-bold text-white mb-2", children: "Ready for Analysis" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-white/60 mb-6", children: "Submit shipment data to generate risk intelligence." }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("a", { href: "/input_v20", className: "inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-medium", children: [
        "Go to Input ",
        /* @__PURE__ */ jsxRuntimeExports.jsx(ArrowRight, { className: "w-5 h-5" })
      ] })
    ] }) });
  }
  const riskLevel = viewModel.overview.riskScore.level.toUpperCase();
  const confidence = viewModel.overview.riskScore.confidence / 100;
  const riskScore = viewModel.overview.riskScore.score;
  const layersData = viewModel.breakdown.layers.map((l) => ({
    name: l.name,
    score: l.score,
    contribution: l.contribution,
    category: l.category || "UNKNOWN",
    enabled: l.enabled !== false,
    status: l.score >= 70 ? "ALERT" : l.score >= 40 ? "WARNING" : "NORMAL",
    notes: `Contributing ${l.contribution}% to overall risk`,
    confidence: viewModel.overview.riskScore.confidence
  }));
  const shipmentData = {
    shipmentId: viewModel.overview.shipment.id || "SHIP-001",
    route: { pol: viewModel.overview.shipment.pol, pod: viewModel.overview.shipment.pod },
    carrier: viewModel.overview.shipment.carrier || "Ocean Carrier",
    etd: viewModel.overview.shipment.etd || "N/A",
    eta: viewModel.overview.shipment.eta || "N/A",
    dataConfidence: confidence,
    cargoValue: viewModel.overview.shipment.cargoValue,
    lastUpdated: (/* @__PURE__ */ new Date()).toLocaleString()
  };
  const explanation = viewModel.overview.reasoning.explanation;
  const fallbackExplanation = riskScore < 30 ? `This shipment from ${viewModel.overview.shipment.pol || "origin"} to ${viewModel.overview.shipment.pod || "destination"} has a LOW risk score of ${Math.round(riskScore)}. Current conditions indicate minimal disruption risk with ${Math.round(confidence * 100)}% confidence. No significant risk factors detected that would require immediate action.` : `Risk assessment complete with score of ${Math.round(riskScore)} and ${Math.round(confidence * 100)}% confidence.`;
  const layerInsights = layersData.filter((l) => l.score > 0 || l.contribution > 0).slice(0, 4).map((l) => `${l.name}: Score ${l.score}, contributing ${l.contribution}% to risk profile`);
  const narrativeData = {
    executiveSummary: explanation || fallbackExplanation,
    keyInsights: viewModel.drivers.length > 0 ? viewModel.drivers.slice(0, 4).map(
      (d) => `${d.name}: ${d.impact > 0 ? "Increases" : "Decreases"} risk by ${Math.abs(d.impact)}%`
    ) : layerInsights.length > 0 ? layerInsights : [`Overall risk level: ${riskLevel}`, `Confidence: ${Math.round(confidence * 100)}%`, `Transit time: ${viewModel.overview.shipment.transitTime} days`],
    actionItems: viewModel.scenarios.length > 0 ? viewModel.scenarios.slice(0, 4).map((s) => s.title) : riskScore < 30 ? ["Continue monitoring shipment", "No immediate action required", "Standard insurance coverage recommended"] : ["Review risk mitigation options", "Consider insurance coverage"],
    riskDrivers: viewModel.drivers.length > 0 ? viewModel.drivers.map((d) => d.name) : layersData.filter((l) => l.score > 30).map((l) => l.name),
    confidenceNotes: `Analysis based on ${Math.round(confidence * 100)}% data confidence. ${riskScore < 30 ? "Low risk - standard monitoring applies." : ""}`
  };
  const scenarioData = viewModel.timeline.projections.length > 0 ? viewModel.timeline.projections.map((p, i) => ({
    date: p.date || `Day ${i + 1}`,
    p10: p.p10,
    p50: p.p50,
    p90: p.p90,
    expected: p.p50
  })) : Array.from({ length: 7 }, (_, idx) => ({
    date: `Day ${idx + 1}`,
    p10: Math.max(0, riskScore - 10 - Math.random() * 5),
    p50: riskScore + (Math.random() - 0.5) * 10,
    p90: Math.min(100, riskScore + 10 + Math.random() * 5),
    expected: riskScore
  }));
  const sensitivityDrivers = viewModel.drivers.length > 0 ? viewModel.drivers.map((d) => ({
    name: d.name,
    impact: d.impact,
    impactMagnitude: Math.abs(d.impact)
  })) : layersData.filter((l) => l.score > 0 || l.contribution > 0).map((l) => ({
    name: l.name.replace(" Risk", ""),
    impact: l.contribution > 0 ? l.contribution : l.score * 0.3,
    impactMagnitude: l.contribution > 0 ? l.contribution : l.score * 0.3
  })).sort((a, b) => b.impact - a.impact);
  const baseScenarios = viewModel.scenarios.length > 0 && viewModel.scenarios.some((s) => s.riskReduction > 0) ? viewModel.scenarios.map((s) => ({
    title: s.title,
    riskReduction: s.riskReduction,
    costImpact: s.costImpact,
    description: s.description,
    feasibility: 0.7 + Math.random() * 0.3
  })) : [
    // Generate sample mitigation scenarios for visualization
    {
      title: "Current Plan (Baseline)",
      riskReduction: 0,
      costImpact: 0,
      description: "Proceed with current plan without changes",
      feasibility: 1
    },
    {
      title: "Enhanced Monitoring",
      riskReduction: Math.max(2, riskScore * 0.1),
      costImpact: 0.5,
      description: "Add real-time tracking and alerts",
      feasibility: 0.95
    },
    {
      title: "Premium Insurance",
      riskReduction: Math.max(5, riskScore * 0.25),
      costImpact: 1.5,
      description: "Comprehensive cargo insurance coverage",
      feasibility: 0.9
    },
    {
      title: "Express Routing",
      riskReduction: Math.max(3, riskScore * 0.15),
      costImpact: 2.5,
      description: "Faster route with premium carrier",
      feasibility: 0.85
    },
    {
      title: "Full Protection Package",
      riskReduction: Math.max(8, riskScore * 0.4),
      costImpact: 4,
      description: "Combined insurance + monitoring + express",
      feasibility: 0.75
    }
  ];
  const scenariosForFrontier = baseScenarios;
  const displayScenarios = baseScenarios.map((s, idx) => ({
    ...s,
    isRecommended: idx === Math.floor(baseScenarios.length / 2)
    // Middle option (best balance)
  }));
  const dataReliabilityDomains = [
    { domain: "Port Data", confidence: 0.92, completeness: 0.95, freshness: 0.88, notes: "Real-time port congestion data" },
    { domain: "Weather", confidence: 0.85, completeness: 0.9, freshness: 0.95, notes: "7-day forecast accuracy" },
    { domain: "Geopolitical", confidence: 0.78, completeness: 0.82, freshness: 0.75, notes: "Risk index from multiple sources" },
    { domain: "Carrier", confidence: 0.88, completeness: 0.85, freshness: 0.92, notes: "Historical carrier performance" }
  ];
  const financialMetrics = {
    expectedLoss: viewModel.loss?.expectedLoss || 0,
    var95: viewModel.loss?.p95 || 0,
    cvar95: viewModel.loss?.p99 || 0,
    stdDev: (viewModel.loss?.p99 || 0) * 0.2,
    histogram: [],
    lossCurve: Array.from({ length: 20 }, (_, i) => ({
      loss: i * 5e3,
      probability: Math.exp(-i * 0.3) * 0.3
    }))
  };
  const getRiskColor2 = () => {
    if (riskScore >= 70) return "from-red-500 to-orange-500";
    if (riskScore >= 40) return "from-amber-500 to-yellow-500";
    return "from-emerald-500 to-green-500";
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "fixed inset-0 pointer-events-none overflow-hidden", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "absolute top-0 left-1/4 w-[600px] h-[600px] bg-blue-500/5 rounded-full blur-3xl animate-pulse" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "absolute bottom-0 right-1/4 w-[600px] h-[600px] bg-purple-500/5 rounded-full blur-3xl animate-pulse", style: { animationDelay: "1s" } }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "absolute top-1/2 left-1/2 w-[400px] h-[400px] bg-cyan-500/5 rounded-full blur-3xl animate-pulse", style: { animationDelay: "2s" } })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "relative z-10 max-w-[1600px] mx-auto p-6 lg:p-8 space-y-8", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("header", { className: "flex flex-wrap items-center justify-between gap-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("h1", { className: "text-3xl lg:text-4xl font-bold text-white tracking-tight flex items-center gap-3", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Activity, { className: "w-6 h-6 text-white" }) }),
            "RISKCAST",
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-blue-400", children: "." })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-white/50 mt-1 ml-15", children: "Enterprise Risk Intelligence Platform" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-3", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex bg-white/5 rounded-xl p-1 border border-white/10", children: ["overview", "analytics", "decisions"].map((tab) => /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              onClick: () => setActiveTab(tab),
              className: `px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === tab ? "bg-white/10 text-white" : "text-white/50 hover:text-white/80"}`,
              children: t(tab)
            },
            tab
          )) }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(HeaderLangSwitcher, {}),
          /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "button",
            {
              onClick: () => fetchResults(true),
              disabled: loading,
              className: "px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white rounded-xl font-medium transition-all flex items-center gap-2 shadow-lg shadow-blue-500/25 disabled:opacity-50",
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx(RefreshCw, { className: `w-4 h-4 ${loading ? "animate-spin" : ""}` }),
                t("refresh")
              ]
            }
          )
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(ShipmentHeader, { data: shipmentData }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { variant: "compact", className: "text-center", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Target, { className: "w-6 h-6 text-blue-400 mx-auto mb-2" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-2xl font-bold text-white", children: Math.round(riskScore) }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-white/50", children: "Risk Score" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { variant: "compact", className: "text-center", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(DollarSign, { className: "w-6 h-6 text-emerald-400 mx-auto mb-2" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: "text-2xl font-bold text-white", children: [
            "$",
            viewModel.loss ? (viewModel.loss.expectedLoss / 1e3).toFixed(1) : "0",
            "K"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-white/50", children: "Expected Loss" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { variant: "compact", className: "text-center", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(TriangleAlert, { className: "w-6 h-6 text-amber-400 mx-auto mb-2" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: "text-2xl font-bold text-white", children: [
            "$",
            viewModel.loss ? (viewModel.loss.p95 / 1e3).toFixed(1) : "0",
            "K"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-white/50", children: "VaR 95%" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { variant: "compact", className: "text-center", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Shield, { className: "w-6 h-6 text-red-400 mx-auto mb-2" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: "text-2xl font-bold text-white", children: [
            "$",
            viewModel.loss ? (viewModel.loss.p99 / 1e3).toFixed(1) : "0",
            "K"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-white/50", children: "CVaR 99%" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { variant: "compact", className: "text-center", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Layers, { className: "w-6 h-6 text-purple-400 mx-auto mb-2" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-2xl font-bold text-white", children: layersData.length }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-white/50", children: "Risk Layers" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { variant: "compact", className: "text-center", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Brain, { className: "w-6 h-6 text-cyan-400 mx-auto mb-2" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: "text-2xl font-bold text-white", children: [
            Math.round(confidence * 100),
            "%"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-white/50", children: "Confidence" })
        ] })
      ] }),
      activeTab === "overview" && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-8", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-1 lg:grid-cols-3 gap-6", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { variant: "hero", className: "flex flex-col items-center justify-center py-8 relative overflow-hidden", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: `absolute inset-0 bg-gradient-to-br ${getRiskColor2()} opacity-5` }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(RiskOrbPremium, { score: Math.round(riskScore), riskLevel }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mt-6 text-center relative z-10", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex items-center justify-center gap-2 mb-2", children: /* @__PURE__ */ jsxRuntimeExports.jsx(BadgeRisk, { level: riskLevel, size: "lg" }) }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-white/60 text-sm max-w-xs mx-auto", children: viewModel.overview.reasoning.explanation || "Risk assessment complete" })
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(GlassCard, { className: "flex items-center justify-center", children: /* @__PURE__ */ jsxRuntimeExports.jsx(ConfidenceGauge, { confidence, showPercentage: true }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("h3", { className: "text-lg font-semibold text-white mb-4 flex items-center gap-2", children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx(MapPin, { className: "w-5 h-5 text-blue-400" }),
                "Route Details"
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-3", children: [
                /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex justify-between items-center p-3 bg-white/5 rounded-lg", children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/60", children: "Origin" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white font-medium", children: viewModel.overview.shipment.pol })
                ] }),
                /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex justify-between items-center p-3 bg-white/5 rounded-lg", children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/60", children: "Destination" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white font-medium", children: viewModel.overview.shipment.pod })
                ] }),
                /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex justify-between items-center p-3 bg-white/5 rounded-lg", children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/60", children: "Transit Time" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "text-white font-medium", children: [
                    viewModel.overview.shipment.transitTime,
                    " days"
                  ] })
                ] }),
                /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex justify-between items-center p-3 bg-white/5 rounded-lg", children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/60", children: "Cargo Value" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "text-white font-medium", children: [
                    "$",
                    ((viewModel.overview.shipment.cargoValue || 0) / 1e3).toFixed(0),
                    "K"
                  ] })
                ] })
              ] })
            ] })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-1 lg:grid-cols-2 gap-6", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(RiskRadar, { layers: layersData }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(RiskContributionWaterfall, { layers: layersData, overallScore: riskScore })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(ExecutiveNarrative, { narrative: narrativeData }),
        viewModel.drivers.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("h2", { className: "text-xl font-semibold text-white mb-6 flex items-center gap-2", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Zap, { className: "w-5 h-5 text-amber-400" }),
            "Risk Drivers Impact Analysis"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4", children: viewModel.drivers.slice(0, 8).map((driver, idx) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "div",
            {
              className: `p-4 rounded-xl border transition-all hover:scale-[1.02] ${driver.impact > 0 ? "bg-red-500/5 border-red-500/20 hover:border-red-500/40" : "bg-emerald-500/5 border-emerald-500/20 hover:border-emerald-500/40"}`,
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-start justify-between mb-2", children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white font-medium text-sm", children: driver.name }),
                  driver.impact > 0 ? /* @__PURE__ */ jsxRuntimeExports.jsx(CircleAlert, { className: "w-4 h-4 text-red-400" }) : /* @__PURE__ */ jsxRuntimeExports.jsx(CircleCheck, { className: "w-4 h-4 text-emerald-400" })
                ] }),
                /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: `text-2xl font-bold ${driver.impact > 0 ? "text-red-400" : "text-emerald-400"}`, children: [
                  driver.impact > 0 ? "+" : "",
                  driver.impact,
                  "%"
                ] }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-white/50 mt-1", children: driver.description || "Impact on risk score" })
              ]
            },
            idx
          )) })
        ] })
      ] }),
      activeTab === "analytics" && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-8", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          RiskScenarioFanChart,
          {
            data: scenarioData,
            etd: viewModel.overview.shipment.etd || "N/A",
            eta: viewModel.overview.shipment.eta || "N/A"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(RiskSensitivityTornado, { drivers: sensitivityDrivers }),
        scenariosForFrontier.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsx(
          RiskCostEfficiencyFrontier,
          {
            scenarios: scenariosForFrontier,
            baselineRisk: riskScore,
            highlightedScenario: null
          }
        ),
        viewModel.loss && viewModel.loss.expectedLoss > 0 && /* @__PURE__ */ jsxRuntimeExports.jsx(FinancialModule, { financial: financialMetrics }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(LayersTable, { layers: layersData }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(DataReliabilityMatrix, { domains: dataReliabilityDomains })
      ] }),
      activeTab === "decisions" && (() => {
        const recommendedScenario = displayScenarios.find((s) => s.isRecommended) || displayScenarios[Math.floor(displayScenarios.length / 2)];
        const maxProtectionScenario = displayScenarios[displayScenarios.length - 1];
        return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-8", children: [
          displayScenarios.length > 0 && recommendedScenario && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-1 lg:grid-cols-2 gap-6", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              PrimaryRecommendationCard,
              {
                title: recommendedScenario.title,
                badge: "TOP RECOMMENDATION",
                riskReduction: recommendedScenario.riskReduction,
                costImpact: `$${recommendedScenario.costImpact.toFixed(1)}K`,
                confidence,
                rationale: recommendedScenario.description,
                currentRisk: riskScore,
                newRisk: Math.max(0, riskScore - recommendedScenario.riskReduction)
              }
            ),
            displayScenarios.length > 3 && maxProtectionScenario && /* @__PURE__ */ jsxRuntimeExports.jsx(
              PrimaryRecommendationCard,
              {
                title: maxProtectionScenario.title,
                badge: "MAXIMUM PROTECTION",
                riskReduction: maxProtectionScenario.riskReduction,
                costImpact: `$${maxProtectionScenario.costImpact.toFixed(1)}K`,
                confidence: confidence * 0.85,
                rationale: maxProtectionScenario.description,
                currentRisk: riskScore,
                newRisk: Math.max(0, riskScore - maxProtectionScenario.riskReduction)
              }
            )
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-1 md:grid-cols-3 gap-4", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              SecondaryRecommendationCard,
              {
                category: "Insurance",
                badge: { text: viewModel.decisions.insurance.status, type: "consider" },
                metric: viewModel.decisions.insurance.recommendation,
                context: viewModel.decisions.insurance.rationale,
                confidence
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              SecondaryRecommendationCard,
              {
                category: "Timing",
                badge: { text: viewModel.decisions.timing.status, type: "evaluate" },
                metric: viewModel.decisions.timing.recommendation,
                context: viewModel.decisions.timing.rationale,
                confidence
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              SecondaryRecommendationCard,
              {
                category: "Routing",
                badge: { text: viewModel.decisions.routing.status, type: "consider" },
                metric: viewModel.decisions.routing.recommendation,
                context: viewModel.decisions.routing.rationale,
                confidence
              }
            )
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("h2", { className: "text-xl font-semibold text-white mb-6 flex items-center gap-2", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(ChartColumn, { className: "w-5 h-5 text-blue-400" }),
              "Decision Support Matrix"
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "overflow-x-auto", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("table", { className: "w-full", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("thead", { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("tr", { className: "border-b border-white/10", children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("th", { className: "text-left py-3 px-4 text-sm font-medium text-white/60", children: "Category" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("th", { className: "text-left py-3 px-4 text-sm font-medium text-white/60", children: "Status" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("th", { className: "text-left py-3 px-4 text-sm font-medium text-white/60", children: "Action" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("th", { className: "text-left py-3 px-4 text-sm font-medium text-white/60", children: "Potential Impact" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("th", { className: "text-left py-3 px-4 text-sm font-medium text-white/60", children: "Confidence" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("th", { className: "text-left py-3 px-4 text-sm font-medium text-white/60", children: "Rationale" })
              ] }) }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("tbody", { children: [
                {
                  cat: "Insurance",
                  icon: "🛡️",
                  ...viewModel.decisions.insurance,
                  impact: riskScore < 30 ? "Minimal" : riskScore < 60 ? "-5 to -10 pts" : "-10 to -20 pts",
                  impactColor: riskScore < 30 ? "text-emerald-400" : "text-amber-400"
                },
                {
                  cat: "Timing",
                  icon: "⏱️",
                  ...viewModel.decisions.timing,
                  impact: riskScore < 30 ? "Minimal" : riskScore < 60 ? "-3 to -8 pts" : "-8 to -15 pts",
                  impactColor: riskScore < 30 ? "text-emerald-400" : "text-amber-400"
                },
                {
                  cat: "Routing",
                  icon: "🗺️",
                  ...viewModel.decisions.routing,
                  impact: riskScore < 30 ? "Minimal" : riskScore < 60 ? "-2 to -5 pts" : "-5 to -12 pts",
                  impactColor: riskScore < 30 ? "text-emerald-400" : "text-amber-400"
                }
              ].map((row, idx) => /* @__PURE__ */ jsxRuntimeExports.jsxs("tr", { className: "border-b border-white/5 hover:bg-white/5 transition-colors group", children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("td", { className: "py-4 px-4", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-lg", children: row.icon }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-sm font-medium text-white", children: row.cat })
                ] }) }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("td", { className: "py-4 px-4", children: /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: `text-xs px-3 py-1.5 rounded-full font-medium inline-flex items-center gap-1 ${row.status === "RECOMMENDED" ? "bg-gradient-to-r from-green-500/20 to-emerald-500/20 text-green-400 border border-green-500/30" : row.status === "NOT_NEEDED" ? "bg-gradient-to-r from-blue-500/10 to-cyan-500/10 text-cyan-400 border border-cyan-500/20" : String(row.status).includes("EVAL") ? "bg-gradient-to-r from-amber-500/20 to-orange-500/20 text-amber-400 border border-amber-500/30" : "bg-white/10 text-white/60 border border-white/10"}`, children: row.status === "NOT_NEEDED" ? "✓ Optional" : row.status === "RECOMMENDED" ? "★ Recommended" : String(row.status).includes("EVAL") ? "⚡ Evaluate" : row.status }) }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("td", { className: "py-4 px-4", children: /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-sm text-white font-medium", children: row.recommendation }) }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("td", { className: "py-4 px-4", children: /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: `text-sm font-medium ${row.impactColor}`, children: row.impact }) }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("td", { className: "py-4 px-4", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-16 h-2 bg-white/10 rounded-full overflow-hidden", children: /* @__PURE__ */ jsxRuntimeExports.jsx(
                    "div",
                    {
                      className: "h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full",
                      style: { width: `${Math.round(confidence * 100)}%` }
                    }
                  ) }),
                  /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "text-xs text-white/60", children: [
                    Math.round(confidence * 100),
                    "%"
                  ] })
                ] }) }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("td", { className: "py-4 px-4 text-sm text-white/60 max-w-xs", children: /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "line-clamp-2 group-hover:line-clamp-none transition-all", children: row.rationale }) })
              ] }, idx)) })
            ] }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mt-6 pt-4 border-t border-white/10 flex items-center justify-between", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-4 text-xs text-white/50", children: [
                /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "flex items-center gap-1", children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "w-2 h-2 rounded-full bg-cyan-400" }),
                  "Optional = Low priority"
                ] }),
                /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "flex items-center gap-1", children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "w-2 h-2 rounded-full bg-amber-400" }),
                  "Evaluate = Review needed"
                ] }),
                /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "flex items-center gap-1", children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "w-2 h-2 rounded-full bg-green-400" }),
                  "Recommended = Take action"
                ] })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-xs text-white/40", children: [
                "Overall Risk: ",
                riskScore < 30 ? "LOW" : riskScore < 60 ? "MEDIUM" : "HIGH",
                " (",
                Math.round(riskScore),
                "/100)"
              ] })
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("h2", { className: "text-xl font-semibold text-white mb-6 flex items-center gap-2", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(ChartLine, { className: "w-5 h-5 text-purple-400" }),
              "All Mitigation Scenarios"
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4", children: displayScenarios.map((scenario, idx) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
              "div",
              {
                className: `p-4 rounded-xl border transition-all hover:scale-[1.02] cursor-pointer ${scenario.isRecommended ? "bg-gradient-to-br from-blue-500/20 to-purple-500/10 border-blue-500/40 shadow-lg shadow-blue-500/10" : idx === 0 ? "bg-white/5 border-white/20" : "bg-white/5 border-white/10 hover:border-white/30"}`,
                children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-start justify-between mb-3", children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-white font-medium", children: scenario.title }),
                    scenario.isRecommended ? /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs px-2 py-1 bg-blue-500/30 text-blue-300 rounded-full font-medium", children: "✓ Best Value" }) : idx === 0 ? /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs px-2 py-1 bg-white/10 text-white/60 rounded-full", children: "Baseline" }) : idx === displayScenarios.length - 1 ? /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs px-2 py-1 bg-purple-500/20 text-purple-300 rounded-full", children: "Max Protection" }) : null
                  ] }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-white/60 mb-3", children: scenario.description }),
                  /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between text-sm", children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
                      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/60", children: "Risk Reduction: " }),
                      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: `font-medium ${scenario.riskReduction > 0 ? "text-emerald-400" : "text-white/40"}`, children: scenario.riskReduction > 0 ? `-${Math.round(scenario.riskReduction)} pts` : "—" })
                    ] }),
                    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
                      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/60", children: "Cost: " }),
                      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white font-medium", children: scenario.costImpact > 0 ? `$${scenario.costImpact.toFixed(1)}K` : "Free" })
                    ] })
                  ] }),
                  /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mt-3 pt-3 border-t border-white/10", children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between text-xs mb-1", children: [
                      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/50", children: "Feasibility" }),
                      /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "text-white/70", children: [
                        Math.round((scenario.feasibility || 0.85) * 100),
                        "%"
                      ] })
                    ] }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-full h-1.5 bg-white/10 rounded-full overflow-hidden", children: /* @__PURE__ */ jsxRuntimeExports.jsx(
                      "div",
                      {
                        className: "h-full bg-gradient-to-r from-emerald-500 to-blue-500 rounded-full",
                        style: { width: `${(scenario.feasibility || 0.85) * 100}%` }
                      }
                    ) })
                  ] })
                ]
              },
              idx
            )) })
          ] })
        ] });
      })(),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("footer", { className: "text-center py-8 border-t border-white/10", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-center gap-2 text-white/30 text-sm mb-2", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Activity, { className: "w-4 h-4" }),
          "RISKCAST Enterprise Risk Intelligence"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: "text-white/20 text-xs", children: [
          "Engine v2 • Last updated: ",
          (/* @__PURE__ */ new Date()).toLocaleString(),
          " • Data Confidence: ",
          Math.round(confidence * 100),
          "%"
        ] })
      ] })
    ] })
  ] });
}
function Header({ saveState, lastSaved }) {
  const getTimeSince = (date) => {
    const seconds = Math.floor(((/* @__PURE__ */ new Date()).getTime() - date.getTime()) / 1e3);
    if (seconds < 60) return "just now";
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ago`;
  };
  const saveStateConfig = {
    saved: {
      icon: CircleCheckBig,
      text: "All changes saved",
      color: "text-green-400",
      show: true
    },
    saving: {
      icon: RefreshCw,
      text: "Saving...",
      color: "text-cyan-400",
      show: true,
      spin: true
    },
    unsaved: {
      icon: CircleAlert,
      text: "Unsaved changes",
      color: "text-orange-400",
      show: true,
      pulse: true
    },
    error: {
      icon: CircleAlert,
      text: "Save failed",
      color: "text-red-400",
      show: true
    }
  };
  const config = saveStateConfig[saveState];
  const Icon2 = config.icon;
  return /* @__PURE__ */ jsxRuntimeExports.jsx("header", { className: "sticky top-0 z-50 h-[72px] bg-[#0a1628]/80 backdrop-blur-sm border-b border-white/10", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "h-full px-12 flex items-center justify-between", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-6", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-3", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-10 h-10 rounded-xl bg-gradient-to-br from-[#00D9FF] to-[#0088FF] flex items-center justify-center", children: /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xl", children: "⚡" }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-white tracking-wide", children: "RISKCAST" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-white/50 text-xs", children: "FutureOS" })
        ] })
      ] }),
      config.show && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: `flex items-center gap-2 text-sm ${config.color}`, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Icon2, { className: `w-4 h-4 ${config.spin ? "animate-spin" : ""} ${config.pulse ? "animate-pulse" : ""}` }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: config.text })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-3", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 text-white/40 text-xs", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Clock, { className: "w-3 h-3" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
          "Last saved: ",
          getTimeSince(lastSaved)
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "button",
        {
          className: "p-2.5 border border-white/10 rounded-lg hover:border-[#00D9FF]/50 transition-all",
          title: "Change language",
          children: /* @__PURE__ */ jsxRuntimeExports.jsx(Globe, { className: "w-5 h-5 text-white/70" })
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "button",
        {
          className: "p-2.5 border border-white/10 rounded-lg hover:border-[#00D9FF]/50 transition-all",
          title: "Refresh data",
          children: /* @__PURE__ */ jsxRuntimeExports.jsx(RefreshCw, { className: "w-5 h-5 text-white/70" })
        }
      )
    ] })
  ] }) });
}
function HeroOverview({ data }) {
  const ModeIcon = data.trade.mode === "AIR" ? Plane : data.trade.mode === "SEA" ? Ship : Truck;
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "backdrop-blur-xl bg-gradient-to-br from-white/10 to-white/5 border border-white/10 rounded-[24px] p-8 shadow-[0_8px_32px_rgba(0,0,0,0.3)]", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-6 gap-8", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "col-span-2", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-cyan-400/70 text-xs uppercase tracking-wider mb-3", children: "Route" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-4", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-center", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-white/90 text-2xl", children: data.trade.pol }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-white/50 text-xs mt-1", children: data.trade.polCity })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex-1 flex items-center gap-2", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "h-px flex-1 bg-gradient-to-r from-cyan-500/50 to-teal-500/50" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(ModeIcon, { className: "w-5 h-5 text-cyan-400" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "h-px flex-1 bg-gradient-to-r from-teal-500/50 to-cyan-500/50" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-center", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-white/90 text-2xl", children: data.trade.pod }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-white/50 text-xs mt-1", children: data.trade.podCity })
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-cyan-400/70 text-xs uppercase tracking-wider mb-3", children: "Transport Mode" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "inline-flex items-center gap-2 px-4 py-2.5 bg-[#00D9FF]/20 border border-[#00D9FF]/30 rounded-xl", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(ModeIcon, { className: "w-4 h-4 text-cyan-400" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white", children: data.trade.mode })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-cyan-400/70 text-xs uppercase tracking-wider mb-3", children: "Container" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-white/90", children: data.trade.container_type }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-white/50 text-sm mt-1", children: data.trade.mode === "AIR" ? "Air Cargo Unit" : "Container" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-cyan-400/70 text-xs uppercase tracking-wider mb-3", children: "Transit & Weight" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-white/90", children: [
          data.trade.transit_time_days,
          " days"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-white/50 text-sm mt-1", children: [
          data.cargo.gross_weight_kg.toLocaleString(),
          " kg"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-white/40 text-xs mt-1", children: [
          data.cargo.volume_cbm,
          " CBM"
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-cyan-400/70 text-xs uppercase tracking-wider mb-3", children: "Shipment Value" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-white/90 text-xl", children: [
          "$",
          data.value.toLocaleString()
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-white/50 text-sm mt-1", children: "USD" })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mt-6 pt-6 border-t border-white/10 flex items-center justify-between", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-3", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-2 h-2 bg-green-400 rounded-full animate-pulse" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/70 text-sm", children: "Ready for Analysis" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-white/40 text-xs", children: "Updated just now" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-3", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/50 text-sm", children: "Data Confidence:" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-32 h-1 bg-white/10 rounded-full overflow-hidden", children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "h-full w-[95%] bg-gradient-to-r from-cyan-500 to-teal-500 rounded-full" }) }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-teal-400 text-sm", children: "95%" })
        ] })
      ] })
    ] })
  ] });
}
function FieldTile({ label, value, path, hasError, hasWarning, onClick }) {
  const displayValue = typeof value === "boolean" ? value ? "Yes" : "No" : value;
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      className: `
        group cursor-pointer rounded-xl p-4 
        bg-white/5 hover:bg-white/10 border border-white/10 
        transition-all duration-200
        ${hasError ? "border-red-500/50 bg-red-500/10" : ""}
        ${hasWarning && !hasError ? "border-orange-400/50 bg-orange-400/10" : ""}
      `,
      onClick: () => onClick(path),
      "data-field-path": path,
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-start justify-between mb-2", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/50 text-xs uppercase tracking-wide", children: label }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-1", children: [
            hasError && /* @__PURE__ */ jsxRuntimeExports.jsx(CircleAlert, { className: "w-3.5 h-3.5 text-red-400" }),
            hasWarning && !hasError && /* @__PURE__ */ jsxRuntimeExports.jsx(TriangleAlert, { className: "w-3.5 h-3.5 text-orange-400" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(ChevronRight, { className: "w-4 h-4 text-white/30 group-hover:text-cyan-400 transition-colors" })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-white/90 font-medium truncate", children: displayValue || "—" })
      ]
    }
  );
}
function InfoPanel({ title, icon, fields, validationIssues, onFieldClick }) {
  const IconComponent = icon === "trade" ? Plane : icon === "cargo" ? Package : icon === "seller" ? Building2 : User;
  const iconGradients = {
    trade: "from-blue-500 to-cyan-500",
    cargo: "from-green-500 to-emerald-500",
    seller: "from-amber-500 to-orange-500",
    buyer: "from-purple-500 to-pink-500"
  };
  const getFieldIssues = (path) => {
    return validationIssues.filter((issue) => issue.affectedFields.includes(path));
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "backdrop-blur-xl bg-white/5 border border-white/10 rounded-[20px] p-6", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-3 mb-6", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: `w-10 h-10 rounded-xl bg-gradient-to-br ${iconGradients[icon]} flex items-center justify-center shadow-lg`, children: /* @__PURE__ */ jsxRuntimeExports.jsx(IconComponent, { className: "w-5 h-5 text-white" }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-white font-medium", children: title }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: "text-white/40 text-xs", children: [
          fields.length,
          " fields"
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "grid grid-cols-2 gap-3", children: fields.map((field) => {
      const issues = getFieldIssues(field.path);
      const hasError = issues.some((i) => i.severity === "critical");
      const hasWarning = issues.some((i) => i.severity === "warning");
      return /* @__PURE__ */ jsxRuntimeExports.jsx(
        FieldTile,
        {
          label: field.label,
          value: field.value,
          path: field.path,
          hasError,
          hasWarning,
          onClick: onFieldClick
        },
        field.path
      );
    }) })
  ] });
}
function AIAdvisor({ issues, onIssueClick }) {
  const critical = issues.filter((i) => i.severity === "critical");
  const warnings = issues.filter((i) => i.severity === "warning");
  const suggestions = issues.filter((i) => i.severity === "suggestion");
  const renderIssue = (issue) => {
    const config = {
      critical: {
        icon: CircleAlert,
        bg: "bg-red-500/20",
        border: "border-red-500/30",
        iconColor: "text-red-400",
        btnColor: "bg-red-500/30 text-red-300"
      },
      warning: {
        icon: TriangleAlert,
        bg: "bg-orange-500/20",
        border: "border-orange-500/30",
        iconColor: "text-orange-400",
        btnColor: "bg-orange-500/30 text-orange-300"
      },
      suggestion: {
        icon: Lightbulb,
        bg: "bg-blue-500/20",
        border: "border-blue-500/30",
        iconColor: "text-blue-400",
        btnColor: "bg-blue-500/30 text-blue-300"
      }
    }[issue.severity];
    const Icon2 = config.icon;
    return /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        className: `${config.bg} border ${config.border} rounded-xl p-4 cursor-pointer hover:scale-[1.02] transition-transform`,
        onClick: () => onIssueClick(issue),
        children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-start gap-3", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Icon2, { className: `w-5 h-5 ${config.iconColor} flex-shrink-0 mt-0.5` }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex-1 min-w-0", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between gap-2", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white font-medium text-sm truncate", children: issue.message }),
              issue.action && /* @__PURE__ */ jsxRuntimeExports.jsxs("button", { className: `${config.btnColor} px-2 py-0.5 rounded text-xs font-medium flex items-center gap-1`, children: [
                issue.action,
                /* @__PURE__ */ jsxRuntimeExports.jsx(ChevronRight, { className: "w-3 h-3" })
              ] })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-white/50 text-xs mt-1", children: issue.detail })
          ] })
        ] })
      },
      issue.id
    );
  };
  if (issues.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "backdrop-blur-xl bg-white/5 border border-white/10 rounded-[20px] p-6 h-full", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-3 mb-6", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center", children: /* @__PURE__ */ jsxRuntimeExports.jsx(CircleCheckBig, { className: "w-5 h-5 text-white" }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-white font-medium", children: "AI Advisor" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-white/40 text-xs", children: "Real-time validation" })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex flex-col items-center justify-center py-12 text-center", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mb-4", children: /* @__PURE__ */ jsxRuntimeExports.jsx(CircleCheckBig, { className: "w-8 h-8 text-green-400" }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("h4", { className: "text-white font-medium mb-2", children: "All Clear!" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-white/50 text-sm", children: "No validation issues detected. Your shipment data is ready for analysis." })
      ] })
    ] });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "backdrop-blur-xl bg-white/5 border border-white/10 rounded-[20px] p-6 h-full", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-3 mb-6", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center", children: /* @__PURE__ */ jsxRuntimeExports.jsx(CircleAlert, { className: "w-5 h-5 text-white" }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-white font-medium", children: "AI Advisor" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-white/40 text-xs", children: "Real-time validation" })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex gap-2 mb-6", children: [
      critical.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-1.5 px-3 py-1.5 bg-red-500/20 border border-red-500/30 rounded-full", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(CircleAlert, { className: "w-3.5 h-3.5 text-red-400" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "text-red-300 text-xs font-medium", children: [
          critical.length,
          " Critical"
        ] })
      ] }),
      warnings.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-1.5 px-3 py-1.5 bg-orange-500/20 border border-orange-500/30 rounded-full", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(TriangleAlert, { className: "w-3.5 h-3.5 text-orange-400" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "text-orange-300 text-xs font-medium", children: [
          warnings.length,
          " Warnings"
        ] })
      ] }),
      suggestions.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-1.5 px-3 py-1.5 bg-blue-500/20 border border-blue-500/30 rounded-full", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Lightbulb, { className: "w-3.5 h-3.5 text-blue-400" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "text-blue-300 text-xs font-medium", children: [
          suggestions.length,
          " Tips"
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-3 max-h-[500px] overflow-y-auto pr-2", children: [
      critical.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-red-400/80 text-xs uppercase tracking-wider font-medium", children: "Critical Issues" }),
        critical.map(renderIssue)
      ] }),
      warnings.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-orange-400/80 text-xs uppercase tracking-wider font-medium mt-4", children: "Warnings" }),
        warnings.map(renderIssue)
      ] }),
      suggestions.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-blue-400/80 text-xs uppercase tracking-wider font-medium mt-4", children: "Suggestions" }),
        suggestions.map(renderIssue)
      ] })
    ] })
  ] });
}
function IntelligenceModules({ modules, onToggle }) {
  const moduleConfig = [
    {
      key: "esg",
      label: "ESG Score",
      icon: Leaf,
      description: "Environmental, Social & Governance",
      gradient: "from-green-500 to-emerald-500"
    },
    {
      key: "weather",
      label: "Weather",
      icon: Cloud,
      description: "Route weather forecast",
      gradient: "from-blue-500 to-cyan-500"
    },
    {
      key: "portCongestion",
      label: "Port Congestion",
      icon: Anchor,
      description: "Port delay prediction",
      gradient: "from-amber-500 to-orange-500"
    },
    {
      key: "carrierPerformance",
      label: "Carrier",
      icon: TrendingUp,
      description: "Carrier reliability score",
      gradient: "from-purple-500 to-pink-500"
    },
    {
      key: "marketScanner",
      label: "Market Scanner",
      icon: Search,
      description: "Market rate analysis",
      gradient: "from-indigo-500 to-blue-500"
    },
    {
      key: "insurance",
      label: "Insurance",
      icon: Shield,
      description: "Coverage recommendation",
      gradient: "from-teal-500 to-cyan-500"
    }
  ];
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "backdrop-blur-xl bg-white/5 border border-white/10 rounded-[20px] p-6", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between mb-6", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-white font-medium", children: "Intelligence Modules" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-white/40 text-xs mt-1", children: "Select risk analysis components" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-white/40 text-sm", children: [
        Object.values(modules).filter(Boolean).length,
        "/6 enabled"
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "grid grid-cols-3 gap-4", children: moduleConfig.map(({ key, label, icon: Icon2, description, gradient }) => {
      const isActive = modules[key];
      return /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "div",
        {
          className: `
                relative cursor-pointer rounded-xl p-4 
                border transition-all duration-300
                ${isActive ? "bg-white/10 border-white/20" : "bg-white/5 border-white/10 opacity-60 hover:opacity-80"}
              `,
          onClick: () => onToggle(key),
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: `
                w-10 h-10 rounded-xl flex items-center justify-center mb-3
                ${isActive ? `bg-gradient-to-br ${gradient}` : "bg-white/10"}
              `, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Icon2, { className: `w-5 h-5 ${isActive ? "text-white" : "text-white/50"}` }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mb-3", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: `font-medium text-sm ${isActive ? "text-white" : "text-white/70"}`, children: label }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-white/40 text-xs mt-0.5", children: description })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: `
                w-10 h-5 rounded-full relative transition-colors duration-200
                ${isActive ? "bg-cyan-500" : "bg-white/20"}
              `, children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: `
                  absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform duration-200
                  ${isActive ? "translate-x-5" : "translate-x-0.5"}
                ` }) }),
            isActive && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "absolute top-2 right-2 w-2 h-2 bg-green-400 rounded-full animate-pulse" })
          ]
        },
        key
      );
    }) })
  ] });
}
function getValidationIssues(data) {
  const issues = [];
  if (data.trade.mode === "SEA" && (data.trade.polName?.toLowerCase().includes("airport") || data.trade.podName?.toLowerCase().includes("airport"))) {
    issues.push({
      id: "MODE_PORT_MISMATCH_SEA",
      severity: "critical",
      message: "Mode is SEA but ports are airports",
      detail: "POL/POD should be seaports, not airports",
      affectedFields: ["trade.mode", "trade.pol", "trade.pod"],
      action: "Fix Now"
    });
  }
  if (data.trade.mode === "AIR" && (data.trade.polName?.toLowerCase().includes("seaport") || data.trade.podName?.toLowerCase().includes("seaport"))) {
    issues.push({
      id: "MODE_PORT_MISMATCH_AIR",
      severity: "critical",
      message: "Mode is AIR but ports are seaports",
      detail: "POL/POD should be airports, not seaports",
      affectedFields: ["trade.mode", "trade.pol", "trade.pod"],
      action: "Fix Now"
    });
  }
  const etdDate = new Date(data.trade.etd);
  const today = /* @__PURE__ */ new Date();
  today.setHours(0, 0, 0, 0);
  if (etdDate < today) {
    issues.push({
      id: "ETD_IN_PAST",
      severity: "critical",
      message: "Departure date is in the past",
      detail: "ETD must be today or future date",
      affectedFields: ["trade.etd"],
      action: "Fix Now"
    });
  }
  const etaDate = new Date(data.trade.eta);
  if (etaDate <= etdDate) {
    issues.push({
      id: "ETA_BEFORE_ETD",
      severity: "critical",
      message: "Arrival before departure",
      detail: "ETA must be after ETD",
      affectedFields: ["trade.eta", "trade.etd"],
      action: "Fix Now"
    });
  }
  if (!data.cargo.hs_code && (data.cargo.gross_weight_kg > 0 || data.cargo.volume_cbm > 0)) {
    issues.push({
      id: "HS_CODE_REQUIRED",
      severity: "critical",
      message: "HS Code is required",
      detail: "Mandatory when weight/volume specified",
      affectedFields: ["cargo.hs_code"],
      action: "Fix Now"
    });
  }
  const hsChapter = data.cargo.hs_code ? parseInt(data.cargo.hs_code.split(".")[0]) : 0;
  if ((hsChapter === 28 || hsChapter === 29) && !data.cargo.is_dg) {
    issues.push({
      id: "HS_DG_ENFORCED",
      severity: "critical",
      message: "Dangerous goods flag required",
      detail: "HS Chapter 28/29 typically contains DG",
      affectedFields: ["cargo.hs_code", "cargo.is_dg"],
      action: "Fix Now"
    });
  }
  if (data.cargo.net_weight_kg && data.cargo.gross_weight_kg && data.cargo.net_weight_kg > data.cargo.gross_weight_kg) {
    issues.push({
      id: "WEIGHT_GREATER_THAN_NET",
      severity: "critical",
      message: "Net weight exceeds gross weight",
      detail: "Net weight must be ≤ Gross weight",
      affectedFields: ["cargo.gross_weight_kg", "cargo.net_weight_kg"],
      action: "Fix Now"
    });
  }
  if (!data.seller.email || !data.seller.phone) {
    issues.push({
      id: "SELLER_CONTACT_REQUIRED",
      severity: "critical",
      message: "Seller contact information incomplete",
      detail: "Email and phone are required",
      affectedFields: ["seller.email", "seller.phone"],
      action: "Fix Now"
    });
  }
  if (!data.buyer.email || !data.buyer.phone) {
    issues.push({
      id: "BUYER_CONTACT_REQUIRED",
      severity: "critical",
      message: "Buyer contact information incomplete",
      detail: "Email and phone are required",
      affectedFields: ["buyer.email", "buyer.phone"],
      action: "Fix Now"
    });
  }
  if (!data.trade.transit_time_days || data.trade.transit_time_days === 0) {
    issues.push({
      id: "TRANSIT_DAYS_MISSING",
      severity: "warning",
      message: "Transit time not specified",
      detail: "Please estimate transit duration",
      affectedFields: ["trade.transit_time_days"],
      action: "Review"
    });
  }
  if (data.trade.transit_time_days > 0) {
    if (data.trade.mode === "SEA" && (data.trade.transit_time_days < 3 || data.trade.transit_time_days > 90)) {
      issues.push({
        id: "TRANSIT_DAYS_OUTLIER",
        severity: "warning",
        message: "Transit time seems unusual",
        detail: "SEA: 3-90 days expected",
        affectedFields: ["trade.transit_time_days", "trade.mode"],
        action: "Review"
      });
    } else if (data.trade.mode === "AIR" && data.trade.transit_time_days >= 15) {
      issues.push({
        id: "TRANSIT_DAYS_OUTLIER",
        severity: "warning",
        message: "Transit time seems unusual",
        detail: "AIR: <15 days expected",
        affectedFields: ["trade.transit_time_days", "trade.mode"],
        action: "Review"
      });
    }
  }
  const incotermsNeedingLocation = ["FOB", "CIF", "CFR", "DAP", "DPU", "DDP"];
  if (incotermsNeedingLocation.includes(data.trade.incoterm) && !data.trade.incoterm_location) {
    issues.push({
      id: "INCOTERM_LOCATION_REQUIRED",
      severity: "warning",
      message: "Incoterm location missing",
      detail: `${data.trade.incoterm} requires location`,
      affectedFields: ["trade.incoterm", "trade.incoterm_location"],
      action: "Review"
    });
  }
  const perishableChapters = [2, 3, 7, 8];
  if (perishableChapters.includes(hsChapter) && !data.cargo.temp_control_required) {
    issues.push({
      id: "HS_REEFER_ENFORCED",
      severity: "warning",
      message: "Perishable cargo needs reefer",
      detail: "Container should be temperature controlled",
      affectedFields: ["cargo.hs_code", "cargo.temp_control_required"],
      action: "Review"
    });
  }
  if (data.cargo.cargo_type?.toLowerCase().includes("fragile") && data.cargo.stackability) {
    issues.push({
      id: "STACKABILITY_CHECK",
      severity: "warning",
      message: "Fragile items marked as stackable",
      detail: "Fragile cargo typically non-stackable",
      affectedFields: ["cargo.cargo_type", "cargo.stackability"],
      action: "Review"
    });
  }
  if (data.cargo.gross_weight_kg && data.cargo.volume_cbm) {
    const ratio = data.cargo.gross_weight_kg / data.cargo.volume_cbm;
    if (ratio < 50 || ratio > 1500) {
      issues.push({
        id: "WEIGHT_VOLUME_INCONSISTENT",
        severity: "warning",
        message: "Weight/volume ratio unusual",
        detail: `Expected 50-1500 kg/CBM, got ${ratio.toFixed(0)}`,
        affectedFields: ["cargo.gross_weight_kg", "cargo.volume_cbm"],
        action: "Review"
      });
    }
  }
  if (!data.cargo.packages || data.cargo.packages === 0) {
    issues.push({
      id: "PACKAGES_REQUIRED",
      severity: "warning",
      message: "Package count missing",
      detail: "Specify number of packages/pallets",
      affectedFields: ["cargo.packages"],
      action: "Review"
    });
  }
  if (data.trade.transit_time_days > 30) {
    issues.push({
      id: "RISK_MODULES_OFF_FOR_LONG_ROUTE",
      severity: "suggestion",
      message: "Long route, consider enabling modules",
      detail: "Route >30 days benefits from risk tracking",
      affectedFields: ["trade.transit_time_days"],
      action: "Enable"
    });
  }
  if (data.value > 1e5 || data.cargo.is_dg) {
    issues.push({
      id: "INSURANCE_ADVICE_HIGH_RISK",
      severity: "suggestion",
      message: "Consider enabling insurance module",
      detail: "Multiple risk factors detected",
      affectedFields: ["value", "cargo.is_dg"],
      action: "Enable"
    });
  }
  return issues;
}
function ActionFooter({ data, modules, onRunAnalysis, onSaveDraft, onBack, lastSaved, isAnalyzing }) {
  const issues = getValidationIssues(data);
  const criticalCount = issues.filter((i) => i.severity === "critical").length;
  const warningCount = issues.filter((i) => i.severity === "warning").length;
  const requiredFields = [
    { value: data.trade.pol, label: "POL" },
    { value: data.trade.pod, label: "POD" },
    { value: data.trade.mode, label: "Mode" },
    { value: data.trade.container_type, label: "Container" },
    { value: data.trade.etd, label: "ETD" },
    { value: data.trade.transit_time_days, label: "Transit Time" },
    { value: data.cargo.cargo_type, label: "Cargo Type" },
    { value: data.cargo.hs_code, label: "HS Code" },
    { value: data.cargo.packages, label: "Packages" },
    { value: data.cargo.gross_weight_kg, label: "Gross Weight" },
    { value: data.cargo.volume_cbm, label: "Volume" },
    { value: data.seller.company, label: "Seller Company" },
    { value: data.seller.email, label: "Seller Email" },
    { value: data.seller.phone, label: "Seller Phone" },
    { value: data.seller.country, label: "Seller Country" },
    { value: data.buyer.company, label: "Buyer Company" },
    { value: data.buyer.email, label: "Buyer Email" },
    { value: data.buyer.phone, label: "Buyer Phone" },
    { value: data.buyer.country, label: "Buyer Country" }
  ];
  const filledCount = requiredFields.filter((f) => f.value && f.value !== 0).length;
  const completeness = Math.round(filledCount / requiredFields.length * 100);
  const enabledModules = Object.values(modules).filter(Boolean).length;
  const canAnalyze = completeness >= 50;
  const getTimeSince = (date) => {
    const seconds = Math.floor(((/* @__PURE__ */ new Date()).getTime() - date.getTime()) / 1e3);
    if (seconds < 60) return "just now";
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ago`;
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "fixed bottom-0 left-0 right-0 z-40 backdrop-blur-xl bg-[#0a1628]/90 border-t border-white/10", children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "px-12 py-4", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-4", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-3", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-32 h-2 bg-white/10 rounded-full overflow-hidden", children: /* @__PURE__ */ jsxRuntimeExports.jsx(
          "div",
          {
            className: `h-full rounded-full transition-all ${completeness === 100 ? "bg-green-500" : completeness >= 80 ? "bg-cyan-500" : "bg-orange-500"}`,
            style: { width: `${completeness}%` }
          }
        ) }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "text-white/70 text-sm", children: [
          completeness,
          "% Complete"
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
        criticalCount > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-1.5 px-3 py-1.5 bg-red-500/20 border border-red-500/30 rounded-full", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(CircleAlert, { className: "w-3.5 h-3.5 text-red-400" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "text-red-300 text-xs font-medium", children: [
            criticalCount,
            " Critical"
          ] })
        ] }),
        warningCount > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-1.5 px-3 py-1.5 bg-orange-500/20 border border-orange-500/30 rounded-full", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(TriangleAlert, { className: "w-3.5 h-3.5 text-orange-400" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "text-orange-300 text-xs font-medium", children: [
            warningCount,
            " Warnings"
          ] })
        ] }),
        criticalCount === 0 && warningCount === 0 && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex items-center gap-1.5 px-3 py-1.5 bg-green-500/20 border border-green-500/30 rounded-full", children: /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-green-300 text-xs font-medium", children: "✓ All Clear" }) })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-white/40 text-sm flex items-center gap-1.5", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
          enabledModules,
          " modules"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/20", children: "•" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Clock, { className: "w-3.5 h-3.5" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
          "Saved ",
          getTimeSince(lastSaved)
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-3", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "button",
        {
          onClick: onBack,
          className: "px-4 py-2.5 border border-white/20 rounded-xl text-white/70 hover:text-white hover:border-white/40 transition-all flex items-center gap-2",
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(ArrowLeft, { className: "w-4 h-4" }),
            "Back"
          ]
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "button",
        {
          onClick: onSaveDraft,
          className: "px-4 py-2.5 border border-white/20 rounded-xl text-white/70 hover:text-white hover:border-white/40 transition-all flex items-center gap-2",
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Save, { className: "w-4 h-4" }),
            "Save Draft"
          ]
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "button",
        {
          onClick: onRunAnalysis,
          disabled: !canAnalyze || isAnalyzing,
          className: `
                px-6 py-2.5 rounded-xl font-medium flex items-center gap-2 transition-all
                ${canAnalyze && !isAnalyzing ? "bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg shadow-cyan-500/30 hover:shadow-cyan-500/50" : "bg-white/10 text-white/40 cursor-not-allowed"}
              `,
          children: isAnalyzing ? /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" }),
            "Analyzing..."
          ] }) : /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
            "Run Analysis",
            /* @__PURE__ */ jsxRuntimeExports.jsx(ChevronRight, { className: "w-4 h-4" })
          ] })
        }
      )
    ] })
  ] }) }) });
}
const PORTS_DATABASE = [
  // Vietnam Airports
  { code: "SGN", name: "Tan Son Nhat International Airport", city: "Ho Chi Minh City", country: "VN", countryName: "Vietnam", type: "airport" },
  { code: "HAN", name: "Noi Bai International Airport", city: "Hanoi", country: "VN", countryName: "Vietnam", type: "airport" },
  { code: "DAD", name: "Da Nang International Airport", city: "Da Nang", country: "VN", countryName: "Vietnam", type: "airport" },
  { code: "CXR", name: "Cam Ranh International Airport", city: "Nha Trang", country: "VN", countryName: "Vietnam", type: "airport" },
  { code: "PQC", name: "Phu Quoc International Airport", city: "Phu Quoc", country: "VN", countryName: "Vietnam", type: "airport" },
  // Vietnam Seaports
  { code: "VNSGN", name: "Saigon Port (Cat Lai)", city: "Ho Chi Minh City", country: "VN", countryName: "Vietnam", type: "seaport" },
  { code: "VNHPH", name: "Hai Phong Port", city: "Hai Phong", country: "VN", countryName: "Vietnam", type: "seaport" },
  { code: "VNCMP", name: "Cai Mep International Terminal", city: "Vung Tau", country: "VN", countryName: "Vietnam", type: "seaport" },
  { code: "VNDAD", name: "Da Nang Port (Tien Sa)", city: "Da Nang", country: "VN", countryName: "Vietnam", type: "seaport" },
  // China Airports
  { code: "PVG", name: "Shanghai Pudong International Airport", city: "Shanghai", country: "CN", countryName: "China", type: "airport" },
  { code: "SHA", name: "Shanghai Hongqiao Airport", city: "Shanghai", country: "CN", countryName: "China", type: "airport" },
  { code: "PEK", name: "Beijing Capital International Airport", city: "Beijing", country: "CN", countryName: "China", type: "airport" },
  { code: "CAN", name: "Guangzhou Baiyun Airport", city: "Guangzhou", country: "CN", countryName: "China", type: "airport" },
  { code: "SZX", name: "Shenzhen Bao'an Airport", city: "Shenzhen", country: "CN", countryName: "China", type: "airport" },
  // China Seaports
  { code: "CNSHA", name: "Port of Shanghai", city: "Shanghai", country: "CN", countryName: "China", type: "seaport" },
  { code: "CNNGB", name: "Ningbo-Zhoushan Port", city: "Ningbo", country: "CN", countryName: "China", type: "seaport" },
  { code: "CNSZX", name: "Shenzhen Port (Yantian)", city: "Shenzhen", country: "CN", countryName: "China", type: "seaport" },
  { code: "CNQIN", name: "Port of Qingdao", city: "Qingdao", country: "CN", countryName: "China", type: "seaport" },
  { code: "CNDLC", name: "Port of Dalian", city: "Dalian", country: "CN", countryName: "China", type: "seaport" },
  { code: "CNXMN", name: "Port of Xiamen", city: "Xiamen", country: "CN", countryName: "China", type: "seaport" },
  // USA Airports
  { code: "LAX", name: "Los Angeles International Airport", city: "Los Angeles", country: "US", countryName: "USA", type: "airport" },
  { code: "JFK", name: "John F. Kennedy International Airport", city: "New York", country: "US", countryName: "USA", type: "airport" },
  { code: "ORD", name: "O'Hare International Airport", city: "Chicago", country: "US", countryName: "USA", type: "airport" },
  { code: "SFO", name: "San Francisco International Airport", city: "San Francisco", country: "US", countryName: "USA", type: "airport" },
  { code: "MIA", name: "Miami International Airport", city: "Miami", country: "US", countryName: "USA", type: "airport" },
  { code: "SEA", name: "Seattle-Tacoma International Airport", city: "Seattle", country: "US", countryName: "USA", type: "airport" },
  { code: "DFW", name: "Dallas/Fort Worth International Airport", city: "Dallas", country: "US", countryName: "USA", type: "airport" },
  // USA Seaports
  { code: "USLAX", name: "Port of Los Angeles", city: "Los Angeles", country: "US", countryName: "USA", type: "seaport" },
  { code: "USLGB", name: "Port of Long Beach", city: "Long Beach", country: "US", countryName: "USA", type: "seaport" },
  { code: "USNYC", name: "Port of New York/New Jersey", city: "New York", country: "US", countryName: "USA", type: "seaport" },
  { code: "USOAK", name: "Port of Oakland", city: "Oakland", country: "US", countryName: "USA", type: "seaport" },
  { code: "USSEA", name: "Port of Seattle/Tacoma", city: "Seattle", country: "US", countryName: "USA", type: "seaport" },
  { code: "USSAV", name: "Port of Savannah", city: "Savannah", country: "US", countryName: "USA", type: "seaport" },
  { code: "USHOU", name: "Port of Houston", city: "Houston", country: "US", countryName: "USA", type: "seaport" },
  // Hong Kong
  { code: "HKG", name: "Hong Kong International Airport", city: "Hong Kong", country: "HK", countryName: "Hong Kong", type: "airport" },
  { code: "HKHKG", name: "Port of Hong Kong", city: "Hong Kong", country: "HK", countryName: "Hong Kong", type: "seaport" },
  // Singapore
  { code: "SIN", name: "Singapore Changi Airport", city: "Singapore", country: "SG", countryName: "Singapore", type: "airport" },
  { code: "SGSIN", name: "Port of Singapore", city: "Singapore", country: "SG", countryName: "Singapore", type: "seaport" },
  // Japan
  { code: "NRT", name: "Narita International Airport", city: "Tokyo", country: "JP", countryName: "Japan", type: "airport" },
  { code: "HND", name: "Tokyo Haneda Airport", city: "Tokyo", country: "JP", countryName: "Japan", type: "airport" },
  { code: "KIX", name: "Kansai International Airport", city: "Osaka", country: "JP", countryName: "Japan", type: "airport" },
  { code: "JPTYO", name: "Port of Tokyo", city: "Tokyo", country: "JP", countryName: "Japan", type: "seaport" },
  { code: "JPYOK", name: "Port of Yokohama", city: "Yokohama", country: "JP", countryName: "Japan", type: "seaport" },
  // South Korea
  { code: "ICN", name: "Incheon International Airport", city: "Seoul", country: "KR", countryName: "South Korea", type: "airport" },
  { code: "KRPUS", name: "Port of Busan", city: "Busan", country: "KR", countryName: "South Korea", type: "seaport" },
  { code: "KRICN", name: "Port of Incheon", city: "Incheon", country: "KR", countryName: "South Korea", type: "seaport" },
  // Thailand
  { code: "BKK", name: "Suvarnabhumi Airport", city: "Bangkok", country: "TH", countryName: "Thailand", type: "airport" },
  { code: "DMK", name: "Don Mueang Airport", city: "Bangkok", country: "TH", countryName: "Thailand", type: "airport" },
  { code: "THLCH", name: "Laem Chabang Port", city: "Chonburi", country: "TH", countryName: "Thailand", type: "seaport" },
  { code: "THBKK", name: "Bangkok Port", city: "Bangkok", country: "TH", countryName: "Thailand", type: "seaport" },
  // Europe
  { code: "LHR", name: "London Heathrow Airport", city: "London", country: "GB", countryName: "UK", type: "airport" },
  { code: "FRA", name: "Frankfurt Airport", city: "Frankfurt", country: "DE", countryName: "Germany", type: "airport" },
  { code: "AMS", name: "Amsterdam Schiphol Airport", city: "Amsterdam", country: "NL", countryName: "Netherlands", type: "airport" },
  { code: "CDG", name: "Paris Charles de Gaulle Airport", city: "Paris", country: "FR", countryName: "France", type: "airport" },
  { code: "NLRTM", name: "Port of Rotterdam", city: "Rotterdam", country: "NL", countryName: "Netherlands", type: "seaport" },
  { code: "DEHAM", name: "Port of Hamburg", city: "Hamburg", country: "DE", countryName: "Germany", type: "seaport" },
  { code: "BEANR", name: "Port of Antwerp", city: "Antwerp", country: "BE", countryName: "Belgium", type: "seaport" },
  { code: "GBFXT", name: "Port of Felixstowe", city: "Felixstowe", country: "GB", countryName: "UK", type: "seaport" },
  // UAE
  { code: "DXB", name: "Dubai International Airport", city: "Dubai", country: "AE", countryName: "UAE", type: "airport" },
  { code: "AEJEA", name: "Jebel Ali Port", city: "Dubai", country: "AE", countryName: "UAE", type: "seaport" },
  // Malaysia
  { code: "KUL", name: "Kuala Lumpur International Airport", city: "Kuala Lumpur", country: "MY", countryName: "Malaysia", type: "airport" },
  { code: "MYPKG", name: "Port Klang", city: "Klang", country: "MY", countryName: "Malaysia", type: "seaport" },
  // Taiwan
  { code: "TPE", name: "Taiwan Taoyuan International Airport", city: "Taipei", country: "TW", countryName: "Taiwan", type: "airport" },
  { code: "TWKHH", name: "Port of Kaohsiung", city: "Kaohsiung", country: "TW", countryName: "Taiwan", type: "seaport" }
];
const CARRIERS_DATABASE = [
  // Sea Carriers
  { code: "MAERSK", name: "Maersk Line", mode: "SEA", reliability: 85, icon: "🚢" },
  { code: "MSC", name: "Mediterranean Shipping Company", mode: "SEA", reliability: 82, icon: "🚢" },
  { code: "ONE", name: "Ocean Network Express", mode: "SEA", reliability: 78, icon: "🚢" },
  { code: "COSCO", name: "COSCO Shipping", mode: "SEA", reliability: 80, icon: "🚢" },
  { code: "HPL", name: "Hapag-Lloyd", mode: "SEA", reliability: 76, icon: "🚢" },
  { code: "EVERGREEN", name: "Evergreen Line", mode: "SEA", reliability: 79, icon: "🚢" },
  { code: "YANGMING", name: "Yang Ming Marine", mode: "SEA", reliability: 74, icon: "🚢" },
  { code: "HMM", name: "HMM (Hyundai)", mode: "SEA", reliability: 77, icon: "🚢" },
  { code: "CMA", name: "CMA CGM", mode: "SEA", reliability: 81, icon: "🚢" },
  { code: "ZIM", name: "ZIM Integrated Shipping", mode: "SEA", reliability: 72, icon: "🚢" },
  // Air Carriers
  { code: "VNA", name: "Vietnam Airlines Cargo", mode: "AIR", reliability: 89, icon: "✈️" },
  { code: "KE", name: "Korean Air Cargo", mode: "AIR", reliability: 93, icon: "✈️" },
  { code: "ANA", name: "All Nippon Airways Cargo", mode: "AIR", reliability: 95, icon: "✈️" },
  { code: "LH", name: "Lufthansa Cargo", mode: "AIR", reliability: 90, icon: "✈️" },
  { code: "CX", name: "Cathay Pacific Cargo", mode: "AIR", reliability: 88, icon: "✈️" },
  { code: "SQ", name: "Singapore Airlines Cargo", mode: "AIR", reliability: 91, icon: "✈️" },
  { code: "EK", name: "Emirates SkyCargo", mode: "AIR", reliability: 87, icon: "✈️" },
  { code: "TK", name: "Turkish Airlines Cargo", mode: "AIR", reliability: 84, icon: "✈️" },
  { code: "FX", name: "FedEx Express", mode: "AIR", reliability: 94, icon: "✈️" },
  { code: "UPS", name: "UPS Airlines", mode: "AIR", reliability: 92, icon: "✈️" },
  { code: "DHL", name: "DHL Express", mode: "AIR", reliability: 93, icon: "✈️" }
];
const CONTAINER_TYPES = {
  SEA: [
    { value: "20GP", label: "20' General Purpose", desc: "Standard 20ft dry container" },
    { value: "40GP", label: "40' General Purpose", desc: "Standard 40ft dry container" },
    { value: "40HC", label: "40' High Cube", desc: `Extra height (9'6")` },
    { value: "20RF", label: "20' Reefer", desc: "Temperature controlled" },
    { value: "40RF", label: "40' Reefer", desc: "Temperature controlled" },
    { value: "20OT", label: "20' Open Top", desc: "For oversized cargo" },
    { value: "40OT", label: "40' Open Top", desc: "For oversized cargo" },
    { value: "20FR", label: "20' Flat Rack", desc: "For heavy/odd shapes" },
    { value: "40FR", label: "40' Flat Rack", desc: "For heavy/odd shapes" },
    { value: "LCL", label: "LCL (Less than Container)", desc: "Shared container space" },
    { value: "FCL", label: "FCL (Full Container)", desc: "Full container load" }
  ],
  AIR: [
    { value: "ULD-AKE", label: "ULD-AKE (LD3)", desc: "Standard narrow-body" },
    { value: "ULD-AKH", label: "ULD-AKH (LD3-45)", desc: "Contour container" },
    { value: "ULD-AQY", label: "ULD-AQY (LD7)", desc: "Wide-body main deck" },
    { value: "ULD-PMC", label: "ULD-PMC (P6P)", desc: "96x125 pallet" },
    { value: "ULD-PGF", label: "ULD-PGF (P1P)", desc: "88x125 pallet" },
    { value: "LOOSE", label: "Loose Cargo", desc: "Non-containerized" }
  ],
  ROAD: [
    { value: "FTL", label: "FTL (Full Truck Load)", desc: "Dedicated truck" },
    { value: "LTL", label: "LTL (Less Than Truck)", desc: "Shared truck space" },
    { value: "FLATBED", label: "Flatbed Trailer", desc: "For oversized cargo" },
    { value: "REEFER", label: "Reefer Truck", desc: "Temperature controlled" }
  ],
  RAIL: [
    { value: "FCL", label: "FCL Rail Container", desc: "Full container by rail" },
    { value: "LCL", label: "LCL Rail Container", desc: "Shared container by rail" },
    { value: "BOXCAR", label: "Boxcar", desc: "Rail boxcar" }
  ]
};
const CARGO_TYPES = [
  { value: "electronics", label: "Electronics & Technology", icon: "💻", desc: "Phones, computers, components" },
  { value: "textiles", label: "Textiles & Apparel", icon: "👕", desc: "Clothing, fabrics, footwear" },
  { value: "machinery", label: "Machinery & Equipment", icon: "⚙️", desc: "Industrial machines, parts" },
  { value: "food", label: "Food & Beverages", icon: "🍎", desc: "Perishable goods, drinks" },
  { value: "chemicals", label: "Chemicals", icon: "🧪", desc: "Industrial chemicals, paints" },
  { value: "automotive", label: "Automotive Parts", icon: "🚗", desc: "Car parts, accessories" },
  { value: "furniture", label: "Furniture & Home", icon: "🪑", desc: "Home goods, decor" },
  { value: "pharmaceuticals", label: "Pharmaceuticals", icon: "💊", desc: "Medicine, medical supplies" },
  { value: "raw_materials", label: "Raw Materials", icon: "🪨", desc: "Metals, minerals, wood" },
  { value: "consumer_goods", label: "Consumer Goods", icon: "📦", desc: "General retail products" },
  { value: "perishables", label: "Perishables", icon: "❄️", desc: "Requires cold chain" },
  { value: "hazmat", label: "Hazardous Materials", icon: "☣️", desc: "DG class goods" }
];
const INCOTERMS = [
  { value: "EXW", label: "EXW - Ex Works", desc: "Seller makes goods available at their premises", risk: "Seller: Minimal | Buyer: Maximum" },
  { value: "FCA", label: "FCA - Free Carrier", desc: "Seller delivers to carrier nominated by buyer", risk: "Seller: Low | Buyer: High" },
  { value: "FAS", label: "FAS - Free Alongside Ship", desc: "Seller delivers alongside vessel at port", risk: "Seller: Medium-Low | Buyer: Medium-High" },
  { value: "FOB", label: "FOB - Free On Board", desc: "Seller loads goods on vessel nominated by buyer", risk: "Seller: Medium | Buyer: Medium" },
  { value: "CFR", label: "CFR - Cost and Freight", desc: "Seller pays freight to destination port", risk: "Seller: Medium-High | Buyer: Medium-Low" },
  { value: "CIF", label: "CIF - Cost, Insurance, Freight", desc: "Seller pays freight and insurance", risk: "Seller: High | Buyer: Low" },
  { value: "CPT", label: "CPT - Carriage Paid To", desc: "Seller pays carriage to named place", risk: "Seller: High | Buyer: Low" },
  { value: "CIP", label: "CIP - Carriage and Insurance Paid", desc: "Seller pays carriage and insurance", risk: "Seller: High | Buyer: Low" },
  { value: "DAP", label: "DAP - Delivered at Place", desc: "Seller delivers goods ready for unloading", risk: "Seller: Very High | Buyer: Very Low" },
  { value: "DPU", label: "DPU - Delivered at Place Unloaded", desc: "Seller delivers and unloads goods", risk: "Seller: Very High | Buyer: Very Low" },
  { value: "DDP", label: "DDP - Delivered Duty Paid", desc: "Seller delivers goods cleared for import", risk: "Seller: Maximum | Buyer: Minimal" }
];
const TRANSPORT_MODES = [
  { value: "AIR", label: "Air Freight", icon: /* @__PURE__ */ jsxRuntimeExports.jsx(Plane, { className: "w-5 h-5" }), desc: "Fast delivery, higher cost", color: "from-sky-400 to-blue-500" },
  { value: "SEA", label: "Sea Freight", icon: /* @__PURE__ */ jsxRuntimeExports.jsx(Ship, { className: "w-5 h-5" }), desc: "Cost-effective for large volumes", color: "from-cyan-400 to-teal-500" },
  { value: "ROAD", label: "Road Transport", icon: /* @__PURE__ */ jsxRuntimeExports.jsx(Truck, { className: "w-5 h-5" }), desc: "Flexible door-to-door delivery", color: "from-amber-400 to-orange-500" },
  { value: "RAIL", label: "Rail Freight", icon: /* @__PURE__ */ jsxRuntimeExports.jsx(TramFront, { className: "w-5 h-5" }), desc: "Efficient for long distances", color: "from-purple-400 to-indigo-500" },
  { value: "MULTIMODAL", label: "Multimodal", icon: /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-lg", children: "🔄" }), desc: "Combined transport modes", color: "from-pink-400 to-rose-500" }
];
function SmartInlineEditor({
  isOpen,
  field,
  label,
  value,
  type,
  options,
  position,
  transportMode = "SEA",
  onSave,
  onClose
}) {
  const [localValue, setLocalValue] = reactExports.useState(String(value ?? ""));
  const [error, setError] = reactExports.useState(null);
  const [isValid, setIsValid] = reactExports.useState(false);
  const [suggestions, setSuggestions] = reactExports.useState([]);
  const [showSuggestions, setShowSuggestions] = reactExports.useState(false);
  const [recentPorts, setRecentPorts] = reactExports.useState([]);
  const [selectedIndex, setSelectedIndex] = reactExports.useState(-1);
  const inputRef = reactExports.useRef(null);
  const containerRef = reactExports.useRef(null);
  reactExports.useEffect(() => {
    try {
      const saved = localStorage.getItem("recent_ports");
      if (saved) {
        const codes = JSON.parse(saved);
        const recent = codes.map((code) => PORTS_DATABASE.find((p) => p.code === code)).filter(Boolean);
        setRecentPorts(recent.slice(0, 5));
      }
    } catch (e) {
      console.warn("Failed to load recent ports:", e);
    }
  }, []);
  const saveToRecent = reactExports.useCallback((code) => {
    try {
      const saved = localStorage.getItem("recent_ports");
      const codes = saved ? JSON.parse(saved) : [];
      const updated = [code, ...codes.filter((c) => c !== code)].slice(0, 10);
      localStorage.setItem("recent_ports", JSON.stringify(updated));
    } catch (e) {
      console.warn("Failed to save recent port:", e);
    }
  }, []);
  reactExports.useEffect(() => {
    setLocalValue(String(value ?? ""));
    setError(null);
    validateValue(String(value ?? ""));
  }, [value, field]);
  reactExports.useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
      if (type === "port") {
        const currentValue = String(value ?? "");
        if (currentValue) {
          const q = currentValue.toLowerCase();
          const results = PORTS_DATABASE.filter(
            (p) => p.code.toLowerCase().includes(q) || p.name.toLowerCase().includes(q) || p.city.toLowerCase().includes(q) || p.country.toLowerCase().includes(q) || p.countryName.toLowerCase().includes(q)
          ).slice(0, 10);
          setSuggestions(results);
          setShowSuggestions(results.length > 0);
        } else {
          setShowSuggestions(false);
        }
      }
    }
  }, [isOpen, type, value]);
  reactExports.useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        onClose();
      }
    };
    const handleEscape = (e) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("keydown", handleEscape);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [isOpen, onClose]);
  const validateValue = reactExports.useCallback((val) => {
    if (type === "port") {
      const found = PORTS_DATABASE.find(
        (p) => p.code.toLowerCase() === val.toLowerCase() || p.name.toLowerCase().includes(val.toLowerCase()) || val.toLowerCase().includes(p.code.toLowerCase())
      );
      setIsValid(!!found || val.length >= 2);
      return !!found || val.length >= 2;
    }
    if (type === "number") {
      const num = Number(val);
      setIsValid(!isNaN(num) && num >= 0);
      return !isNaN(num) && num >= 0;
    }
    if (type === "date") {
      const date = new Date(val);
      setIsValid(!isNaN(date.getTime()));
      return !isNaN(date.getTime());
    }
    setIsValid(val.length > 0);
    return val.length > 0;
  }, [type]);
  const searchPorts = reactExports.useCallback((query) => {
    if (!query.trim()) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    const q = query.toLowerCase();
    const results = PORTS_DATABASE.filter(
      (p) => p.code.toLowerCase().includes(q) || p.name.toLowerCase().includes(q) || p.city.toLowerCase().includes(q) || p.country.toLowerCase().includes(q) || p.countryName.toLowerCase().includes(q)
    ).slice(0, 10);
    setSuggestions(results);
    setShowSuggestions(results.length > 0);
    setSelectedIndex(-1);
  }, []);
  const handleInputChange = (e) => {
    const val = e.target.value;
    setLocalValue(val);
    validateValue(val);
    if (type === "port") {
      searchPorts(val);
    }
  };
  const handleSelectSuggestion = (port) => {
    const displayValue = `${port.code} - ${port.name}`;
    setLocalValue(displayValue);
    setIsValid(true);
    setShowSuggestions(false);
    saveToRecent(port.code);
  };
  const handleKeyDown = (e) => {
    if (type === "port" && showSuggestions) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((prev) => Math.min(prev + 1, suggestions.length - 1));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((prev) => Math.max(prev - 1, 0));
      } else if (e.key === "Enter" && selectedIndex >= 0 && suggestions[selectedIndex]) {
        e.preventDefault();
        handleSelectSuggestion(suggestions[selectedIndex]);
        return;
      }
    }
    if (e.key === "Enter" && type !== "textarea") {
      e.preventDefault();
      handleSave();
    }
  };
  const handleSave = () => {
    if (!validateValue(localValue)) {
      setError("Please enter a valid value");
      return;
    }
    let saveValue = localValue;
    if (type === "port") {
      const match = localValue.match(/^([A-Z0-9]+)/i);
      if (match && match[1]) {
        saveValue = match[1].toUpperCase();
      }
    } else if (type === "number") {
      saveValue = Number(localValue);
    }
    onSave(saveValue);
    onClose();
  };
  if (!isOpen) return null;
  const adjustedPosition = {
    x: Math.min(Math.max(position.x, 20), window.innerWidth - 440),
    y: Math.min(Math.max(position.y, 20), window.innerHeight - 500)
  };
  const POPULAR_PORTS = PORTS_DATABASE.filter(
    (p) => ["SGN", "HAN", "VNSGN", "VNCMP", "LAX", "JFK", "USLAX", "CNSHA", "HKG", "SIN", "SGSIN", "NRT", "ICN", "BKK", "THLCH"].includes(p.code)
  );
  const renderPortEditor = () => {
    const displayPorts = showSuggestions && suggestions.length > 0 ? suggestions : recentPorts.length > 0 ? [] : POPULAR_PORTS.slice(0, 8);
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-4", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "relative", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "absolute left-3 top-1/2 -translate-y-1/2 text-cyan-400", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Search, { className: "w-4 h-4" }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            ref: inputRef,
            type: "text",
            value: localValue,
            onChange: handleInputChange,
            onKeyDown: handleKeyDown,
            placeholder: "Search port code, city or country...",
            className: "w-full bg-[#0a1628] border border-cyan-500/30 rounded-xl pl-10 pr-4 py-3.5 text-white placeholder-white/40 focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20 transition-all font-medium"
          }
        ),
        isValid && localValue && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1.5 text-emerald-400", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Check, { className: "w-4 h-4" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-sm font-medium", children: "Valid" })
        ] })
      ] }),
      recentPorts.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 text-amber-400/70 text-xs font-medium mb-2 px-1", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Clock, { className: "w-3.5 h-3.5" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Recent Ports:" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "space-y-1.5 max-h-40 overflow-y-auto custom-scrollbar", children: recentPorts.map((port) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "div",
          {
            onClick: () => handleSelectSuggestion(port),
            className: "flex items-center gap-3 px-3 py-2.5 rounded-xl bg-amber-500/5 hover:bg-gradient-to-r hover:from-amber-500/10 hover:to-orange-500/10 border border-amber-500/20 hover:border-amber-400/40 cursor-pointer transition-all group",
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "px-2 py-0.5 bg-amber-500/20 text-amber-300 text-xs font-bold rounded uppercase tracking-wide", children: port.country }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex-1 min-w-0", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white font-semibold", children: port.code }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/30", children: "-" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/70 truncate", children: port.city })
              ] }) }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/40 text-xs", children: port.type === "airport" ? "✈️" : "🚢" })
            ]
          },
          `recent-${port.code}`
        )) })
      ] }),
      (showSuggestions ? suggestions.length > 0 : displayPorts.length > 0) && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2 text-cyan-400/70 text-xs font-medium mb-2 px-1", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(MapPin, { className: "w-3.5 h-3.5" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: showSuggestions ? "Search Results:" : "Popular Ports:" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "space-y-1.5 max-h-48 overflow-y-auto custom-scrollbar", children: (showSuggestions ? suggestions : displayPorts).map((port, index) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "div",
          {
            onClick: () => handleSelectSuggestion(port),
            className: `
                    flex items-center gap-3 px-3 py-2.5 rounded-xl cursor-pointer transition-all
                    ${index === selectedIndex && showSuggestions ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-400/50 shadow-lg shadow-cyan-500/10" : "bg-white/5 hover:bg-white/10 border border-transparent hover:border-cyan-500/30"}
                  `,
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: `
                    px-2 py-0.5 text-xs font-bold rounded uppercase tracking-wide
                    ${index === selectedIndex && showSuggestions ? "bg-cyan-400 text-slate-900" : "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300"}
                  `, children: port.country }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex-1 min-w-0", children: [
                /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white font-semibold", children: port.code }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/30", children: "-" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/70 truncate", children: port.city })
                ] }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-white/40 text-xs truncate", children: port.name })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white/40 text-sm", children: port.type === "airport" ? "✈️" : "🚢" })
            ]
          },
          `port-${port.code}`
        )) })
      ] }),
      !showSuggestions && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "pt-2 border-t border-white/10", children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "button",
        {
          type: "button",
          onClick: () => {
            setSuggestions(PORTS_DATABASE.slice(0, 20));
            setShowSuggestions(true);
          },
          className: "w-full text-center text-cyan-400/70 hover:text-cyan-300 text-sm py-2 rounded-lg hover:bg-white/5 transition-colors",
          children: [
            "Browse all ",
            PORTS_DATABASE.length,
            " ports →"
          ]
        }
      ) })
    ] });
  };
  const renderCarrierEditor = () => {
    const currentMode = transportMode?.toUpperCase() || "SEA";
    const filteredCarriers = CARRIERS_DATABASE.filter(
      (c) => c.mode === currentMode || currentMode === "MULTIMODAL"
    );
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-4", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "input",
        {
          ref: inputRef,
          type: "text",
          value: localValue,
          onChange: handleInputChange,
          onKeyDown: handleKeyDown,
          placeholder: "Search carrier...",
          className: "w-full bg-[#0a1628] border border-white/20 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-cyan-500"
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "space-y-1.5 max-h-64 overflow-y-auto custom-scrollbar", children: filteredCarriers.map((carrier) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "div",
        {
          onClick: () => {
            setLocalValue(carrier.name);
            setIsValid(true);
          },
          className: `
                flex items-center gap-3 px-3 py-3 rounded-xl cursor-pointer transition-all
                ${localValue === carrier.name ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-400/50" : "bg-white/5 hover:bg-white/10 border border-transparent"}
              `,
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-2xl", children: carrier.icon }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex-1", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-white font-medium", children: carrier.name }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-white/50 text-xs", children: [
                "Reliability: ",
                carrier.reliability,
                "%"
              ] })
            ] }),
            localValue === carrier.name && /* @__PURE__ */ jsxRuntimeExports.jsx(Check, { className: "w-5 h-5 text-cyan-400" })
          ]
        },
        carrier.code
      )) })
    ] });
  };
  const renderContainerEditor = () => {
    const currentMode = transportMode?.toUpperCase() || "SEA";
    const containers = CONTAINER_TYPES[currentMode] || CONTAINER_TYPES.SEA;
    return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "space-y-1.5 max-h-72 overflow-y-auto custom-scrollbar", children: containers.map((container) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "div",
      {
        onClick: () => {
          setLocalValue(container.value);
          setIsValid(true);
        },
        className: `
              px-3 py-3 rounded-xl cursor-pointer transition-all
              ${localValue === container.value ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-400/50" : "bg-white/5 hover:bg-white/10 border border-transparent"}
            `,
        children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white font-medium", children: container.label }),
            localValue === container.value && /* @__PURE__ */ jsxRuntimeExports.jsx(Check, { className: "w-5 h-5 text-cyan-400" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-white/50 text-xs mt-1", children: container.desc })
        ]
      },
      container.value
    )) });
  };
  const renderCargoTypeEditor = () => /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "space-y-1.5 max-h-72 overflow-y-auto custom-scrollbar", children: CARGO_TYPES.map((cargo) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      onClick: () => {
        setLocalValue(cargo.value);
        setIsValid(true);
      },
      className: `
            flex items-center gap-3 px-3 py-3 rounded-xl cursor-pointer transition-all
            ${localValue === cargo.value ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-400/50" : "bg-white/5 hover:bg-white/10 border border-transparent"}
          `,
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-2xl w-10 text-center", children: cargo.icon }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex-1", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-white font-medium", children: cargo.label }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-white/50 text-xs", children: cargo.desc })
        ] }),
        localValue === cargo.value && /* @__PURE__ */ jsxRuntimeExports.jsx(Check, { className: "w-5 h-5 text-cyan-400" })
      ]
    },
    cargo.value
  )) });
  const renderIncotermEditor = () => /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "space-y-1.5 max-h-72 overflow-y-auto custom-scrollbar", children: INCOTERMS.map((term) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      onClick: () => {
        setLocalValue(term.value);
        setIsValid(true);
      },
      className: `
            px-3 py-3 rounded-xl cursor-pointer transition-all
            ${localValue === term.value ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-400/50" : "bg-white/5 hover:bg-white/10 border border-transparent"}
          `,
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between mb-1", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white font-medium", children: term.label }),
          localValue === term.value && /* @__PURE__ */ jsxRuntimeExports.jsx(Check, { className: "w-5 h-5 text-cyan-400" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-white/50 text-xs", children: term.desc }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-amber-400/60 text-xs mt-1", children: term.risk })
      ]
    },
    term.value
  )) });
  const renderModeEditor = () => /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "space-y-2", children: TRANSPORT_MODES.map((mode) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      onClick: () => {
        setLocalValue(mode.value);
        setIsValid(true);
      },
      className: `
            flex items-center gap-4 px-4 py-4 rounded-xl cursor-pointer transition-all
            ${localValue === mode.value ? `bg-gradient-to-r ${mode.color} bg-opacity-20 border border-white/20 shadow-lg` : "bg-white/5 hover:bg-white/10 border border-transparent"}
          `,
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: `
            w-12 h-12 rounded-xl flex items-center justify-center text-white
            ${localValue === mode.value ? `bg-gradient-to-r ${mode.color}` : "bg-white/10"}
          `, children: mode.icon }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex-1", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-white font-semibold", children: mode.label }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-white/50 text-sm", children: mode.desc })
        ] }),
        localValue === mode.value && /* @__PURE__ */ jsxRuntimeExports.jsx(Check, { className: "w-6 h-6 text-white" })
      ]
    },
    mode.value
  )) });
  const renderDefaultEditor = () => {
    if (type === "select" && options) {
      return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "space-y-1.5 max-h-64 overflow-y-auto custom-scrollbar", children: options.map((opt) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "div",
        {
          onClick: () => {
            setLocalValue(opt.value);
            setIsValid(true);
          },
          className: `
                flex items-center justify-between px-3 py-3 rounded-xl cursor-pointer transition-all
                ${localValue === opt.value ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-400/50" : "bg-white/5 hover:bg-white/10 border border-transparent"}
              `,
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white font-medium", children: opt.label }),
            localValue === opt.value && /* @__PURE__ */ jsxRuntimeExports.jsx(Check, { className: "w-5 h-5 text-cyan-400" })
          ]
        },
        opt.value
      )) });
    }
    if (type === "checkbox") {
      const isChecked = localValue === "true" || localValue === "1";
      return /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: "flex items-center gap-4 cursor-pointer p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-colors", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            type: "checkbox",
            checked: isChecked,
            onChange: (e) => setLocalValue(String(e.target.checked)),
            className: "w-6 h-6 rounded border-white/20 bg-[#0a1628] text-cyan-500 focus:ring-cyan-500 focus:ring-offset-0"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white font-medium", children: isChecked ? "Yes - Enabled" : "No - Disabled" })
      ] });
    }
    if (type === "textarea") {
      return /* @__PURE__ */ jsxRuntimeExports.jsx(
        "textarea",
        {
          value: localValue,
          onChange: (e) => {
            setLocalValue(e.target.value);
            validateValue(e.target.value);
          },
          rows: 4,
          className: "w-full bg-[#0a1628] border border-white/20 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-cyan-500 resize-none"
        }
      );
    }
    if (type === "date") {
      return /* @__PURE__ */ jsxRuntimeExports.jsx(
        "input",
        {
          ref: inputRef,
          type: "date",
          value: localValue,
          onChange: (e) => {
            setLocalValue(e.target.value);
            validateValue(e.target.value);
          },
          onKeyDown: handleKeyDown,
          className: "w-full bg-[#0a1628] border border-white/20 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-cyan-500"
        }
      );
    }
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "relative", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "input",
        {
          ref: inputRef,
          type: type === "number" ? "number" : "text",
          value: localValue,
          onChange: handleInputChange,
          onKeyDown: handleKeyDown,
          className: "w-full bg-[#0a1628] border border-white/20 rounded-xl px-4 py-3.5 text-white focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
        }
      ),
      isValid && localValue && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1.5 text-emerald-400", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Check, { className: "w-4 h-4" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-sm font-medium", children: "Valid" })
      ] })
    ] });
  };
  const renderEditor = () => {
    switch (type) {
      case "port":
        return renderPortEditor();
      case "cargo_type":
        return renderCargoTypeEditor();
      case "incoterm":
        return renderIncotermEditor();
      case "mode":
        return renderModeEditor();
      case "carrier":
        return renderCarrierEditor();
      case "container":
        return renderContainerEditor();
      default:
        return renderDefaultEditor();
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      ref: containerRef,
      className: "fixed z-[100] w-[420px] backdrop-blur-2xl bg-gradient-to-br from-[#0d1f35]/98 to-[#0a1628]/98 border border-white/20 rounded-2xl shadow-2xl shadow-black/50 overflow-hidden",
      style: {
        left: adjustedPosition.x,
        top: adjustedPosition.y
      },
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between px-5 py-4 border-b border-white/10 bg-gradient-to-r from-white/5 to-transparent", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-3", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-pink-500 flex items-center justify-center shadow-lg shadow-orange-500/30", children: /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-white text-lg", children: "✏️" }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-white font-semibold text-lg", children: [
                "Edit: ",
                label
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-white/40 text-xs font-mono", children: field })
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              onClick: onClose,
              className: "p-2.5 hover:bg-white/10 rounded-xl transition-colors",
              children: /* @__PURE__ */ jsxRuntimeExports.jsx(X, { className: "w-5 h-5 text-white/50 hover:text-white" })
            }
          )
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "p-5 max-h-[60vh] overflow-y-auto custom-scrollbar", children: [
          renderEditor(),
          error && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mt-3 flex items-center gap-2 text-red-400 text-sm bg-red-500/10 px-3 py-2 rounded-lg", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(CircleAlert, { className: "w-4 h-4" }),
            error
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-end gap-3 px-5 py-4 border-t border-white/10 bg-white/5", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              onClick: onClose,
              className: "px-6 py-2.5 text-white/70 hover:text-white hover:bg-white/10 rounded-xl font-medium transition-all",
              children: "Cancel"
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "button",
            {
              onClick: handleSave,
              disabled: !isValid,
              className: `
            px-6 py-2.5 rounded-xl font-semibold flex items-center gap-2 transition-all
            ${isValid ? "bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg shadow-cyan-500/30 hover:shadow-cyan-500/50" : "bg-white/10 text-white/40 cursor-not-allowed"}
          `,
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx(Check, { className: "w-4 h-4" }),
                "Save"
              ]
            }
          )
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("style", { children: `
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.2);
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.3);
        }
      ` })
      ]
    }
  );
}
const FIELD_CONFIG = {
  "trade.pol": { type: "port", label: "Port of Loading" },
  "trade.pod": { type: "port", label: "Port of Discharge" },
  "trade.mode": { type: "mode", label: "Transport Mode" },
  "trade.container_type": { type: "container", label: "Container Type" },
  "trade.etd": { type: "date", label: "ETD" },
  "trade.eta": { type: "date", label: "ETA" },
  "trade.transit_time_days": { type: "number", label: "Transit Days" },
  "trade.incoterm": { type: "incoterm", label: "Incoterm" },
  "trade.incoterm_location": { type: "text", label: "Incoterm Location" },
  "trade.carrier": { type: "carrier", label: "Carrier" },
  "trade.priority": { type: "select", label: "Priority", options: [
    { value: "low", label: "Low" },
    { value: "normal", label: "Normal" },
    { value: "high", label: "High" },
    { value: "urgent", label: "Urgent" }
  ] },
  "cargo.cargo_type": { type: "cargo_type", label: "Cargo Type" },
  "cargo.cargo_category": { type: "text", label: "Cargo Category" },
  "cargo.hs_code": { type: "text", label: "HS Code" },
  "cargo.packages": { type: "number", label: "Packages" },
  "cargo.gross_weight_kg": { type: "number", label: "Gross Weight (kg)" },
  "cargo.net_weight_kg": { type: "number", label: "Net Weight (kg)" },
  "cargo.volume_cbm": { type: "number", label: "Volume (CBM)" },
  "cargo.packing_type": { type: "text", label: "Packing Type" },
  "cargo.stackability": { type: "checkbox", label: "Stackable" },
  "cargo.temp_control_required": { type: "checkbox", label: "Temperature Controlled" },
  "cargo.is_dg": { type: "checkbox", label: "Dangerous Goods" },
  "seller.company": { type: "text", label: "Company" },
  "seller.name": { type: "text", label: "Contact Name" },
  "seller.email": { type: "text", label: "Email" },
  "seller.phone": { type: "text", label: "Phone" },
  "seller.country": { type: "text", label: "Country" },
  "seller.city": { type: "text", label: "City" },
  "seller.address": { type: "textarea", label: "Address" },
  "seller.tax_id": { type: "text", label: "Tax ID" },
  "buyer.company": { type: "text", label: "Company" },
  "buyer.name": { type: "text", label: "Contact Name" },
  "buyer.email": { type: "text", label: "Email" },
  "buyer.phone": { type: "text", label: "Phone" },
  "buyer.country": { type: "text", label: "Country" },
  "buyer.city": { type: "text", label: "City" },
  "buyer.address": { type: "textarea", label: "Address" },
  "buyer.tax_id": { type: "text", label: "Tax ID" },
  "value": { type: "number", label: "Shipment Value (USD)" }
};
function getNestedValue(obj, path) {
  return path.split(".").reduce((acc, part) => acc?.[part], obj);
}
function setNestedValue(obj, path, value) {
  const parts = path.split(".");
  const last = parts.pop();
  const target = parts.reduce((acc, part) => {
    if (!acc[part]) {
      acc[part] = {};
    }
    return acc[part];
  }, obj);
  target[last] = value;
}
function RiskcastSummary({ initialData }) {
  const defaultData = {
    shipmentId: "SH-SGN-LAX-" + Date.now().toString().slice(-10),
    trade: {
      pol: "SGN",
      polName: "Tan Son Nhat International Airport",
      polCity: "Ho Chi Minh City",
      polCountry: "Vietnam",
      pod: "LAX",
      podName: "Los Angeles International Airport",
      podCity: "Los Angeles",
      podCountry: "United States",
      mode: "AIR",
      service_route: "SGN-LAX Direct",
      carrier: "Cathay Pacific",
      container_type: "Air Cargo Unit",
      etd: new Date(Date.now() + 7 * 24 * 60 * 60 * 1e3).toISOString().split("T")[0],
      eta: new Date(Date.now() + 10 * 24 * 60 * 60 * 1e3).toISOString().split("T")[0],
      transit_time_days: 3,
      incoterm: "CIF",
      incoterm_location: "Los Angeles",
      priority: "normal"
    },
    cargo: {
      cargo_type: "Electronics",
      cargo_category: "General",
      hs_code: "8471.30",
      hs_chapter: "84",
      packing_type: "Pallets",
      packages: 24,
      gross_weight_kg: 1200,
      net_weight_kg: 1100,
      volume_cbm: 8.5,
      stackability: false,
      temp_control_required: false,
      is_dg: false
    },
    seller: {
      name: "John Nguyen",
      company: "Vietnam Export Co.",
      email: "john@vnexport.com",
      phone: "+84 28 3824 5678",
      country: "Vietnam",
      city: "Ho Chi Minh City",
      address: "123 Le Loi Street",
      tax_id: "VN123456789"
    },
    buyer: {
      name: "Mike Johnson",
      company: "US Import LLC",
      email: "mike@usimport.com",
      phone: "+1 213 555 1234",
      country: "United States",
      city: "Los Angeles",
      address: "456 Commerce Ave",
      tax_id: "US987654321"
    },
    value: 125e3
  };
  const [data, setData] = reactExports.useState(initialData ?? defaultData);
  const [modules, setModules] = reactExports.useState({
    esg: true,
    weather: true,
    portCongestion: true,
    carrierPerformance: true,
    marketScanner: false,
    insurance: true
  });
  const [saveState, setSaveState] = reactExports.useState("saved");
  const [lastSaved, setLastSaved] = reactExports.useState(/* @__PURE__ */ new Date());
  const [isAnalyzing, setIsAnalyzing] = reactExports.useState(false);
  const [editor, setEditor] = reactExports.useState({
    isOpen: false,
    field: "",
    value: null,
    position: { x: 0, y: 0 }
  });
  const transformInputStateToSummary = (state) => {
    const transport = state.transport || {};
    const cargo = state.cargo || {};
    const seller = state.seller || {};
    const buyer = state.buyer || {};
    const pol = String(transport.pol || "SGN");
    const pod = String(transport.pod || "LAX");
    const portInfo = {
      "SGN": { name: "Tan Son Nhat International Airport", city: "Ho Chi Minh City", country: "Vietnam" },
      "VNSGN": { name: "Tan Son Nhat International Airport", city: "Ho Chi Minh City", country: "Vietnam" },
      "LAX": { name: "Los Angeles International Airport", city: "Los Angeles", country: "United States" },
      "USLAX": { name: "Los Angeles International Airport", city: "Los Angeles", country: "United States" },
      "SHA": { name: "Shanghai Pudong International Airport", city: "Shanghai", country: "China" },
      "HKG": { name: "Hong Kong International Airport", city: "Hong Kong", country: "Hong Kong" },
      "SIN": { name: "Changi Airport", city: "Singapore", country: "Singapore" }
    };
    const polInfo = portInfo[pol.toUpperCase()] || { name: pol, city: pol, country: "Unknown" };
    const podInfo = portInfo[pod.toUpperCase()] || { name: pod, city: pod, country: "Unknown" };
    const shipmentValue = Number(cargo.insuranceValue) || Number(cargo.value) || Number(cargo.cargo_value) || Number(state.value) || 0;
    const getCountryName = (country) => {
      if (typeof country === "string") return country;
      if (country && typeof country === "object" && "name" in country) return String(country.name);
      return "";
    };
    return {
      shipmentId: String(state.shipmentId || `SH-${pol}-${pod}-${Date.now().toString().slice(-10)}`),
      trade: {
        pol,
        polName: polInfo.name,
        polCity: polInfo.city,
        polCountry: polInfo.country,
        pod,
        podName: podInfo.name,
        podCity: podInfo.city,
        podCountry: podInfo.country,
        mode: String(transport.mode || transport.modeOfTransport || "AIR").toUpperCase(),
        service_route: String(transport.serviceRoute || `${pol}-${pod} Direct`),
        carrier: String(transport.carrier || ""),
        container_type: String(transport.containerType || "Air Cargo Unit"),
        etd: String(transport.etd || new Date(Date.now() + 7 * 24 * 60 * 60 * 1e3).toISOString().split("T")[0]),
        eta: String(transport.eta || new Date(Date.now() + 10 * 24 * 60 * 60 * 1e3).toISOString().split("T")[0]),
        transit_time_days: Number(transport.transitTime || transport.transitTimeDays) || 3,
        incoterm: String(transport.incoterm || "FOB"),
        incoterm_location: String(transport.incotermLocation || ""),
        priority: String(transport.priority || "normal")
      },
      cargo: {
        cargo_type: String(cargo.cargoType || ""),
        cargo_category: String(cargo.category || "General"),
        hs_code: String(cargo.hsCode || ""),
        hs_chapter: String(cargo.hsCode || "").split(".")[0] || "",
        packing_type: String(cargo.packingType || cargo.packaging || ""),
        packages: Number(cargo.numberOfPackages || cargo.packageCount) || 0,
        gross_weight_kg: Number(cargo.grossWeight || cargo.weight) || 0,
        net_weight_kg: Number(cargo.netWeight) || 0,
        volume_cbm: Number(cargo.volumeM3 || cargo.volume) || 0,
        stackability: cargo.stackable !== false,
        temp_control_required: Boolean(cargo.temperatureControl || cargo.tempControl),
        is_dg: Boolean(cargo.dangerousGoods || cargo.isDG)
      },
      seller: {
        name: String(seller.contactPerson || seller.contact_person || ""),
        company: String(seller.companyName || seller.company_name || ""),
        email: String(seller.email || ""),
        phone: String(seller.phone || ""),
        country: getCountryName(seller.country),
        city: String(seller.city || ""),
        address: String(seller.address || ""),
        tax_id: String(seller.taxId || seller.tax_id || "")
      },
      buyer: {
        name: String(buyer.contactPerson || buyer.contact_person || ""),
        company: String(buyer.companyName || buyer.company_name || ""),
        email: String(buyer.email || ""),
        phone: String(buyer.phone || ""),
        country: getCountryName(buyer.country),
        city: String(buyer.city || ""),
        address: String(buyer.address || ""),
        tax_id: String(buyer.taxId || buyer.tax_id || "")
      },
      value: shipmentValue
    };
  };
  reactExports.useEffect(() => {
    console.log("[RiskcastSummary] Loading state from localStorage...");
    const savedState = localStorage.getItem("RISKCAST_STATE");
    if (savedState) {
      try {
        const parsed = JSON.parse(savedState);
        console.log("[RiskcastSummary] Parsed RISKCAST_STATE:", parsed);
        if (parsed.transport) {
          const transformed = transformInputStateToSummary(parsed);
          console.log("[RiskcastSummary] Transformed data:", transformed);
          setData(transformed);
          const riskModules = parsed.riskModules || parsed.modules || {};
          setModules({
            esg: riskModules.esg !== false,
            weather: riskModules.weather !== false,
            portCongestion: riskModules.port !== false && riskModules.portCongestion !== false,
            carrierPerformance: riskModules.carrier !== false,
            marketScanner: riskModules.market === true,
            insurance: riskModules.insurance !== false
          });
        } else if (parsed.trade) {
          setData({
            ...defaultData,
            ...parsed
          });
        }
      } catch (e) {
        console.warn("[RiskcastSummary] Failed to parse saved state:", e);
      }
    } else {
      console.log("[RiskcastSummary] No RISKCAST_STATE found, using default data");
    }
    const savedModules = localStorage.getItem("summary_modules_state");
    if (savedModules) {
      try {
        setModules(JSON.parse(savedModules));
      } catch (e) {
        console.warn("Failed to parse saved modules:", e);
      }
    }
  }, []);
  reactExports.useEffect(() => {
    localStorage.setItem("summary_modules_state", JSON.stringify(modules));
  }, [modules]);
  const validationIssues = getValidationIssues(data);
  const handleFieldClick = reactExports.useCallback((path, event) => {
    const fieldConfig2 = FIELD_CONFIG[path];
    if (!fieldConfig2) return;
    const value = getNestedValue(data, path);
    const rect = event?.target instanceof HTMLElement ? event.target.getBoundingClientRect() : { left: window.innerWidth / 2 - 150, top: window.innerHeight / 2 - 100 };
    setEditor({
      isOpen: true,
      field: path,
      value,
      position: { x: rect.left, y: rect.top + 40 }
    });
  }, [data]);
  const handleEditorSave = reactExports.useCallback((value) => {
    setSaveState("saving");
    const newData = JSON.parse(JSON.stringify(data));
    setNestedValue(newData, editor.field, value);
    setData(newData);
    localStorage.setItem("RISKCAST_STATE", JSON.stringify(newData));
    setTimeout(() => {
      setSaveState("saved");
      setLastSaved(/* @__PURE__ */ new Date());
    }, 500);
  }, [data, editor.field]);
  const handleEditorClose = reactExports.useCallback(() => {
    setEditor((prev) => ({ ...prev, isOpen: false }));
  }, []);
  const handleModuleToggle = reactExports.useCallback((key) => {
    setModules((prev) => ({ ...prev, [key]: !prev[key] }));
    setSaveState("unsaved");
    setTimeout(() => {
      setSaveState("saved");
      setLastSaved(/* @__PURE__ */ new Date());
    }, 500);
  }, []);
  const handleSaveDraft = reactExports.useCallback(() => {
    setSaveState("saving");
    localStorage.setItem("RISKCAST_STATE", JSON.stringify(data));
    localStorage.setItem("summary_modules_state", JSON.stringify(modules));
    setTimeout(() => {
      setSaveState("saved");
      setLastSaved(/* @__PURE__ */ new Date());
    }, 500);
  }, [data, modules]);
  const handleBack = reactExports.useCallback(() => {
    window.history.back();
  }, []);
  const handleRunAnalysis = reactExports.useCallback(async () => {
    setIsAnalyzing(true);
    try {
      localStorage.setItem("RISKCAST_STATE", JSON.stringify(data));
      localStorage.setItem("summary_modules_state", JSON.stringify(modules));
      const payload = {
        ...data,
        modules,
        timestamp: (/* @__PURE__ */ new Date()).toISOString()
      };
      let results = null;
      try {
        const response = await fetch("/api/v1/risk/v2/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (response.ok) {
          results = await response.json();
        }
      } catch (apiError) {
        console.warn("[RiskcastSummary] API not available, generating mock results:", apiError);
      }
      if (!results) {
        const hasRoute = data.trade.pol && data.trade.pod;
        const hasCarrier = !!data.trade.carrier;
        const hasCargo = !!data.cargo.cargo_type;
        const hasParties = !!data.seller.company || !!data.buyer.company;
        let baseRisk = 45;
        if (!hasRoute) baseRisk += 15;
        if (!hasCarrier) baseRisk += 10;
        if (!hasCargo) baseRisk += 8;
        if (!hasParties) baseRisk += 5;
        const riskScoreValue = Math.min(95, Math.max(15, baseRisk + Math.floor(Math.random() * 15) - 7));
        const transitDays = data.trade.transit_time_days || 7;
        const getRiskLevel2 = (score) => {
          if (score < 30) return "Low";
          if (score < 50) return "Medium";
          if (score < 75) return "High";
          return "Critical";
        };
        const riskLevel = getRiskLevel2(riskScoreValue);
        results = {
          // Use snake_case to match engine format expected by adapter
          risk_score: riskScoreValue,
          risk_level: riskLevel,
          confidence: 85,
          overall_risk: riskScoreValue,
          profile: {
            score: riskScoreValue,
            level: riskLevel,
            confidence: 85,
            // Factors for radar chart - grouped by category
            factors: {
              // By Category (for radar)
              transport: Math.floor(Math.random() * 20) + 55,
              // Mode, Carrier, Route, Transit
              cargo: Math.floor(Math.random() * 25) + 50,
              // Sensitivity, Packing, DG
              commercial: Math.floor(Math.random() * 20) + 60,
              // Incoterm, Seller, Buyer, Insurance
              compliance: Math.floor(Math.random() * 20) + 45,
              // Documentation, Trade
              external: Math.floor(Math.random() * 25) + 40,
              // Port, Weather, Market
              // Individual key metrics
              carrier_performance: Math.floor(Math.random() * 25) + 55,
              route_complexity: Math.floor(Math.random() * 20) + 60,
              cargo_sensitivity: Math.floor(Math.random() * 30) + 50,
              weather_exposure: Math.floor(Math.random() * 35) + 35,
              port_congestion: Math.floor(Math.random() * 30) + 40
            },
            // Risk matrix
            matrix: {
              probability: Math.floor(riskScoreValue / 20) + 2,
              // 1-9
              severity: Math.floor(riskScoreValue / 15) + 2,
              // 1-9
              quadrant: riskScoreValue >= 75 ? "High-High" : riskScoreValue >= 50 ? "Medium-Medium" : "Low-Low",
              description: riskScoreValue >= 75 ? "High probability and severity - immediate attention required" : riskScoreValue >= 50 ? "Moderate risk profile - monitor closely" : "Low risk profile - standard monitoring sufficient"
            },
            explanation: [
              `Risk score of ${riskScoreValue} indicates ${riskScoreValue >= 75 ? "elevated" : "manageable"} risk level`,
              `Transit from ${data.trade.pol} to ${data.trade.pod} via ${data.trade.mode || "SEA"}`,
              `${transitDays} days estimated transit time`
            ]
          },
          shipment: {
            id: data.shipmentId || `SH-${data.trade.pol}-${data.trade.pod}-${Date.now()}`,
            // Use keys that adapter expects
            pol_code: data.trade.pol,
            pod_code: data.trade.pod,
            origin: data.trade.pol,
            destination: data.trade.pod,
            route: `${data.trade.pol} → ${data.trade.pod}`,
            carrier: data.trade.carrier || "Maersk",
            etd: data.trade.etd,
            eta: data.trade.eta,
            transit_time: transitDays,
            container: data.trade.container_type,
            cargo: data.cargo.cargo_type,
            incoterm: data.trade.incoterm,
            cargo_value: data.value || 1e5,
            value: data.value || 1e5
          },
          // Drivers - Top risk factors impacting this shipment
          drivers: [
            { name: "Carrier Performance", impact: 32, description: "Historical carrier on-time delivery rate" },
            { name: "Cargo Sensitivity", impact: 28, description: "Cargo fragility and special handling needs" },
            { name: "Route Complexity", impact: 22, description: "Distance, transhipments, and route reliability" },
            { name: "Weather Exposure", impact: 18, description: "Climate conditions along route" },
            { name: "Port Congestion", impact: 15, description: "Origin/destination port utilization" },
            { name: "Transit Variance", impact: 12, description: "Schedule reliability and delays" },
            { name: "Incoterm Risk", impact: 10, description: "Responsibility transfer points" },
            { name: "Trade Compliance", impact: 8, description: "Customs and regulatory requirements" }
          ],
          // 16 Risk Layers matching RiskScoringEngineV21 - ALL ENABLED
          layers: [
            // TRANSPORT (4 layers - 35%)
            { name: "Mode Reliability", score: Math.floor(Math.random() * 25) + 55, contribution: 10, category: "TRANSPORT" },
            { name: "Carrier Performance", score: Math.floor(Math.random() * 30) + 50, contribution: 12, category: "TRANSPORT" },
            { name: "Route Complexity", score: Math.floor(Math.random() * 25) + 60, contribution: 8, category: "TRANSPORT" },
            { name: "Transit Time Variance", score: Math.floor(Math.random() * 20) + 45, contribution: 5, category: "TRANSPORT" },
            // CARGO (3 layers - 25%)
            { name: "Cargo Sensitivity", score: Math.floor(Math.random() * 30) + 55, contribution: 12, category: "CARGO" },
            { name: "Packing Quality", score: Math.floor(Math.random() * 25) + 50, contribution: 8, category: "CARGO" },
            { name: "DG Compliance", score: Math.floor(Math.random() * 20) + 30, contribution: 5, category: "CARGO" },
            // COMMERCIAL (4 layers - 20%)
            { name: "Incoterm Risk", score: Math.floor(Math.random() * 25) + 45, contribution: 8, category: "COMMERCIAL" },
            { name: "Seller Credibility", score: Math.floor(Math.random() * 20) + 60, contribution: 6, category: "COMMERCIAL" },
            { name: "Buyer Credibility", score: Math.floor(Math.random() * 20) + 65, contribution: 4, category: "COMMERCIAL" },
            { name: "Insurance Adequacy", score: Math.floor(Math.random() * 15) + 70, contribution: 2, category: "COMMERCIAL" },
            // COMPLIANCE (2 layers - 10%)
            { name: "Documentation", score: Math.floor(Math.random() * 20) + 50, contribution: 5, category: "COMPLIANCE" },
            { name: "Trade Compliance", score: Math.floor(Math.random() * 25) + 45, contribution: 5, category: "COMPLIANCE" },
            // EXTERNAL (3 layers - 10%)
            { name: "Port Congestion", score: Math.floor(Math.random() * 30) + 40, contribution: 4, category: "EXTERNAL" },
            { name: "Weather Climate", score: Math.floor(Math.random() * 35) + 35, contribution: 3, category: "EXTERNAL" },
            { name: "Market Volatility", score: Math.floor(Math.random() * 25) + 30, contribution: 3, category: "EXTERNAL" }
          ],
          // Financial loss metrics
          loss: {
            expectedLoss: Math.round((data.value || 1e5) * (riskScoreValue / 100) * 0.05),
            // ~5% of value * risk
            p95: Math.round((data.value || 1e5) * (riskScoreValue / 100) * 0.08),
            // VaR 95%
            p99: Math.round((data.value || 1e5) * (riskScoreValue / 100) * 0.12),
            // CVaR 99%
            tailContribution: 25
          },
          // Timeline projections
          timeline: {
            projections: Array.from({ length: 7 }, (_, i) => ({
              date: new Date(Date.now() + i * 24 * 60 * 60 * 1e3).toISOString().split("T")[0],
              p10: Math.max(0, riskScoreValue - 15 - Math.random() * 5),
              p50: riskScoreValue + (Math.random() - 0.5) * 10,
              p90: Math.min(100, riskScoreValue + 15 + Math.random() * 5)
            }))
          },
          // Risk scenario projections (for fan chart)
          riskScenarioProjections: Array.from({ length: 7 }, (_, i) => ({
            date: new Date(Date.now() + i * 24 * 60 * 60 * 1e3).toISOString().split("T")[0],
            p10: Math.max(0, riskScoreValue - 15 - Math.random() * 5),
            p50: riskScoreValue + (Math.random() - 0.5) * 10,
            p90: Math.min(100, riskScoreValue + 15 + Math.random() * 5),
            phase: i < 2 ? "Loading" : i < 5 ? "Transit" : "Discharge"
          })),
          // Scenarios for recommendations
          scenarios: [
            {
              title: "Expedited Shipping",
              description: "Use express carrier to reduce transit time",
              riskReduction: 15,
              costImpact: 2.5
            },
            {
              title: "Alternative Route",
              description: "Route via less congested ports",
              riskReduction: 10,
              costImpact: 1
            },
            {
              title: "Enhanced Insurance",
              description: "Comprehensive cargo protection",
              riskReduction: 20,
              costImpact: 1.5
            }
          ],
          recommendations: [
            {
              type: "primary",
              title: "Consider Alternative Route",
              description: "A direct route via alternative carrier may reduce transit time by 2 days.",
              impact: "medium"
            },
            {
              type: "secondary",
              title: "Monitor Weather Conditions",
              description: "Seasonal weather patterns may affect schedule reliability.",
              impact: "low"
            }
          ],
          reasoning: {
            explanation: `Risk analysis for shipment from ${data.trade.pol} to ${data.trade.pod}. The overall risk score of ${riskScoreValue} indicates ${riskLevel.toUpperCase()} risk level with ${transitDays} days transit time via ${data.trade.mode || "SEA"} transport.`
          },
          // Decision support data (use snake_case for adapter)
          decision_summary: {
            insurance: {
              status: riskScoreValue >= 60 ? "RECOMMENDED" : riskScoreValue >= 40 ? "OPTIONAL" : "NOT_NEEDED",
              recommendation: riskScoreValue >= 60 ? "BUY" : riskScoreValue >= 40 ? "CONSIDER" : "SKIP",
              rationale: riskScoreValue >= 60 ? `High risk score (${riskScoreValue}) suggests comprehensive cargo insurance is advisable` : riskScoreValue >= 40 ? `Moderate risk level - insurance optional based on cargo value ($${(data.value || 1e5).toLocaleString()})` : `Low risk profile - standard coverage should be sufficient`,
              risk_delta_points: riskScoreValue >= 60 ? -15 : riskScoreValue >= 40 ? -8 : -3,
              cost_impact_usd: Math.round((data.value || 1e5) * 5e-3),
              // ~0.5% of cargo value
              providers: ["Allianz", "AIG", "Zurich"]
            },
            timing: {
              status: riskScoreValue >= 50 ? "RECOMMENDED" : "OPTIONAL",
              recommendation: riskScoreValue >= 50 ? "ADJUST_ETD" : "KEEP_ETD",
              rationale: riskScoreValue >= 50 ? `Consider adjusting departure to avoid peak congestion periods` : `Current timing is acceptable for this risk profile`,
              optimal_window: {
                start: new Date(Date.now() + 7 * 24 * 60 * 60 * 1e3).toISOString().split("T")[0],
                end: new Date(Date.now() + 14 * 24 * 60 * 60 * 1e3).toISOString().split("T")[0]
              },
              risk_reduction_points: riskScoreValue >= 50 ? -10 : -3,
              cost_impact_usd: riskScoreValue >= 50 ? 500 : 0
            },
            routing: {
              status: riskScoreValue >= 70 ? "RECOMMENDED" : "NOT_NEEDED",
              recommendation: riskScoreValue >= 70 ? "CHANGE_ROUTE" : "KEEP_ROUTE",
              rationale: riskScoreValue >= 70 ? `Alternative routing via less congested ports may reduce risk significantly` : `Current route ${data.trade.pol} → ${data.trade.pod} is optimal for this shipment`,
              best_alternative: riskScoreValue >= 70 ? "Via transshipment hub (Singapore)" : null,
              tradeoff: riskScoreValue >= 70 ? "+2 days transit, -15% risk" : null,
              risk_reduction_points: riskScoreValue >= 70 ? -12 : 0,
              cost_impact_usd: riskScoreValue >= 70 ? 1200 : 0
            }
          },
          insights: [
            { type: "info", message: "Route analysis completed successfully" },
            { type: "warning", message: "Consider transit time variability" }
          ],
          timestamp: (/* @__PURE__ */ new Date()).toISOString(),
          engine_version: "2.0-mock",
          modules
        };
      }
      localStorage.setItem("RISKCAST_RESULTS_V2", JSON.stringify(results));
      await new Promise((resolve) => setTimeout(resolve, 1e3));
      console.log("[RiskcastSummary] Redirecting to /results...");
      window.location.href = "/results";
    } catch (error) {
      console.error("[RiskcastSummary] Analysis error:", error);
      setSaveState("error");
      alert("Analysis failed. Please try again.");
    } finally {
      setIsAnalyzing(false);
    }
  }, [data, modules]);
  const handleIssueClick = reactExports.useCallback((issue) => {
    if (issue.affectedFields.length > 0) {
      const firstField = issue.affectedFields[0];
      const fieldElement = document.querySelector(`[data-field-path="${firstField}"]`);
      if (fieldElement) {
        fieldElement.scrollIntoView({ behavior: "smooth", block: "center" });
        const rect = fieldElement.getBoundingClientRect();
        handleFieldClick(firstField, { target: fieldElement, left: rect.left, top: rect.top });
      }
    }
  }, [handleFieldClick]);
  const tradeFields = [
    { label: "POL", value: data.trade.pol, path: "trade.pol" },
    { label: "POD", value: data.trade.pod, path: "trade.pod" },
    { label: "Mode", value: data.trade.mode, path: "trade.mode" },
    { label: "Container", value: data.trade.container_type, path: "trade.container_type" },
    { label: "ETD", value: data.trade.etd, path: "trade.etd" },
    { label: "ETA", value: data.trade.eta, path: "trade.eta" },
    { label: "Transit Days", value: data.trade.transit_time_days, path: "trade.transit_time_days" },
    { label: "Incoterm", value: data.trade.incoterm, path: "trade.incoterm" },
    { label: "Carrier", value: data.trade.carrier, path: "trade.carrier" },
    { label: "Priority", value: data.trade.priority, path: "trade.priority" }
  ];
  const cargoFields = [
    { label: "Cargo Type", value: data.cargo.cargo_type, path: "cargo.cargo_type" },
    { label: "HS Code", value: data.cargo.hs_code, path: "cargo.hs_code" },
    { label: "Packages", value: data.cargo.packages, path: "cargo.packages" },
    { label: "Gross Weight", value: `${data.cargo.gross_weight_kg} kg`, path: "cargo.gross_weight_kg" },
    { label: "Volume", value: `${data.cargo.volume_cbm} CBM`, path: "cargo.volume_cbm" },
    { label: "Packing", value: data.cargo.packing_type, path: "cargo.packing_type" },
    { label: "Stackable", value: data.cargo.stackability, path: "cargo.stackability" },
    { label: "Temp Control", value: data.cargo.temp_control_required, path: "cargo.temp_control_required" },
    { label: "Dangerous", value: data.cargo.is_dg, path: "cargo.is_dg" }
  ];
  const sellerFields = [
    { label: "Company", value: data.seller.company, path: "seller.company" },
    { label: "Contact", value: data.seller.name, path: "seller.name" },
    { label: "Email", value: data.seller.email, path: "seller.email" },
    { label: "Phone", value: data.seller.phone, path: "seller.phone" },
    { label: "Country", value: data.seller.country, path: "seller.country" },
    { label: "City", value: data.seller.city, path: "seller.city" }
  ];
  const buyerFields = [
    { label: "Company", value: data.buyer.company, path: "buyer.company" },
    { label: "Contact", value: data.buyer.name, path: "buyer.name" },
    { label: "Email", value: data.buyer.email, path: "buyer.email" },
    { label: "Phone", value: data.buyer.phone, path: "buyer.phone" },
    { label: "Country", value: data.buyer.country, path: "buyer.country" },
    { label: "City", value: data.buyer.city, path: "buyer.city" }
  ];
  const fieldConfig = FIELD_CONFIG[editor.field] ?? { type: "text", label: editor.field };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "min-h-screen bg-gradient-to-br from-[#0a1628] via-[#0d1f35] to-[#0a1628]", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(Header, { saveState, lastSaved }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("main", { className: "px-12 py-8 pb-28", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(HeroOverview, { data }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mt-8 grid grid-cols-3 gap-6", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "col-span-2 space-y-6", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-2 gap-6", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              InfoPanel,
              {
                title: "Trade Details",
                icon: "trade",
                fields: tradeFields,
                validationIssues,
                onFieldClick: handleFieldClick
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              InfoPanel,
              {
                title: "Cargo Details",
                icon: "cargo",
                fields: cargoFields,
                validationIssues,
                onFieldClick: handleFieldClick
              }
            )
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-2 gap-6", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              InfoPanel,
              {
                title: "Seller/Shipper",
                icon: "seller",
                fields: sellerFields,
                validationIssues,
                onFieldClick: handleFieldClick
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              InfoPanel,
              {
                title: "Buyer/Consignee",
                icon: "buyer",
                fields: buyerFields,
                validationIssues,
                onFieldClick: handleFieldClick
              }
            )
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(IntelligenceModules, { modules, onToggle: handleModuleToggle })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "sticky top-24", children: /* @__PURE__ */ jsxRuntimeExports.jsx(AIAdvisor, { issues: validationIssues, onIssueClick: handleIssueClick }) })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      ActionFooter,
      {
        data,
        modules,
        onRunAnalysis: handleRunAnalysis,
        onSaveDraft: handleSaveDraft,
        onBack: handleBack,
        lastSaved,
        isAnalyzing
      }
    ),
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      SmartInlineEditor,
      {
        isOpen: editor.isOpen,
        field: editor.field,
        label: fieldConfig.label,
        value: editor.value,
        type: fieldConfig.type,
        options: fieldConfig.options,
        position: editor.position,
        transportMode: data.trade?.mode,
        onSave: handleEditorSave,
        onClose: handleEditorClose
      }
    )
  ] });
}
function SummaryPage() {
  return /* @__PURE__ */ jsxRuntimeExports.jsx(RiskcastSummary, {});
}
function App() {
  const [page, setPage] = reactExports.useState("results");
  reactExports.useEffect(() => {
    const path = window.location.pathname;
    if (path.includes("/summary") || path.includes("/shipments/summary")) {
      setPage("summary");
    } else {
      setPage("results");
    }
    const handlePopState = () => {
      const newPath = window.location.pathname;
      if (newPath.includes("/summary") || newPath.includes("/shipments/summary")) {
        setPage("summary");
      } else {
        setPage("results");
      }
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);
  if (page === "summary") {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(SummaryPage, {});
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsx(ResultsPage, {});
}
const scriptRel = "modulepreload";
const assetsURL = function(dep) {
  return "/" + dep;
};
const seen = {};
const __vitePreload = function preload(baseModule, deps, importerUrl) {
  let promise = Promise.resolve();
  if (deps && deps.length > 0) {
    let allSettled = function(promises$2) {
      return Promise.all(promises$2.map((p) => Promise.resolve(p).then((value$1) => ({
        status: "fulfilled",
        value: value$1
      }), (reason) => ({
        status: "rejected",
        reason
      }))));
    };
    document.getElementsByTagName("link");
    const cspNonceMeta = document.querySelector("meta[property=csp-nonce]");
    const cspNonce = cspNonceMeta?.nonce || cspNonceMeta?.getAttribute("nonce");
    promise = allSettled(deps.map((dep) => {
      dep = assetsURL(dep);
      if (dep in seen) return;
      seen[dep] = true;
      const isCss = dep.endsWith(".css");
      const cssSelector = isCss ? '[rel="stylesheet"]' : "";
      if (document.querySelector(`link[href="${dep}"]${cssSelector}`)) return;
      const link = document.createElement("link");
      link.rel = isCss ? "stylesheet" : scriptRel;
      if (!isCss) link.as = "script";
      link.crossOrigin = "";
      link.href = dep;
      if (cspNonce) link.setAttribute("nonce", cspNonce);
      document.head.appendChild(link);
      if (isCss) return new Promise((res, rej) => {
        link.addEventListener("load", res);
        link.addEventListener("error", () => rej(/* @__PURE__ */ new Error(`Unable to preload CSS for ${dep}`)));
      });
    }));
  }
  function handlePreloadError(err$2) {
    const e$1 = new Event("vite:preloadError", { cancelable: true });
    e$1.payload = err$2;
    window.dispatchEvent(e$1);
    if (!e$1.defaultPrevented) throw err$2;
  }
  return promise.then((res) => {
    for (const item of res || []) {
      if (item.status !== "rejected") continue;
      handlePreloadError(item.reason);
    }
    return baseModule().catch(handlePreloadError);
  });
};
class ConsoleErrorTracker {
  captureException(error, context) {
    console.error("[error]", error, context);
  }
  captureMessage(message, level, context) {
    const payload = { level, message, context };
    if (level === "error") {
      console.error("[message]", payload);
    } else if (level === "warning") {
      console.warn("[message]", payload);
    } else {
      console.info("[message]", payload);
    }
  }
}
let tracker = new ConsoleErrorTracker();
function getErrorTracker() {
  return tracker;
}
function captureMessage(message, level, context) {
  getErrorTracker().captureMessage(message, level, context);
}
function getMonitoringReporter() {
  return ((event) => {
  });
}
const SLOW_THRESHOLDS_MS = {
  chart_render_time: 500,
  trace_drawer_open_time: 100,
  analyst_view_first_paint: 500
};
function trackMetric(name, value, context, unit = "ms") {
  const threshold = SLOW_THRESHOLDS_MS[name];
  if (threshold !== void 0 && value > threshold) {
    captureMessage(`Slow metric: ${name} (${Math.round(value)}ms > ${threshold}ms)`, "warning", {
      name,
      value,
      threshold,
      ...context
    });
  }
}
async function initWebVitals(context) {
  try {
    const mod = await __vitePreload(() => import("./web-vitals-CXzOOaUE.js"), true ? [] : void 0);
    const report = (m) => {
      const evt = {
        type: "web-vital",
        name: m.name,
        value: m.value,
        id: m.id,
        rating: m.rating,
        delta: m.delta,
        navigationType: m.navigationType,
        context,
        timestamp: Date.now()
      };
      getMonitoringReporter()(evt);
    };
    mod.onCLS(report);
    mod.onFCP(report);
    mod.onFID(report);
    mod.onINP(report);
    mod.onLCP(report);
    mod.onTTFB(report);
  } catch (e) {
    captureMessage("initWebVitals failed", "warning", { error: String(e) });
  }
}
function initLongTaskObserver(context) {
  try {
    if (!("PerformanceObserver" in window)) return;
    let lastReport = 0;
    const THROTTLE_MS = 5e3;
    const observer = new PerformanceObserver((list) => {
      const now = Date.now();
      if (now - lastReport < THROTTLE_MS) return;
      lastReport = now;
      for (const entry of list.getEntries()) {
        trackMetric("long_task", entry.duration, { entryType: entry.entryType, name: entry.name, ...context }, "ms");
        break;
      }
    });
    observer.observe({ entryTypes: ["longtask"] });
  } catch {
  }
}
clientExports.createRoot(document.getElementById("root")).render(/* @__PURE__ */ jsxRuntimeExports.jsx(App, {}));
void initWebVitals({ app: "riskcast", surface: "root" });
initLongTaskObserver({ app: "riskcast", surface: "root" });
