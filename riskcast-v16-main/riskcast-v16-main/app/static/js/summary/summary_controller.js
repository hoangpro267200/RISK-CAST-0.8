/**
 * ==========================================================
 * SUMMARY_CONTROLLER_V100.JS
 * RISKCAST FutureOS v100 – Page Orchestration
 * ==========================================================
 *
 * Điều phối toàn bộ luồng:
 * - Load state từ localStorage
 * - Init SmartEditor
 * - Init Validator + Renderer
 * - Handle buttons (Back, Confirm)
 * - Auto-scroll navigation
 * - Mini toast UI
 */

const SummaryController = (() => {
    "use strict";

    /* ---------------------------------------------
     * INIT SUMMARY PAGE
     * --------------------------------------------- */
    async function init() {
        console.log("%c[SummaryController] Initializing…", "color:#00ffff");

        // 1) Load state từ localStorage
        const ok = StateSync.init();
        if (!ok) console.warn("[SummaryController] No state found!");

        // 2) Load dataset expert
        try {
            await DatasetLoader.init();
        } catch (e) {
            console.warn("[SummaryController] Dataset load error", e);
        }

        // 3) Init SmartEditor (non-blocking)
        try {
            SmartEditor.init();
        } catch (e) {
            console.warn("[SummaryController] SmartEditor init skipped", e);
        }

        // 4) Initial validation
        try {
            Validator.init();
        } catch (e) {
            console.warn("[SummaryController] Validator init skipped", e);
        }

        // 5) Initial render (with safe fallback state)
        const state =
            StateSync.getState() || {
                trade_route: {},
                cargo_packing: {},
                seller: {},
                buyer: {},
                risk_modules: {},
            };
        Renderer.renderAll(state);

        // 6) Bind buttons
        initActionButtons();

        // 7) Bind navigation on left
        initNavigation();

        console.log("%c[SummaryController] Ready ✓", "color:#00ff88");
    }

    /* ---------------------------------------------
     * BUTTON HANDLERS
     * --------------------------------------------- */
    function initActionButtons() {
        // Back → Input
        const backBtn = document.getElementById("backToInputBtn");
        if (backBtn) {
            backBtn.addEventListener("click", () => {
                window.location.href = "/input";
            });
        }

        // Confirm → Results
        const confirmBtn = document.getElementById("confirmToResultsBtn");
        if (confirmBtn) {
            confirmBtn.addEventListener("click", () => {
                handleConfirm();
            });
        }
    }

    /* ---------------------------------------------
     * CONFIRM → SAVE STATE → GO TO RESULTS
     * --------------------------------------------- */
    function handleConfirm() {
        const state = StateSync.getState();

        // Basic confirmation validation
        const issues = Validator.getIssues();
        if (issues.errors && issues.errors.length > 0) {
            showToast(
                "Cannot proceed — fix required errors first.",
                "error"
            );
            return;
        }

        // Save to localStorage again
        StateSync.saveState();

        showToast("Summary confirmed! Redirecting…", "success");

        setTimeout(() => {
            window.location.href = "/results";
        }, 650);
    }

    /* ---------------------------------------------
     * SIDE NAVIGATION (LEFT)
     * --------------------------------------------- */
    function initNavigation() {
        const items = document.querySelectorAll(".summary-nav .nav-item");

        items.forEach((item) => {
            item.addEventListener("click", () => {
                const target = item.getAttribute("data-target");
                activateSection(item, target);
            });
        });
    }

    function activateSection(navItem, targetId) {
        // Remove active class
        document.querySelectorAll(".summary-nav .nav-item")
            .forEach((i) => i.classList.remove("active"));

        navItem.classList.add("active");

        // Scroll to section
        const section = document.getElementById(targetId);
        if (section) {
            section.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

            section.classList.add("field-impact");
            setTimeout(() => section.classList.remove("field-impact"), 600);
        }
    }

    /* ---------------------------------------------
     * MINI TOAST UI
     * --------------------------------------------- */
    function showToast(message, type = "info") {
        const toast = document.createElement("div");
        toast.className = `mini-toast mini-toast-${type}`;
        toast.innerText = message;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.classList.add("show");
        }, 10);

        setTimeout(() => {
            toast.classList.remove("show");
            setTimeout(() => toast.remove(), 300);
        }, 2300);
    }

    /* ---------------------------------------------
     * PUBLIC API
     * --------------------------------------------- */
    return {
        init
    };

})();

window.SummaryController = SummaryController;

/* ---------------------------------------------
 * BOOTSTRAP
 * --------------------------------------------- */
document.addEventListener("DOMContentLoaded", () => {
    SummaryController.init();
});
