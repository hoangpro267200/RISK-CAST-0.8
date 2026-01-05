import { r as requireReact, a as requireReactDom } from "./vendor-react-BoEpX7VO.js";
import { r as reactExports, R as RadarChart, P as PolarGrid, a as PolarAngleAxis, b as PolarRadiusAxis, c as Radar, d as React, B as BarChart, C as CartesianGrid, X as XAxis, Y as YAxis, e as Bar, L as LabelList, f as Cell, A as AreaChart, T as Tooltip, g as Area, S as ScatterChart, h as Scatter, i as LineChart, j as Line } from "./vendor-charts-CWR15eOa.js";
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
    contribution: round(toPercent(layer?.contribution), 0)
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
const RiskRadar = ({ layers }) => {
  const [containerRef, containerSize] = useContainerSize();
  if (!layers || layers.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(GlassCard, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-center py-12 text-white/60", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm", children: "No layer data available" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-white/30 mt-1", children: "Layer data is required for this chart" })
    ] }) });
  }
  const data = layers.filter((layer) => layer != null).map((layer) => ({
    name: (layer.name || "Unknown").replace(" Risk", ""),
    value: layer.score ?? 0,
    fullMark: 100
  }));
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-lg font-medium text-white mb-4", children: "Risk Profile Radar" }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        ref: containerRef,
        style: { height: "400px", minHeight: "400px", minWidth: "300px", width: "100%", position: "relative" },
        children: containerSize.ready && containerSize.width > 0 && containerSize.height > 0 ? /* @__PURE__ */ jsxRuntimeExports.jsxs(
          RadarChart,
          {
            width: containerSize.width,
            height: containerSize.height,
            data,
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(PolarGrid, { stroke: "rgba(255,255,255,0.2)" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(PolarAngleAxis, { dataKey: "name", tick: { fill: "rgba(255,255,255,0.6)", fontSize: 12 } }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(PolarRadiusAxis, { angle: 90, domain: [0, 100], tick: { fill: "rgba(255,255,255,0.6)", fontSize: 10 } }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                Radar,
                {
                  name: "Risk Score",
                  dataKey: "value",
                  stroke: "#3B82F6",
                  fill: "#3B82F6",
                  fillOpacity: 0.3,
                  strokeWidth: 2
                }
              )
            ]
          }
        ) : /* @__PURE__ */ jsxRuntimeExports.jsx(ChartSkeleton, { height: 400 })
      }
    )
  ] });
};
function RiskContributionWaterfall({ layers, overallScore, onBarClick }) {
  const [containerRef, containerSize] = useContainerSize();
  const sortedLayers = React.useMemo(() => {
    if (!layers || layers.length === 0) return [];
    return layers.slice().sort((a, b) => (b.contribution ?? 0) - (a.contribution ?? 0));
  }, [layers]);
  const waterfallData = React.useMemo(() => {
    if (sortedLayers.length === 0 || overallScore === 0) return [];
    return sortedLayers.reduce((acc, layer, idx) => {
      const prevValue = idx === 0 ? 0 : acc[idx - 1]?.cumulative ?? 0;
      const contribution = layer.contribution ?? 0;
      const current = overallScore * contribution / 100;
      acc.push({
        name: (layer.name || "").replace(" Risk", ""),
        value: current,
        cumulative: prevValue + current,
        contribution,
        score: layer.score ?? 0,
        layerName: layer.name || ""
      });
      return acc;
    }, []);
  }, [sortedLayers, overallScore]);
  const getBarColor = (score) => {
    if (score >= 70) return "#EF4444";
    if (score >= 40) return "#F59E0B";
    return "#10B981";
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex items-center justify-between mb-6", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-xl font-medium text-white", children: "Layer Contribution Waterfall" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-white/40 mt-1", children: "How each layer contributes to the overall score" })
    ] }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        ref: containerRef,
        style: { height: "400px", minHeight: "400px", minWidth: "300px", width: "100%", position: "relative" },
        children: waterfallData.length === 0 ? /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "h-full flex items-center justify-center text-white/40", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-center", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm", children: "No layer data available" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-white/30 mt-1", children: "Layer contribution data is required for this chart" })
        ] }) }) : containerSize.ready && containerSize.width > 0 && containerSize.height > 0 ? /* @__PURE__ */ jsxRuntimeExports.jsxs(
          BarChart,
          {
            width: containerSize.width,
            height: containerSize.height,
            data: waterfallData,
            margin: { top: 20, right: 20, left: 20, bottom: 60 },
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(CartesianGrid, { strokeDasharray: "3 3", stroke: "rgba(255,255,255,0.1)" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                XAxis,
                {
                  dataKey: "name",
                  angle: -45,
                  textAnchor: "end",
                  height: 60,
                  tick: { fill: "rgba(255,255,255,0.6)", fontSize: 12 },
                  tickLine: { stroke: "rgba(255,255,255,0.2)" }
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                YAxis,
                {
                  tick: { fill: "rgba(255,255,255,0.6)", fontSize: 12 },
                  tickLine: { stroke: "rgba(255,255,255,0.2)" },
                  axisLine: { stroke: "rgba(255,255,255,0.2)" }
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsxs(Bar, { dataKey: "value", radius: [4, 4, 0, 0], children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  LabelList,
                  {
                    dataKey: "contribution",
                    position: "top",
                    formatter: (v) => `${Math.round(Number(v))}%`,
                    fill: "rgba(255,255,255,0.7)",
                    fontSize: 11
                  }
                ),
                waterfallData.map((entry) => /* @__PURE__ */ jsxRuntimeExports.jsx(
                  Cell,
                  {
                    fill: getBarColor(entry.score),
                    style: { cursor: onBarClick ? "pointer" : "default" },
                    onClick: () => onBarClick?.(entry.layerName)
                  },
                  entry.layerName
                ))
              ] })
            ]
          }
        ) : /* @__PURE__ */ jsxRuntimeExports.jsx(ChartSkeleton, { height: 400 })
      }
    )
  ] });
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
const CircleAlert = createLucideIcon("CircleAlert", [
  ["circle", { cx: "12", cy: "12", r: "10", key: "1mglay" }],
  ["line", { x1: "12", x2: "12", y1: "8", y2: "12", key: "1pkeuh" }],
  ["line", { x1: "12", x2: "12.01", y1: "16", y2: "16", key: "4dfq90" }]
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
const RefreshCw = createLucideIcon("RefreshCw", [
  ["path", { d: "M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8", key: "v9h5vc" }],
  ["path", { d: "M21 3v5h-5", key: "1q7to0" }],
  ["path", { d: "M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16", key: "3uifl3" }],
  ["path", { d: "M8 16H3v5", key: "1cv678" }]
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
const Zap = createLucideIcon("Zap", [
  [
    "path",
    {
      d: "M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z",
      key: "1xq2db"
    }
  ]
]);
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
const RiskScenarioFanChart = ({ data, etd, eta }) => {
  const [containerRef, containerSize] = useContainerSize();
  if (!data || data.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(GlassCard, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-center py-12 text-white/60", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm", children: "No scenario projection data available" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-white/30 mt-1", children: "Scenario projection data is required for this chart" })
    ] }) });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mb-4", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-lg font-medium text-white", children: "Risk Scenario Projections" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: "text-sm text-white/60", children: [
        "ETD: ",
        etd || "N/A",
        " → ETA: ",
        eta || "N/A"
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        ref: containerRef,
        style: { height: "400px", minHeight: "400px", minWidth: "300px", width: "100%", position: "relative" },
        children: containerSize.ready && containerSize.width > 0 && containerSize.height > 0 ? /* @__PURE__ */ jsxRuntimeExports.jsxs(
          AreaChart,
          {
            width: containerSize.width,
            height: containerSize.height,
            data,
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(CartesianGrid, { strokeDasharray: "3 3", stroke: "rgba(255,255,255,0.1)" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(XAxis, { dataKey: "date", tick: { fill: "rgba(255,255,255,0.6)" } }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(YAxis, { tick: { fill: "rgba(255,255,255,0.6)" } }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                Tooltip,
                {
                  contentStyle: {
                    backgroundColor: "rgba(0,0,0,0.9)",
                    border: "1px solid rgba(255,255,255,0.2)",
                    borderRadius: "12px"
                  }
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                Area,
                {
                  type: "monotone",
                  dataKey: "p90",
                  stackId: "1",
                  stroke: "none",
                  fill: "rgba(59,130,246,0.1)",
                  name: "90th Percentile"
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                Area,
                {
                  type: "monotone",
                  dataKey: "p10",
                  stackId: "1",
                  stroke: "none",
                  fill: "rgba(59,130,246,0.1)",
                  name: "10th Percentile"
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                Area,
                {
                  type: "monotone",
                  dataKey: "p50",
                  stroke: "#3B82F6",
                  strokeWidth: 2,
                  fill: "none",
                  name: "Median"
                }
              ),
              data.some((d) => d.expected !== void 0) && /* @__PURE__ */ jsxRuntimeExports.jsx(
                Area,
                {
                  type: "monotone",
                  dataKey: "expected",
                  stroke: "#F59E0B",
                  strokeWidth: 2,
                  strokeDasharray: "5 5",
                  fill: "none",
                  name: "Expected"
                }
              )
            ]
          }
        ) : /* @__PURE__ */ jsxRuntimeExports.jsx(ChartSkeleton, { height: 400 })
      }
    )
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
  const CustomTooltip = ({ active, payload }) => {
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
              /* @__PURE__ */ jsxRuntimeExports.jsx(Tooltip, { content: /* @__PURE__ */ jsxRuntimeExports.jsx(CustomTooltip, {}) }),
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
const FinancialModule = ({ financial }) => {
  const [containerRef, containerSize] = useContainerSize();
  if (!financial.lossCurve || financial.lossCurve.length === 0) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(GlassCard, { children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-center py-12 text-white/60", children: "No loss curve data available" }) });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(GlassCard, { children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mb-4", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-lg font-medium text-white", children: "Financial Loss Distribution" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-3 gap-4 mt-4 text-sm", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-white/60", children: "Expected Loss" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-white font-semibold", children: [
            "$",
            (financial.expectedLoss / 1e3).toFixed(1),
            "K"
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-white/60", children: "VaR 95%" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-white font-semibold", children: [
            "$",
            (financial.var95 / 1e3).toFixed(1),
            "K"
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-white/60", children: "CVaR 95%" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-white font-semibold", children: [
            "$",
            (financial.cvar95 / 1e3).toFixed(1),
            "K"
          ] })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        ref: containerRef,
        style: { height: "350px", minHeight: "350px", minWidth: "300px", width: "100%", position: "relative" },
        children: containerSize.ready && containerSize.width > 0 && containerSize.height > 0 ? /* @__PURE__ */ jsxRuntimeExports.jsxs(
          LineChart,
          {
            width: containerSize.width,
            height: containerSize.height,
            data: financial.lossCurve,
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(CartesianGrid, { strokeDasharray: "3 3", stroke: "rgba(255,255,255,0.1)" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(XAxis, { dataKey: "loss", tick: { fill: "rgba(255,255,255,0.6)" } }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(YAxis, { tick: { fill: "rgba(255,255,255,0.6)" } }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                Tooltip,
                {
                  contentStyle: {
                    backgroundColor: "rgba(0,0,0,0.9)",
                    border: "1px solid rgba(255,255,255,0.2)",
                    borderRadius: "12px"
                  }
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(Line, { type: "monotone", dataKey: "probability", stroke: "#EF4444", strokeWidth: 2 })
            ]
          }
        ) : /* @__PURE__ */ jsxRuntimeExports.jsx(ChartSkeleton, { height: 350 })
      }
    )
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
      const timestamp = `?t=${Date.now()}&_=${Math.random().toString(36).substr(2, 9)}`;
      const response = await fetch(`/results/data${timestamp}`, {
        method: "GET",
        headers: {
          "Cache-Control": "no-cache, no-store, must-revalidate",
          "Pragma": "no-cache",
          "Accept": "application/json"
        }
      });
      if (!response.ok) {
        throw new Error(`Failed to fetch results: ${response.status} ${response.statusText}`);
      }
      const _rawResult = await response.json();
      console.log("[ResultsPage] Raw result from backend:", _rawResult);
      const normalized = adaptResultV2(_rawResult);
      console.log("[ResultsPage] Normalized view model:", normalized);
      setViewModel(normalized);
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
function App() {
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
