// ============================================
// RISKCAST OVERVIEW V80+ NEURAL EDITION
// JavaScript Architecture - Modular & Clean
// ============================================

// === SAMPLE DATA ===
const SAMPLE_DATA = {
    shipment: {
        id: "RC-2025-001",
        title: "VN Coffee Beans to EU",
        status: "ACTIVE",
        mode: "Sea",
        carrier: "MAERSK",
        storyline: {
            summary: "Congestion at Singapore + storms in Northern Europe."
        }
    },
    transport: {
        tradeLane: "VN → EU",
        mode: "Sea",
        shipmentType: "FCL",
        serviceRoute: "Asia-Europe Direct",
        carrier: "MAERSK",
        priority: "Balanced",
        incoterm: "FOB",
        incotermLocation: "Ho Chi Minh Port",
        pol: "Ho Chi Minh, VN",
        pod: "Rotterdam, NL",
        containerType: "40' HC",
        etd: "2025-12-12",
        scheduleFrequency: "Weekly",
        transitTime: 21,
        eta: "2026-01-02",
        reliabilityScore: 86
    },
    cargo: {
        cargoType: "Coffee Beans",
        hsCode: "0901.11",
        packingType: "Jute Bags",
        numberOfPackages: 420,
        grossWeightKg: 21000,
        netWeightKg: 20500,
        volumeM3: 67.2,
        stackability: "Yes",
        insuranceValueUSD: 2400000,
        insuranceCoverageType: "All Risks",
        cargoSensitivity: "MEDIUM",
        dangerousGoods: false,
        description: "Arabica coffee beans, Grade A",
        specialHandling: "Keep dry, temperature controlled"
    },
    seller: {
        companyName: "Vietnam Coffee Exports JSC",
        businessType: "Exporter",
        country: "Vietnam",
        city: "Ho Chi Minh City",
        address: "123 Nguyen Hue Street, District 1",
        contactPerson: "Nguyen Van A",
        contactRole: "Export Manager",
        email: "export@vncoffee.vn",
        phone: "+84 28 1234 5678",
        taxId: "VN0123456789"
    },
    buyer: {
        companyName: "European Coffee Traders BV",
        businessType: "Importer",
        country: "Netherlands",
        city: "Rotterdam",
        address: "456 Wilhelminaplein, 3072 DE",
        contactPerson: "Jan de Vries",
        contactRole: "Procurement Director",
        email: "procurement@eucoffee.nl",
        phone: "+31 10 1234 567",
        taxId: "NL123456789B01"
    },
    risk: {
        overallScore: 67,
        level: "MEDIUM",
        weatherScore: 0.55,
        politicalScore: 0.3,
        securityScore: 0.4,
        congestionScore: 0.7,
        delayRisk: 0.32
    },
    modules: {
        esgRisk: { active: true, name: "ESG Risk" },
        weatherClimateRisk: { active: true, name: "Weather & Climate" },
        portCongestionRisk: { active: true, name: "Port Congestion" },
        carrierPerformance: { active: true, name: "Carrier Performance" },
        marketConditionScanner: { active: false, name: "Market Scanner" },
        insuranceOptimization: { active: true, name: "Insurance Optimization" }
    },
    kpi: {
        shipmentValue: 2400000,
        transitDaysPlanned: 21,
        transitDaysProjected: 23,
        onTimeProbability: 0.78,
        carbonFootprint: 8.2,
        estimatedCost: 0,
        congestionIndex: 0,
        carbonKg: 0
    }
};

const ICONS = {
    money: '<svg width="24" height="24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M12 8c-2.21 0-4 1.343-4 3s1.79 3 4 3 4 1.343 4 3-1.79 3-4 3"/><path d="M12 3v2m0 14v2"/><path d="M17 5H9a5 5 0 0 0-5 5v4a5 5 0 0 0 5 5h8a5 5 0 0 0 5-5v-4a5 5 0 0 0-5-5z"/></svg>',
    calendar: '<svg width="24" height="24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4m-8-4v4M3 10h18"/></svg>',
    timer: '<svg width="24" height="24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><circle cx="12" cy="14" r="8"/><path d="M12 14l4-4"/><path d="M9 2h6"/></svg>',
    earth: '<svg width="24" height="24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15 15 0 0 1 0 20"/><path d="M12 2a15 15 0 0 0 0 20"/></svg>',
    shield: '<svg width="24" height="24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    warning: '<svg width="24" height="24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M10.29 3.86 1.82 18a1 1 0 0 0 .86 1.5h18.64a1 1 0 0 0 .86-1.5L13.71 3.86a1 1 0 0 0-1.72 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    weather: '<svg width="24" height="24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M20 17.58A5 5 0 0 0 18 8h-1.26A8 8 0 1 0 4 16"/><line x1="8" y1="19" x2="8" y2="21"/><line x1="12" y1="19" x2="12" y2="21"/><line x1="16" y1="19" x2="16" y2="21"/></svg>',
    ship: '<svg width="24" height="24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M3 21h18"/><path d="M3 17l2-5h14l2 5"/><path d="M5 12V8l7-5 7 5v4"/><path d="M12 3v9"/></svg>',
    plane: '<svg width="24" height="24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M2.5 19.5 21 12 2.5 4.5 2 10l11 2-11 2z"/><path d="m9 12-2.5 7.5"/></svg>',
    truck: '<svg width="24" height="24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M3 7h12v10H3z"/><path d="M15 10h4l2 2v5h-6z"/><circle cx="7.5" cy="17.5" r="1.5"/><circle cx="17.5" cy="17.5" r="1.5"/></svg>',
    box: '<svg width="24" height="24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><path d="M3.27 6.96 12 12.01 20.73 6.96"/><path d="M12 22.08V12"/></svg>',
    package: '<svg width="24" height="24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="m16.5 9.4-9-5.19"/><path d="m21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><path d="M3.3 7 12 12l8.7-5"/><path d="M12 22V12"/></svg>',
    barcode: '<svg width="24" height="24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M4 5h1v14H4zM7 5h1v14H7zM10 5h2v14h-2zM14 5h1v14h-1zM17 5h2v14h-2z"/></svg>',
    user: '<svg width="24" height="24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    building: '<svg width="24" height="24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M3 21h18"/><path d="M6 21V8a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v13"/><path d="M9 21v-4h6v4"/><path d="M9 9h6"/><path d="M9 12h6"/></svg>',
    edit: '<svg width="18" height="18" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25z"/><path d="M14.06 4.94 17.81 8.69"/></svg>'
};

function icon(name) {
    return ICONS[name] || '';
}
const core = window.RISKCAST_INPUT_CORE;

function formatTradeLane(raw) {
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
    // fallback: replace underscores with arrows
    if (raw.includes('→') && !/trade lane/i.test(raw)) return `${raw} Trade Lane`;
    return raw.replace(/_/g, ' → ').replace(/-/g, ' → ');
}

// === STATE MANAGEMENT ===
let RISKCAST_STATE = null;

function moduleNameFromKey(key) {
    return key
        .replace(/([A-Z])/g, " $1")
        .replace(/_/g, " ")
        .replace(/\s+/g, " ")
        .trim()
        .replace(/^./, (c) => c.toUpperCase());
}

function normalizeModules(modules) {
    const fallback = {
        esgRisk: true,
        weatherClimateRisk: true,
        portCongestionRisk: true,
        carrierPerformance: true,
        marketConditionScanner: true,
        insuranceOptimization: true
    };
    const source = modules && Object.keys(modules).length ? modules : fallback;

    return Object.entries(source).reduce((acc, [key, value]) => {
        if (typeof value === "boolean") {
            acc[key] = { name: moduleNameFromKey(key), active: value };
        } else {
            acc[key] = {
                name: value.name || moduleNameFromKey(key),
                active: Boolean(value.active)
            };
        }
        return acc;
    }, {});
}

function normalizeDate(str) {
    if (!str) return null;
    if (/\d{2}\/\d{2}\/\d{4}/.test(str)) {
        const [d, m, y] = str.split('/');
        return `${y}-${m}-${d}`;
    }
    return str;
}

function normalizeState(rawState) {
    if (!rawState || typeof rawState !== "object") return { ...SAMPLE_DATA };

    const state = JSON.parse(JSON.stringify(rawState));

    // Map transportSetup -> transport if needed
    if (state.transportSetup) {
        const t = state.transportSetup;
        const base = state.transport && typeof state.transport === "object" ? state.transport : {};
        const assignIfEmpty = (key, val) => {
            if (base[key] === undefined || base[key] === null || base[key] === "") {
                if (val !== undefined && val !== null && val !== "") base[key] = val;
            }
        };
        assignIfEmpty("tradeLane", t.tradeLane);
        assignIfEmpty("mode", t.modeOfTransport || t.mode);
        assignIfEmpty("shipmentType", t.shipmentType);
        assignIfEmpty("serviceRoute", t.serviceRoute);
        assignIfEmpty("carrier", t.carrier);
        assignIfEmpty("priority", t.priority);
        assignIfEmpty("incoterm", t.incoterm);
        assignIfEmpty("incotermLocation", t.incotermLocation);
        assignIfEmpty("pol", t.pol);
        assignIfEmpty("pod", t.pod);
        assignIfEmpty("containerType", t.containerType);
        assignIfEmpty("etd", normalizeDate(t.etd));
        assignIfEmpty("eta", normalizeDate(t.eta));
        assignIfEmpty("scheduleFrequency", t.scheduleFrequency);
        assignIfEmpty("transitTime", t.transitTimeDays);
        assignIfEmpty("reliabilityScore", t.reliabilityScore);
        state.transport = base;
    }

    state.transport = state.transport || {};
    state.transport.etd = normalizeDate(state.transport.etd);
    state.transport.eta = normalizeDate(state.transport.eta);
    if (!state.transport.tradeLane && state.transport.pol && state.transport.pod) {
        state.transport.tradeLane = `${state.transport.pol} → ${state.transport.pod}`;
    }
    if (!state.transport.transitTime && state.transport.transitTimeDays) {
        state.transport.transitTime = state.transport.transitTimeDays;
    }

    // Shipment mapping
    state.shipment = state.shipment || {};
    if (!state.shipment.id && state.shipment.code) state.shipment.id = state.shipment.code;
    if (!state.shipment.title && state.transport.tradeLane) {
        state.shipment.title = state.transport.tradeLane;
    }
    if (!state.shipment.status) state.shipment.status = "ACTIVE";

    // KPI normalization
    state.kpi = state.kpi || {};
    if (state.kpi.onTimeProbability > 1) {
        state.kpi.onTimeProbability = state.kpi.onTimeProbability / 100;
    }
    if (state.kpi.delayRisk > 1) {
        state.kpi.delayRisk = state.kpi.delayRisk / 100;
    }

    // Risk normalization
    state.risk = state.risk || {};
    if (state.risk.delayRisk > 1) {
        state.risk.delayRisk = state.risk.delayRisk / 100;
    }
    if (state.risk.weatherRisk > 1) {
        state.risk.weatherRisk = state.risk.weatherRisk / 100;
    }
    if (state.risk.congestionRisk > 1) {
        state.risk.congestionRisk = state.risk.congestionRisk / 100;
    }

    // Modules normalization
    state.modules = normalizeModules(state.modules);

    return core && core.recomputeDerivedState ? core.recomputeDerivedState(state) : state;
}

function loadState() {
    const root = document.getElementById('riskcast-root');
    const stateData = root ? root.dataset.riskcastState : null;
    const localState = (() => {
        try {
            return localStorage.getItem("RISKCAST_STATE");
        } catch (e) {
            return null;
        }
    })();

    // Only merge localStorage state if it's valid JSON and contains transport data
    if (root && localState) {
        try {
            const parsed = JSON.parse(localState);
            if (parsed && parsed.transport) {
                root.dataset.riskcastState = localState;
            }
        } catch (e) {
            // ignore invalid local storage
        }
    }
    
    if (stateData && stateData.trim() !== '') {
        try {
            const parsed = JSON.parse(stateData);
            RISKCAST_STATE = normalizeState(parsed);
            return RISKCAST_STATE;
        } catch (e) {
            console.warn('Failed to parse state, using sample data');
            RISKCAST_STATE = { ...SAMPLE_DATA };
            return RISKCAST_STATE;
        }
    }
    
    RISKCAST_STATE = { ...SAMPLE_DATA };
    return RISKCAST_STATE;
}

function computeDerivedKpi(state) {
    const etd = state.transport.etd;
    const eta = state.transport.eta;
    const reliabilityScore = Number(state.transport.reliabilityScore || 0);
    const delayRisk = state.risk.delayRisk != null ? state.risk.delayRisk : Math.max(0, 1 - reliabilityScore / 100);
    const onTime = state.kpi.onTimeProbability != null ? state.kpi.onTimeProbability : Math.max(0, Math.min(1, (reliabilityScore / 100) * (1 - delayRisk)));
    const transitTime = state.transport.transitTime || state.kpi.transitDaysPlanned || 0;
    let transitProjected = state.kpi.transitDaysProjected;
    if (!transitProjected && etd && eta) {
        const d1 = new Date(etd);
        const d2 = new Date(eta);
        if (!isNaN(d1) && !isNaN(d2)) {
            transitProjected = Math.max(0, Math.round((d2.getTime() - d1.getTime()) / (1000 * 60 * 60 * 24)));
        }
    }
    if (!transitProjected) transitProjected = transitTime;
    const grossWeight = state.cargo.grossWeight || state.cargo.grossWeightKg || 0;
    const emissionFactor = 0.00008;
    const carbonFootprint = state.kpi.carbonFootprint || state.shipment.carbonFootprintTons || +(grossWeight * emissionFactor).toFixed(2);

    state.kpi.transitDaysPlanned = transitTime;
    state.kpi.transitDaysProjected = transitProjected;
    state.kpi.onTimeProbability = onTime;
    state.kpi.carbonFootprint = carbonFootprint;
    state.shipment.transitPlannedDays = transitTime;
    state.shipment.transitActualDays = transitProjected;
    state.shipment.onTimeProbability = onTime;
    state.shipment.carbonFootprintTons = carbonFootprint;
}

// === UTILITY FUNCTIONS ===
function formatUSD(value) {
    if (!value) return '$0';
    return '$' + (value / 1000000).toFixed(1) + 'M';
}

function formatPercent(value) {
    if (value === null || value === undefined) return '0%';
    const normalized = value > 1 ? value : value * 100;
    return Math.round(normalized) + '%';
}

function getRiskColor(score) {
    if (score >= 70) return '#FF3B5C';
    if (score >= 40) return '#FFA726';
    return '#00FFC8';
}

function getRiskLevel(score) {
    if (score >= 70) return { level: 'HIGH', class: 'high' };
    if (score >= 40) return { level: 'MEDIUM', class: 'medium' };
    return { level: 'LOW', class: 'low' };
}

// === HEADER RENDERING ===
function renderHeader() {
    const state = RISKCAST_STATE;
    const formattedTitle = (window.RISKCAST_INPUT_CORE && window.RISKCAST_INPUT_CORE.formatTradeLaneForTitle)
        ? window.RISKCAST_INPUT_CORE.formatTradeLaneForTitle(state.transport.tradeLane || state.shipment.title || state.shipment.name || '')
        : formatTradeLane(state.transport.tradeLane || state.shipment.title || state.shipment.name || '');
    
    document.getElementById('shipment-title').textContent = formattedTitle || 'Shipment';
    document.getElementById('shipment-code').textContent = state.shipment.id || state.shipment.code || 'RC-XXXX';
    const mode = state.transport.mode || state.shipment.mode || 'N/A';
    const carrier = state.transport.carrier || state.shipment.carrier || 'Carrier';
    const status = state.shipment.status || 'ACTIVE';

    const modeBadge = document.getElementById('badge-mode');
    const carrierBadge = document.getElementById('badge-carrier');
    const statusBadge = document.getElementById('badge-status');

    const modeIcon = /air/i.test(mode) ? icon('plane') : /truck|road|land/i.test(mode) ? icon('truck') : icon('ship');
    modeBadge.innerHTML = `<span class="badge-icon icon">${modeIcon}</span><span>${mode}</span>`;
    carrierBadge.innerHTML = `<span class="badge-icon icon">${icon('building')}</span><span>${carrier}</span>`;
    statusBadge.innerHTML = `<span class="badge-icon icon">${icon('shield')}</span><span>${status}</span>`;

    const headerQuick = document.getElementById('header-quick');
    if (headerQuick) {
        const otp = state.shipment.onTimeProbability ?? state.kpi.onTimeProbability ?? (state.transport.reliabilityScore || 0) / 100;
        const reliability = state.transport.reliabilityScore || 0;
        const transit = state.transport.transitTime || state.shipment.transitPlannedDays || state.kpi.transitDaysPlanned || 0;
        const quick = [
            { label: 'ETD', value: state.transport.etd || '--', icon: icon('calendar') },
            { label: 'ETA', value: state.transport.eta || '--', icon: icon('calendar') },
            { label: 'Transit', value: `${transit} d`, icon: icon('timer') },
            { label: 'On-Time', value: formatPercent(otp), icon: icon('timer') },
            { label: 'Reliability', value: formatPercent((reliability || 0) / 100), icon: icon('shield') }
        ];
        headerQuick.innerHTML = quick.map(q => `
            <div class="quick-item">
                <div class="quick-icon icon">${q.icon}</div>
                <div class="quick-label">${q.label}</div>
                <div class="quick-value">${q.value}</div>
            </div>
        `).join('');
    }
}

// === KPI RENDERING ===
function renderKPIs() {
    const state = RISKCAST_STATE;
    const kpiRow = document.getElementById('kpi-row');
    const core = window.RISKCAST_INPUT_CORE;
    const transitProjected = Number(state.kpi.transitDaysProjected || 0);
    const transitPlanned = Number(state.kpi.transitDaysPlanned || 0);
    const insuranceValue = Number(state.cargo.insuranceValue || 0);
    const otp = Number(state.kpi.onTimeProbability || (state.transport.reliabilityScore || 0) / 100);
    
    const kpis = [
        {
            icon: icon('money'),
            label: 'Shipment Value',
            value: state.kpi.shipmentValue || insuranceValue,
            warning: false,
            field: 'shipmentValue'
        },
        {
            icon: icon('calendar'),
            label: 'Transit Days',
            value: `${transitProjected || state.transport.transitTime || 0}/${transitPlanned || state.transport.transitTime || 0}`,
            warning: transitProjected > (transitPlanned || state.transport.transitTime || 0),
            field: 'transitDaysProjected'
        },
        {
            icon: icon('timer'),
            label: 'On-Time Probability',
            value: formatPercent(otp),
            warning: (otp || 0) < 0.8,
            field: 'onTimeProbability'
        },
        {
            icon: icon('earth'),
            label: 'Carbon Footprint',
            value: (state.kpi.carbonFootprint || state.shipment.carbonFootprintTons || 0) + 't CO₂',
            warning: false,
            field: 'carbonFootprint'
        }
    ];
    
    kpiRow.innerHTML = kpis.map(kpi => `
        <div class="kpi-card ${kpi.warning ? 'warning' : ''}" data-section="kpi" data-field="${kpi.field}">
            <div class="kpi-icon icon">${kpi.icon}</div>
            <div class="kpi-label">${kpi.label}</div>
            <div class="kpi-value">${core ? core.formatFieldValue('kpi', kpi.field, kpi.value) : kpi.value}</div>
            <button class="edit-btn" aria-label="Edit ${kpi.label}">${icon('edit')}</button>
        </div>
    `).join('');
}

// === RISK GAUGE RENDERING ===
function updateRiskGauge() {
    const state = RISKCAST_STATE;
    const canvas = document.getElementById('risk-gauge');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const centerX = 90;
    const centerY = 90;
    const radius = 70;
    const score = state.risk.overallScore || 0;
    const color = getRiskColor(score);
    
    // Clear canvas
    ctx.clearRect(0, 0, 180, 180);
    
    // Draw background circle
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.lineWidth = 12;
    ctx.stroke();
    
    // Draw progress arc
    const startAngle = -Math.PI / 2;
    const endAngle = startAngle + (2 * Math.PI * score / 100);
    
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, startAngle, endAngle);
    ctx.strokeStyle = color;
    ctx.lineWidth = 12;
    ctx.lineCap = 'round';
    ctx.shadowBlur = 20;
    ctx.shadowColor = color;
    ctx.stroke();
    
    // Update score text
    document.getElementById('gauge-score').textContent = score;
    document.getElementById('gauge-score').style.color = color;
    
    // Update risk badge
    const riskInfo = getRiskLevel(score);
    const badge = document.getElementById('risk-badge');
    badge.textContent = riskInfo.level + ' RISK';
    badge.className = 'risk-badge ' + riskInfo.class;
}

// === STORYLINE RENDERING ===
function renderStoryline() {
    const container = document.getElementById('situation-items');
    const summaryEl = document.getElementById('situation-summary');
    if (!container) return;
    const state = RISKCAST_STATE;

    if (summaryEl) {
        summaryEl.textContent = state.shipment?.storyline?.summary || '';
    }

    const items = [
        {
            icon: icon('warning'),
            text: 'Delay Risk:',
            value: formatPercent(state.risk.delayRisk || 0)
        },
        {
            icon: icon('shield'),
            text: 'Carrier Reliability:',
            value: formatPercent((state.transport.reliabilityScore || 0) / 100)
        },
        {
            icon: icon('shield'),
            text: 'Insurance Coverage:',
            value: state.cargo.insuranceCoverage || 'Coverage pending'
        }
    ];

    container.innerHTML = items.map(item => `
        <div class="situation-item">
            <span class="situation-icon icon">${item.icon}</span>
            <span class="situation-text">${item.text}</span>
            <span class="situation-value">${item.value}</span>
        </div>
    `).join('');
}

// === TRANSPORT RENDERING ===
function renderTransport() {
    const state = RISKCAST_STATE;
    const transportInfo = document.getElementById('transport-info');
    const core = window.RISKCAST_INPUT_CORE;
    
    const items = [
        { label: 'Trade Lane', value: state.transport.tradeLane || `${state.transport.pol || ''} → ${state.transport.pod || ''}`, highlight: true, field: 'tradeLane' },
        { label: 'Mode', value: state.transport.mode || '—', field: 'mode' },
        { label: 'Shipment Type', value: state.transport.shipmentType || '—', field: 'shipmentType' },
        { label: 'Carrier', value: state.transport.carrier || '—', field: 'carrier' },
        { label: 'Priority', value: state.transport.priority || 'Balanced', field: 'priority' },
        { label: 'Service Route', value: state.transport.serviceRoute || '—', field: 'serviceRoute' },
        { label: 'Incoterm', value: `${state.transport.incoterm || 'N/A'} - ${state.transport.incotermLocation || ''}`, field: 'incoterm' },
        { label: 'Container', value: state.transport.containerType || 'N/A', field: 'containerType' },
        { label: 'POL', value: state.transport.pol || '—', highlight: true, field: 'pol' },
        { label: 'POD', value: state.transport.pod || '—', highlight: true, field: 'pod' },
        { label: 'ETD', value: state.transport.etd || '—', field: 'etd' },
        { label: 'ETA', value: state.transport.eta || '—', field: 'eta' },
        { label: 'Transit Time', value: (state.transport.transitTime || state.transport.transitTimeDays || 0) + ' days', field: 'transitTime' },
        { label: 'Schedule', value: state.transport.scheduleFrequency || '—', field: 'scheduleFrequency' },
        { label: 'Reliability', value: formatPercent((state.transport.reliabilityScore || 0) / 100), highlight: true, field: 'reliabilityScore' }
    ];
    
    transportInfo.innerHTML = items.map(item => `
        <div class="info-item" data-section="transport" data-field="${item.field || ''}">
            <div class="info-label">${item.label}</div>
            <div class="info-value ${item.highlight ? 'highlight' : ''}">${core ? core.formatFieldValue('transport', item.field, item.value) : (item.value || '--')}</div>
            <button class="edit-btn" aria-label="Edit ${item.label}">${icon('edit')}</button>
        </div>
    `).join('');
}

// === CARGO RENDERING ===
function renderCargo() {
    const state = RISKCAST_STATE;
    const cargoInfo = document.getElementById('cargo-info');
    const core = window.RISKCAST_INPUT_CORE;
    
    const items = [
        { label: 'Cargo Type', value: state.cargo.cargoType, field: 'cargoType' },
        { label: 'HS Code', value: state.cargo.hsCode, field: 'hsCode' },
        { label: 'Packing Type', value: state.cargo.packingType, field: 'packingType' },
        { label: 'Packages', value: (state.cargo.numberOfPackages || state.cargo.packages || 0).toString(), field: 'numberOfPackages' },
        { label: 'Gross Weight', value: (state.cargo.grossWeight || state.cargo.grossWeightKg || 0) + ' kg', field: 'grossWeight' },
        { label: 'Net Weight', value: (state.cargo.netWeight || state.cargo.netWeightKg || 0) + ' kg', field: 'netWeight' },
        { label: 'Volume', value: (state.cargo.volumeM3 || 0) + ' m³', field: 'volumeM3' },
        { label: 'Stackability', value: state.cargo.stackability || state.cargo.stackable, field: 'stackability' },
        { label: 'Insurance Value', value: formatUSD(state.cargo.insuranceValue || state.shipment.valueUSD), field: 'insuranceValue' },
        { label: 'Coverage', value: state.cargo.insuranceCoverage || 'All Risks', field: 'insuranceCoverage' },
        { label: 'Sensitivity', value: state.cargo.sensitivity || 'Standard', field: 'sensitivity' },
        { label: 'Dangerous Goods', value: state.cargo.dangerousGoods ? 'YES' : 'NO', danger: state.cargo.dangerousGoods, field: 'dangerousGoods' },
        { label: 'Description', value: state.cargo.description, field: 'description' },
        { label: 'Special Instructions', value: state.cargo.specialInstructions, field: 'specialInstructions' }
    ];
    
    cargoInfo.innerHTML = items.map(item => `
        <div class="cargo-item" data-section="cargo" data-field="${item.field || ''}">
            <div class="cargo-label">${item.label}</div>
            <div class="cargo-value ${item.danger ? 'danger' : ''}">${core ? core.formatFieldValue('cargo', item.field, item.value) : (item.value || '--')}</div>
            <button class="edit-btn" aria-label="Edit ${item.label}">${icon('edit')}</button>
        </div>
    `).join('');
}

// === PARTIES RENDERING ===
function renderParties() {
    const state = RISKCAST_STATE;
    
    renderParty('seller-info', state.seller);
    renderParty('buyer-info', state.buyer);
}

function renderParty(elementId, party) {
    const element = document.getElementById(elementId);
    const core = window.RISKCAST_INPUT_CORE;
    
    const rows = [
        { label: 'Company', value: party.companyName, primary: true, field: 'companyName' },
        { label: 'Type', value: party.businessType, field: 'businessType' },
        { label: 'Country', value: party.country, field: 'country' },
        { label: 'City', value: party.city, field: 'city' },
        { label: 'Address', value: party.address, field: 'address' },
        { label: 'Contact', value: party.contactPerson, field: 'contactPerson' },
        { label: 'Role', value: party.contactRole, field: 'contactRole' },
        { label: 'Email', value: party.email, primary: true, field: 'email' },
        { label: 'Phone', value: party.phone, field: 'phone' },
        { label: 'Tax ID', value: party.taxId, field: 'taxId' }
    ];
    
    element.innerHTML = rows.map(row => `
        <div class="party-row" data-section="${elementId === 'seller-info' ? 'seller' : 'buyer'}" data-field="${row.field}">
            <div class="party-label">${row.label}</div>
            <div class="party-value ${row.primary ? 'primary' : ''}">${core ? core.formatFieldValue(elementId === 'seller-info' ? 'seller' : 'buyer', row.field, row.value) : (row.value || '--')}</div>
            <button class="edit-btn" aria-label="Edit ${row.label}">${icon('edit')}</button>
        </div>
    `).join('');
}

// === MODULES RENDERING ===
function renderModules() {
    const state = RISKCAST_STATE;
    const modulesChips = document.getElementById('modules-chips');
    const modulesCount = document.getElementById('modules-count');
    
    const modules = Object.entries(state.modules || {}).map(([key, val]) => {
        if (typeof val === 'boolean') return { name: moduleNameFromKey(key), active: val };
        return { name: val.name || moduleNameFromKey(key), active: !!val.active };
    });
    const activeCount = modules.filter(m => m.active).length;
    
    modulesCount.textContent = `${activeCount}/${modules.length} active`;
    
    modulesChips.innerHTML = modules.map(module => `
        <div class="module-chip ${module.active ? 'active' : 'inactive'}">
            <span class="module-status-dot"></span>
            <span>${module.name}</span>
        </div>
    `).join('');
}

// === GLOBAL RE-RENDER ===
function refreshOverview() {
    renderHeader();
    renderKPIs();
    renderTransport();
    renderCargo();
    renderParties();
    renderStoryline();
    renderModules();
}

window.rerenderOverview = refreshOverview;

window.applyStatePatch = function (patch) {
    if (!window.RISKCAST_STATE) return;
    if (window.RISKCAST_INPUT_CORE && window.RISKCAST_INPUT_CORE.safeUpdateDeep) {
        window.RISKCAST_STATE = window.RISKCAST_INPUT_CORE.safeUpdateDeep(window.RISKCAST_STATE, patch);
    } else {
        Object.entries(patch || {}).forEach(([section, fields]) => {
            if (!window.RISKCAST_STATE[section]) window.RISKCAST_STATE[section] = {};
            Object.entries(fields || {}).forEach(([k, v]) => {
                window.RISKCAST_STATE[section][k] = v;
            });
        });
    }
    try {
        localStorage.setItem("RISKCAST_STATE", JSON.stringify(window.RISKCAST_STATE));
    } catch (e) {
        console.warn("Failed to persist state", e);
    }
    window.rerenderOverview();
};

// === PARTICLE BACKGROUND ===
function initParticles() {
    const container = document.getElementById('particle-background');
    const particleCount = 60;
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        const layer = i % 3 === 0 ? 'layer-2' : i % 5 === 0 ? 'layer-3' : '';
        particle.className = `particle ${layer}`.trim();
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        particle.style.animationDuration = (18 + Math.random() * 25) + 's';
        particle.style.animationDelay = Math.random() * 12 + 's';
        particle.style.setProperty('--base-opacity', (0.15 + Math.random() * 0.2).toString());
        container.appendChild(particle);
    }
}

// === EVENT HANDLERS ===
function initEventHandlers() {
    // Run Analysis Button
    document.getElementById('btn-run-analysis')?.addEventListener('click', () => {
        const btn = document.getElementById('btn-run-analysis');
        btn.classList.add('pulse-animation');
        setTimeout(() => btn.classList.remove('pulse-animation'), 800);
        window.location.href = '/results';
    });

    document.getElementById('btn-export')?.addEventListener('click', () => {
        alert('Export functionality coming soon');
    });

    document.getElementById('btn-ai-assistant')?.addEventListener('click', () => {
        alert('AI Assistant coming soon');
    });

    document.querySelector('.back-button')?.addEventListener('click', () => {
        window.history.back();
    });

    // ================================
    // 🔥 FIX: Prevent edit panel collapse
    // ================================
    const panel = document.getElementById("edit-panel");

    if (panel) {
        // Click inside panel → do NOT bubble
        panel.addEventListener("click", (e) => {
            e.stopPropagation();
        });
    }

    // Main click handler for opening + outside-close
    document.addEventListener("click", (e) => {
        const editPanel = document.getElementById("edit-panel");

        // If click inside panel → skip
        if (editPanel && editPanel.contains(e.target)) return;

        // If click on edit button → open panel
        const btn = e.target.closest(".edit-btn");
        if (btn) {
            const item = btn.closest("[data-section][data-field]");
            if (item && window.openEditPanel) {
                openEditPanel(item.dataset.section, item.dataset.field);
            }
            return;
        }

        // If panel is open & clicked outside → close
        if (editPanel && editPanel.classList.contains("visible")) {
            if (window.closeEditPanel) closeEditPanel();
        }
    });
}

// === INITIALIZATION ===
function init() {
    console.log('🚀 Initializing RISKCAST Overview v80+');
    
    // Load state
    loadState();
    if (core && core.recomputeDerivedState) {
        RISKCAST_STATE = core.recomputeDerivedState(RISKCAST_STATE);
    } else {
        computeDerivedKpi(RISKCAST_STATE);
    }
    console.log('FINAL RISKCAST_STATE:', RISKCAST_STATE);
    
    // Render all components
    refreshOverview();
    
    // Initialize particles
    initParticles();
    
    // Initialize event handlers
    initEventHandlers();
    
    console.log('✅ RISKCAST Overview v80+ Ready');
}

// === START APPLICATION ===
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

