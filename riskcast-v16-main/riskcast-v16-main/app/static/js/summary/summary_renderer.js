/**
 * ==========================================================
 * SUMMARY_RENDERER_V100.JS – Dynamic Section Rendering
 * RISKCAST FutureOS v100
 * ==========================================================
 *
 * Render 5 sections:
 * - Trade & Route
 * - Cargo & Packing
 * - Seller
 * - Buyer
 * - Risk Modules
 *
 * Render Quick Summary
 */

const Renderer = (() => {
    "use strict";

    /* -------------------------------------------------------
     * RENDER EVERYTHING
     * ------------------------------------------------------- */
    function renderAll(state) {
        const safeState = state || {};
        renderSections(safeState);
        renderQuickSummary(safeState);
    }

    /* -------------------------------------------------------
     * QUICK SUMMARY PANEL
     * ------------------------------------------------------- */
    function renderQuickSummary(state) {
        const tr = (state && state.trade_route) || {};
        const cp = (state && state.cargo_packing) || {};

        setText("qs-trade-lane", `${tr.pol || "?"} → ${tr.pod || "?"}`);
        setText("qs-mode", tr.mode || "—");
        setText("qs-route", `${tr.pol || "?"} → ${tr.pod || "?"}`);
        setText("qs-cargo", cp.cargo_type || "—");
        setText("qs-weight-vol", `${cp.gross_weight_kg || "?"} kg / ${cp.volume_cbm || "?"} CBM`);
    }

    function setText(id, value) {
        const el = document.getElementById(id);
        if (el) el.innerText = value;
    }

    /* -------------------------------------------------------
     * MAIN SECTIONS
     * ------------------------------------------------------- */
    function renderSections(state) {
        const root = document.getElementById("summarySectionsRoot");
        if (!root) return;

        root.innerHTML = `
            ${sectionTradeRoute(state)}
            ${sectionCargoPacking(state)}
            ${sectionSeller(state)}
            ${sectionBuyer(state)}
            ${sectionRiskModules(state)}
        `;
    }

    /* -------------------------------------------------------
     * SECTION 01 – TRADE & ROUTE
     * ------------------------------------------------------- */
    function sectionTradeRoute(s) {
        const tr = (s && s.trade_route) || {};
        return `
        <div id="section-trade-route" class="glass-panel">
            <div class="section-header">
                <div class="section-title">
                    <div class="section-icon">🌍</div>
                    <h2>01 • Trade & Route</h2>
                </div>
                <span class="section-badge">ROUTE</span>
            </div>

            <div class="input-row two-col">
                ${input("Trade Lane", "trade_route.pol", tr.pol, true)}
                ${input("Destination (POD)", "trade_route.pod", tr.pod, true)}
            </div>

            <div class="input-row three-col">
                ${select("Mode", "trade_route.mode", tr.mode, ["SEA","AIR","RAIL","TRUCK"], true)}
                ${input("ETD", "trade_route.etd", tr.etd, true, "date")}
                ${input("Transit Time (days)", "trade_route.transit_time", tr.transit_time, true, "number")}
            </div>

            <div class="input-row three-col">
                ${input("ETA (auto)", "trade_route.eta", tr.eta, false)}
                ${input("Service Route ID", "trade_route.service_route", tr.service_route, false)}
                ${input("Carrier", "trade_route.carrier", tr.carrier, false)}
            </div>

            <div class="input-row two-col">
                ${select("Container Type", "trade_route.container_type", tr.container_type, ["20GP","40GP","40HC","45HC","REEFER"], true)}
                ${select("Priority", "trade_route.priority", tr.priority, ["Fastest","Balanced","Cheapest","Most Reliable"], true)}
            </div>
        </div>`;
    }

    /* -------------------------------------------------------
     * SECTION 02 – CARGO & PACKING
     * ------------------------------------------------------- */
    function sectionCargoPacking(s) {
        const cp = (s && s.cargo_packing) || {};
        return `
        <div id="section-cargo-packing" class="glass-panel">
            <div class="section-header">
                <div class="section-title">
                    <div class="section-icon">📦</div>
                    <h2>02 • Cargo & Packing</h2>
                </div>
                <span class="section-badge">CARGO</span>
            </div>

            <div class="input-row three-col">
                ${input("Cargo Type", "cargo_packing.cargo_type", cp.cargo_type, true)}
                ${input("HS Code", "cargo_packing.hs_code", cp.hs_code, true)}
                ${select("Dangerous Goods", "cargo_packing.dangerous_goods", cp.dangerous_goods, ["No","Yes"], true)}
            </div>

            <div class="input-row three-col">
                ${select("Packing Type", "cargo_packing.packing_type", cp.packing_type, true)}
                ${input("Packages", "cargo_packing.packages", cp.packages, true, "number")}
                ${select("Stackability", "cargo_packing.stackability", cp.stackability, ["Yes","No"], true)}
            </div>

            <div class="input-row three-col">
                ${input("Gross Weight (kg)", "cargo_packing.gross_weight_kg", cp.gross_weight_kg, true, "number")}
                ${input("Net Weight (kg)", "cargo_packing.net_weight_kg", cp.net_weight_kg, false, "number")}
                ${input("Volume (CBM)", "cargo_packing.volume_cbm", cp.volume_cbm, true, "number")}
            </div>

            <div class="input-row full-width">
                ${textarea("Cargo Description", "cargo_packing.cargo_desc", cp.cargo_desc)}
            </div>
        </div>`;
    }

    /* -------------------------------------------------------
     * SECTION 03 – SELLER
     * ------------------------------------------------------- */
    function sectionSeller(s) {
        const seller = (s && s.seller) || {};
        return `
        <div id="section-seller" class="glass-panel">
            <div class="section-header">
                <div class="section-title">
                    <div class="section-icon">🏢</div>
                    <h2>03 • Seller Details</h2>
                </div>
                <span class="section-badge">EXPORTER</span>
            </div>

            <div class="input-row two-col">
                ${input("Company Name", "seller.company", seller.company, true)}
                ${input("Business Type", "seller.business_type", seller.business_type, true)}
            </div>

            <div class="input-row three-col">
                ${input("Country", "seller.country", seller.country, true)}
                ${input("City", "seller.city", seller.city, false)}
                ${input("Tax ID / VAT", "seller.tax_id", seller.tax_id, false)}
            </div>

            ${textarea("Address", "seller.address", seller.address)}

            <div class="input-row three-col">
                ${input("Contact Person", "seller.contact_person", seller.contact_person, true)}
                ${input("Role", "seller.contact_role", seller.contact_role, true)}
                ${input("Email", "seller.email", seller.email, true)}
            </div>

            <div class="input-row two-col">
                ${input("Phone", "seller.phone", seller.phone, true)}
            </div>
        </div>`;
    }

    /* -------------------------------------------------------
     * SECTION 04 – BUYER
     * ------------------------------------------------------- */
    function sectionBuyer(s) {
        const buyer = (s && s.buyer) || {};
        return `
        <div id="section-buyer" class="glass-panel">
            <div class="section-header">
                <div class="section-title">
                    <div class="section-icon">🏬</div>
                    <h2>04 • Buyer Details</h2>
                </div>
                <span class="section-badge">IMPORTER</span>
            </div>

            <div class="input-row two-col">
                ${input("Company Name", "buyer.company", buyer.company, true)}
                ${input("Business Type", "buyer.business_type", buyer.business_type, true)}
            </div>

            <div class="input-row three-col">
                ${input("Country", "buyer.country", buyer.country, true)}
                ${input("City", "buyer.city", buyer.city, false)}
                ${input("Tax ID / VAT", "buyer.tax_id", buyer.tax_id, false)}
            </div>

            ${textarea("Address", "buyer.address", buyer.address)}

            <div class="input-row three-col">
                ${input("Contact Person", "buyer.contact_person", buyer.contact_person, true)}
                ${input("Role", "buyer.contact_role", buyer.contact_role, true)}
                ${input("Email", "buyer.email", buyer.email, true)}
            </div>

            <div class="input-row two-col">
                ${input("Phone", "buyer.phone", buyer.phone, true)}
            </div>
        </div>`;
    }

    /* -------------------------------------------------------
     * SECTION 05 – RISK MODULES
     * ------------------------------------------------------- */
    function sectionRiskModules(s) {
        const rm = (s && s.risk_modules) || {};
        return `
        <div id="section-risk-modules" class="glass-panel">
            <div class="section-header">
                <div class="section-title">
                    <div class="section-icon">⚠️</div>
                    <h2>05 • Risk Analysis Modules</h2>
                </div>
                <span class="section-badge">RISK</span>
            </div>

            <div class="card-grid">
                ${riskModuleCard("ESG Risk", "risk_modules.esg", rm.esg)}
                ${riskModuleCard("Weather & Climate", "risk_modules.weather", rm.weather)}
                ${riskModuleCard("Port Congestion", "risk_modules.congestion", rm.congestion)}
                ${riskModuleCard("Carrier Performance", "risk_modules.carrier_perf", rm.carrier_perf)}
                ${riskModuleCard("Market Condition", "risk_modules.market", rm.market)}
                ${riskModuleCard("Insurance Optimization", "risk_modules.insurance", rm.insurance)}
            </div>
        </div>`;
    }

    /* -------------------------------------------------------
     * UI COMPONENT GENERATORS
     * ------------------------------------------------------- */
    function input(label, field, value, required = false, type = "text") {
        return `
        <div class="input-group">
            <label class="input-label">${label}${required ? '<span class="required-star">*</span>' : ''}</label>
            <input type="${type}" data-field="${field}" class="input-field" value="${value || ""}" />
        </div>`;
    }

    function select(label, field, value, options = [], required = false) {
        const list = Array.isArray(options) ? options : [];
        return `
        <div class="input-group">
            <label class="input-label">${label}${required ? '<span class="required-star">*</span>' : ''}</label>
            <select data-field="${field}" class="input-field">
                ${list.map(o => `<option value="${o}" ${o == value ? "selected" : ""}>${o}</option>`).join("")}
            </select>
        </div>`;
    }

    function textarea(label, field, value) {
        return `
        <div class="input-group full-width">
            <label class="input-label">${label}</label>
            <textarea data-field="${field}" class="textarea-field" rows="3">${value || ""}</textarea>
        </div>`;
    }

    function riskModuleCard(title, field, enabled) {
        const activeClass = enabled ? "badge-good" : "badge-warn";

        return `
        <div class="info-card">
            <div class="info-card-title">${title}</div>
            <div class="info-card-value">
                ${enabled ? "Enabled" : "Disabled"}
                <span class="badge ${activeClass}">${enabled ? "ON" : "OFF"}</span>
            </div>
            <select data-field="${field}" class="input-field" style="margin-top:12px;">
                <option value="true" ${enabled ? "selected" : ""}>Enable</option>
                <option value="false" ${!enabled ? "selected" : ""}>Disable</option>
            </select>
        </div>`;
    }

    /* -------------------------------------------------------
     * PUBLIC API
     * ------------------------------------------------------- */
    return {
        renderAll,
        renderQuickSummary
    };

})();

window.Renderer = Renderer;
console.log("[Renderer] Module loaded ✓");
