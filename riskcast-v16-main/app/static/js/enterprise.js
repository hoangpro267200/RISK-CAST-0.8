// ===============================================================
// KPI handler • Chart Render • Auto-update
// Author: Kai × Hoàng
// ===============================================================

// ------------- GLOBAL DATA CACHE -------------
let riskData = null;

// ------------- DOM HELPERS -------------
function $(id) {
    return document.getElementById(id);
}

// ------------- UPDATE KPI CARDS -------------
function updateKPIs(data) {
    $("kpi_overall_value").innerText = data.overall_risk.toFixed(2);
    $("kpi_cost_value").innerText = "$" + data.expected_loss.toLocaleString();
    $("kpi_delay_value").innerText = (data.delay_prob * 100).toFixed(1) + "%";
}

// ------------- RADAR CHART -------------
function drawRadarChart(data) {
    const factors = data.risk_factors;
    const scores = factors.map(f => f.score);

    const trace = {
        type: "scatterpolar",
        r: scores,
        theta: factors.map(f => f.name),
        fill: "toself"
    };

    Plotly.newPlot("radar_chart", [trace], {
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        polar: { radialaxis: { visible: true, range: [0, 10] } }
    });
}

// ------------- BAR CHART -------------
function drawBarChart(data) {
    const factors = data.risk_factors;

    const trace = {
        x: factors.map(f => f.name),
        y: factors.map(f => f.score),
        type: "bar"
    };

    Plotly.newPlot("bar_chart", [trace], {
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)"
    });
}

// ------------- FORECAST CHART -------------
function drawForecast(data) {
    Plotly.newPlot("forecast_chart", [{
        x: data.forecast.days,
        y: data.forecast.values,
        type: "scatter",
        line: { width: 2 }
    }], {
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)"
    });
}

// ------------- MAIN LOAD FUNCTION -------------
function loadEnterprise(data) {
    riskData = data;

    updateKPIs(data);
    drawRadarChart(data);
    drawBarChart(data);
    drawForecast(data);
}

// ------------- RUN BUTTON HANDLER -------------
async function runEnterprise() {
    window.location.href = "/input";
}

window.runEnterprise = runEnterprise;
