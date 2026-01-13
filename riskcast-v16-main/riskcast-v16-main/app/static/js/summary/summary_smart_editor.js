/**
 * ==========================================================
 * SMARTEDITOR_V100.JS – Intelligent Form Engine
 * RISKCAST FutureOS v100
 * ==========================================================
 *
 * Chức năng:
 * - Auto-bind input/select/textarea → update StateSync
 * - Auto-calc ETA, dim-weight, container fit logic
 * - Auto-suggest carrier & service route
 * - Debounced input to avoid lag
 * - Field-impact visual highlighting
 * - Emit events → Validator + Renderer
 */

const SmartEditor = (() => {
    "use strict";

    const DEBOUNCE_MS = 250;
    let debounceTimers = {};

    /* -----------------------------------------------
     * INIT SMART EDITOR
     * ----------------------------------------------- */
    function init() {
        console.log("%c[SmartEditor] Initializing…", "color:#00ffff");

        bindInputs();
        bindSelects();
        bindTextareas();

        console.log("%c[SmartEditor] Ready ✓", "color:#00ff88");
    }

    /* -----------------------------------------------
     * BIND INPUT FIELDS
     * ----------------------------------------------- */
    function bindInputs() {
        document.querySelectorAll("input[data-field]").forEach((el) => {
            el.addEventListener("input", () => debounceUpdate(el));
        });
    }

    function bindSelects() {
        document.querySelectorAll("select[data-field]").forEach((el) => {
            el.addEventListener("change", () => instantUpdate(el));
        });
    }

    function bindTextareas() {
        document.querySelectorAll("textarea[data-field]").forEach((el) => {
            el.addEventListener("input", () => debounceUpdate(el));
        });
    }

    /* -----------------------------------------------
     * DEBOUNCE UPDATE
     * ----------------------------------------------- */
    function debounceUpdate(el) {
        const field = el.dataset.field;

        if (debounceTimers[field]) clearTimeout(debounceTimers[field]);

        debounceTimers[field] = setTimeout(() => {
            instantUpdate(el);
        }, DEBOUNCE_MS);
    }

    /* -----------------------------------------------
     * INSTANT UPDATE
     * ----------------------------------------------- */
    function instantUpdate(el) {
        const field = el.dataset.field;
        const value = el.value;

        console.log("[SmartEditor] change", field, value);

        updateState(field, value);
        highlightImpact(el);
        runAutoLogic(field, value);

        Renderer.renderQuickSummary(StateSync.getState());
    }

    /* -----------------------------------------------
     * UPDATE STATE
     * ----------------------------------------------- */
    function updateState(field, value) {
        const [section, key] = field.split(".");
        StateSync.updateField(section, key, value);
    }

    /* -----------------------------------------------
     * FIELD HIGHLIGHT EFFECT
     * ----------------------------------------------- */
    function highlightImpact(el) {
        el.classList.add("field-impact");
        setTimeout(() => el.classList.remove("field-impact"), 700);
    }

    /* -----------------------------------------------
     * AUTO LOGIC ROUTER
     * ----------------------------------------------- */
    function runAutoLogic(field, value) {
        const [section, key] = field.split(".");
        const state = StateSync.getState();

        if (section === "trade_route" && (key === "etd" || key === "transit_time"))
            autoCalcETA(state);

        if (key === "pol" || key === "pod")
            autoSuggestRoute(state);

        if (section === "cargo_packing" && key === "volume_cbm")
            autoContainerFit(state);

        if (section === "cargo_packing" && key === "hs_code")
            autoHSLogic(state);

        Validator.forceValidation(); // re-check warnings
    }

    /* -----------------------------------------------
     * AUTO CALCULATE ETA
     * ----------------------------------------------- */
    function autoCalcETA(state) {
        const etd = state.trade_route.etd;
        const t = state.trade_route.transit_time;

        if (!etd || !t) return;

        const eta = StateSync.calculateETA(etd, t);
        StateSync.updateField("trade_route", "eta", eta);
    }

    /* -----------------------------------------------
     * ROUTE SUGGESTION
     * ----------------------------------------------- */
    function autoSuggestRoute(state) {
        const pol = state.trade_route.pol;
        const pod = state.trade_route.pod;

        if (!pol || !pod) return;

        const routes = DatasetLoader.getServiceRoutes(pol, pod);
        if (routes.length > 0) {
            const best = routes[0];
            StateSync.updateField("trade_route", "service_route", best.id);
            StateSync.updateField("trade_route", "carrier", best.carrier);
            console.log("[SmartEditor] Auto route selected:", best.id);
        }
    }

    /* -----------------------------------------------
     * AUTO CONTAINER LOGIC (volume → container)
     * ----------------------------------------------- */
    function autoContainerFit(state) {
        const vol = parseFloat(state.cargo_packing.volume_cbm);
        if (!vol) return;

        const types = DatasetLoader.getContainerTypes();
        const fit = types.find((c) => vol <= c.capacity_cbm);

        if (fit) {
            StateSync.updateField("trade_route", "container_type", fit.code);
            console.log("[SmartEditor] Auto container fit:", fit.code);
        }
    }

    /* -----------------------------------------------
     * HS CODE AUTO-LOGIC (DG, electronics…)
     * ----------------------------------------------- */
    function autoHSLogic(state) {
        const hs = (state.cargo_packing.hs_code || "") + "";

        // Electronics (85xxxx)
        if (hs.startsWith("85")) {
            StateSync.updateField("cargo_packing", "stackability", "No");
            console.log("[SmartEditor] HS electronics → No stack");
        }

        // Chemicals/DG
        if (hs.startsWith("28") || hs.startsWith("29")) {
            StateSync.updateField("cargo_packing", "dangerous_goods", "Yes");
            console.log("[SmartEditor] HS indicates DG → Yes");
        }
    }

    /* -----------------------------------------------
     * PUBLIC API
     * ----------------------------------------------- */
    return {
        init,
    };
})();

window.SmartEditor = SmartEditor;
console.log("[SmartEditor] Module loaded ✓");
