
(function() {
    'use strict';

    // SVG Icons (3D Isometric Style)
    const icons = {
        route: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
        </svg>`,
        transport: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M1 3H15L18 12H23L21 19H3L1 12V3Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
            <circle cx="6" cy="19" r="2" stroke="currentColor" stroke-width="2"/>
            <circle cx="18" cy="19" r="2" stroke="currentColor" stroke-width="2"/>
        </svg>`,
        port: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M3 21L21 21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path d="M5 21L5 8L12 3L19 8L19 21" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
            <path d="M9 21L9 12L12 10L15 12L15 21" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
        </svg>`,
        distance: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <path d="M12 2L12 12L20 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>`,
        time: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <path d="M12 6V12L16 14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>`,
        cargo: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="8" width="18" height="12" rx="2" stroke="currentColor" stroke-width="2"/>
            <path d="M3 10C3 8.89543 3.89543 8 5 8H19C20.1046 8 21 8.89543 21 10V12H3V10Z" stroke="currentColor" stroke-width="2"/>
            <path d="M7 8V6C7 4.89543 7.89543 4 9 4H15C16.1046 4 17 4.89543 17 6V8" stroke="currentColor" stroke-width="2"/>
        </svg>`,
        container: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="2" y="6" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
            <path d="M2 10H22" stroke="currentColor" stroke-width="2"/>
            <path d="M8 6V4C8 2.89543 8.89543 2 10 2H14C15.1046 2 16 2.89543 16 4V6" stroke="currentColor" stroke-width="2"/>
        </svg>`,
        package: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
        </svg>`,
        value: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
        </svg>`,
        calendar: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="4" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
            <path d="M16 2V6M8 2V6M3 10H21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>`,
        party: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M17 21V19C17 17.9391 16.5786 16.9217 15.8284 16.1716C15.0783 15.4214 14.0609 15 13 15H5C3.93913 15 2.92172 15.4214 2.17157 16.1716C1.42143 16.9217 1 17.9391 1 19V21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="9" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
            <path d="M23 21V19C22.9993 18.1137 22.7044 17.2528 22.1614 16.5523C21.6184 15.8519 20.8581 15.3516 20 15.13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M16 3.13C16.8604 3.35031 17.623 3.85071 18.1676 4.55232C18.7122 5.25392 19.0078 6.11683 19.0078 7.005C19.0078 7.89318 18.7122 8.75608 18.1676 9.45769C17.623 10.1593 16.8604 10.6597 16 10.88" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>`,
        weather: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2V4M12 20V22M4 12H2M6.31412 6.31412L4.8999 4.8999M17.6859 6.31412L19.1001 4.8999M6.31412 17.69L4.8999 19.1042M17.6859 17.69L19.1001 19.1042M22 12H20M17 12C17 14.7614 14.7614 17 12 17C9.23858 17 7 14.7614 7 12C7 9.23858 9.23858 7 12 7C14.7614 7 17 9.23858 17 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>`,
        esg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
            <path d="M12 6V12L16 14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>`,
        risk: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
        </svg>`
    };

    /**
     * Get data from form or results
     */
    function getBookingData() {
        // Try to get data from multiple sources
        const formData = JSON.parse(localStorage.getItem('riskcast_form_data') || '{}');
        const resultsData = window.riskcastResults || {};
        const appData = window.appData || {};
        
        // Extract from appData if available (from results_core.js)
        const inputData = appData.input || {};
        
        // Merge data sources (priority: appData > resultsData > formData)
        return {
            route: inputData.route || formData.route || resultsData.route || 'vn_us',
            transportMode: inputData.transport_mode || formData.transport_mode || resultsData.transport_mode || 'ocean_fcl',
            pol: inputData.pol || formData.pol || resultsData.pol || 'Cái Mép - Thị Vải',
            polCode: inputData.pol_code || formData.pol_code || resultsData.pol_code || 'CMP',
            pod: inputData.pod || formData.pod || resultsData.pod || 'Long Beach',
            podCode: inputData.pod_code || formData.pod_code || resultsData.pod_code || 'USLGB',
            distance: inputData.distance || formData.distance || resultsData.distance || appData.distance || 12600,
            transitTime: inputData.transit_time || formData.transit_time || resultsData.transit_time || appData.transit_time || 18,
            cargoType: inputData.cargo_type || formData.cargo_type || resultsData.cargo_type || 'electronics',
            containerType: inputData.container_type || formData.container_type || resultsData.container_type || '40ft',
            incoterm: inputData.incoterm || formData.incoterm || resultsData.incoterm || 'FAS',
            packaging: inputData.packaging || formData.packaging || resultsData.packaging || 'Standard',
            containerMatch: inputData.container_match || formData.container_match || resultsData.container_match || appData.container_match || 9.8,
            carrier: inputData.carrier || formData.carrier || resultsData.carrier || 'MSC',
            carrierRating: inputData.carrier_rating || formData.carrier_rating || resultsData.carrier_rating || 3.0,
            carrierComment: inputData.carrier_comment || formData.carrier_comment || resultsData.carrier_comment || 'Giá cạnh tranh, nhiều chuyến',
            packages: inputData.packages || formData.packages || resultsData.packages || 500,
            cargoValue: inputData.cargo_value || formData.cargo_value || resultsData.cargo_value || 250000,
            etd: inputData.etd || formData.etd || resultsData.etd || '2025-11-26',
            eta: inputData.eta || formData.eta || resultsData.eta || '2025-12-04',
            seller: inputData.seller || formData.seller || resultsData.seller || 'Người bán 5',
            buyer: inputData.buyer || formData.buyer || resultsData.buyer || 'Người mua 55',
            enso: inputData.enso || formData.enso || resultsData.enso || appData.enso || 'La Niña',
            storms: inputData.storms || formData.storms || resultsData.storms || appData.storms || 3,
            climatePressure: inputData.climate_pressure || formData.climate_pressure || resultsData.climate_pressure || appData.climate_pressure || 8.7,
            esgScore: inputData.esg_score || formData.esg_score || resultsData.esg_score || appData.esg_score || 69,
            riskScore: appData.overall_risk || formData.risk_score || resultsData.risk_score || 72
        };
    }

    /**
     * Format date
     */
    function formatDate(dateString) {
        if (!dateString) return '--';
        const date = new Date(dateString);
        return date.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
    }

    /**
     * Generate star rating HTML
     */
    function generateStars(rating) {
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 >= 0.5;
        let html = '';
        
        for (let i = 0; i < 5; i++) {
            if (i < fullStars) {
                html += '<svg class="star" viewBox="0 0 24 24"><path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" fill="currentColor"/></svg>';
            } else if (i === fullStars && hasHalfStar) {
                html += '<svg class="star" viewBox="0 0 24 24"><path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" fill="currentColor" opacity="0.5"/></svg>';
            } else {
                html += '<svg class="star empty" viewBox="0 0 24 24"><path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" fill="currentColor"/></svg>';
            }
        }
        return html;
    }

    /**
     * Calculate transit time in days
     */
    function calculateTransitDays(etd, eta) {
        if (!etd || !eta) return 8;
        const start = new Date(etd);
        const end = new Date(eta);
        const diffTime = Math.abs(end - start);
        return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    }

    /**
     * Render risk score circular progress
     */
    function renderRiskScore(score) {
        const radius = 90;
        const circumference = 2 * Math.PI * radius;
        const offset = circumference - (score / 100) * circumference;
        
        return `
            <div class="risk-score-ring">
                <svg class="risk-score-svg" viewBox="0 0 200 200">
                    <defs>
                        <linearGradient id="emeraldGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:#10B981;stop-opacity:1" />
                            <stop offset="100%" style="stop-color:#34D399;stop-opacity:1" />
                        </linearGradient>
                    </defs>
                    <circle class="risk-score-circle-bg" cx="100" cy="100" r="${radius}"/>
                    <circle class="risk-score-circle-progress" cx="100" cy="100" r="${radius}" 
                            stroke-dasharray="${circumference}" 
                            stroke-dashoffset="${offset}"/>
                </svg>
                <div class="risk-score-value">${score}</div>
            </div>
            <div class="risk-score-label">Overall Risk Score</div>
        `;
    }

    /**
     * Populate dashboard with data
     */
    function populateDashboard() {
        const data = getBookingData();
        const dashboard = document.getElementById('booking-summary-dashboard');
        
        if (!dashboard) {
            // Silently skip - element only exists on results page, not input page
            // This is normal behavior when script is loaded on input.html
            return;
        }

        // Get logistics data
        const logisticsData = window.LOGISTICS_DATA || {};
        const routeData = logisticsData.getRoute ? logisticsData.getRoute(data.route) : null;
        
        // Calculate transit days
        const transitDays = calculateTransitDays(data.etd, data.eta);

        // Populate sections
        populateTransportOverview(dashboard, data, routeData);
        populateCargoDetails(dashboard, data);
        populateCarrier(dashboard, data);
        populateMilestones(dashboard, data, transitDays);
        populateParties(dashboard, data);
        populateWeatherESG(dashboard, data);
        populateRiskScore(dashboard, data);
    }

    function populateTransportOverview(dashboard, data, routeData) {
        const section = dashboard.querySelector('.transport-overview-section');
        if (!section) return;

        const grid = section.querySelector('.transport-overview-grid');
        if (!grid) return;

        const routeName = routeData?.name_vi || data.route;
        const transportModeLabel = getTransportModeLabel(data.transportMode);

        grid.innerHTML = `
            <div class="booking-summary-card">
                <div class="card-icon-wrapper">${icons.route}</div>
                <div class="card-content-wrapper">
                    <div class="card-label">Tuyến Đường</div>
                    <div class="card-value">${routeName}</div>
                </div>
            </div>
            <div class="booking-summary-card">
                <div class="card-icon-wrapper">${icons.transport}</div>
                <div class="card-content-wrapper">
                    <div class="card-label">Phương Thức</div>
                    <div class="card-value">${transportModeLabel}</div>
                </div>
            </div>
            <div class="booking-summary-card">
                <div class="card-icon-wrapper">${icons.port}</div>
                <div class="card-content-wrapper">
                    <div class="card-label">POL / POD</div>
                    <div class="card-value">${data.polCode} → ${data.podCode}</div>
                    <div class="card-note">${data.pol} → ${data.pod}</div>
                </div>
            </div>
            <div class="booking-summary-card">
                <div class="card-icon-wrapper">${icons.distance}</div>
                <div class="card-content-wrapper">
                    <div class="card-label">Khoảng Cách</div>
                    <div class="card-value">${data.distance.toLocaleString()} km</div>
                </div>
            </div>
            <div class="booking-summary-card">
                <div class="card-icon-wrapper">${icons.time}</div>
                <div class="card-content-wrapper">
                    <div class="card-label">Thời Gian</div>
                    <div class="card-value">${data.transitTime} ngày</div>
                </div>
            </div>
        `;
    }

    function populateCargoDetails(dashboard, data) {
        const section = dashboard.querySelector('.cargo-details-section');
        if (!section) return;

        const grid = section.querySelector('.cargo-details-grid');
        if (!grid) return;

        const cargoTypeLabel = getCargoTypeLabel(data.cargoType);
        const containerTypeLabel = getContainerTypeLabel(data.containerType);

        grid.innerHTML = `
            <div class="booking-summary-card">
                <div class="card-icon-wrapper">${icons.cargo}</div>
                <div class="card-content-wrapper">
                    <div class="card-label">Loại Hàng</div>
                    <div class="card-value">${cargoTypeLabel}</div>
                </div>
            </div>
            <div class="booking-summary-card">
                <div class="card-icon-wrapper">${icons.container}</div>
                <div class="card-content-wrapper">
                    <div class="card-label">Loại Container</div>
                    <div class="card-value">${containerTypeLabel}</div>
                </div>
            </div>
            <div class="booking-summary-card">
                <div class="card-icon-wrapper">${icons.package}</div>
                <div class="card-content-wrapper">
                    <div class="card-label">Incoterm</div>
                    <div class="card-value">${data.incoterm}</div>
                </div>
            </div>
            <div class="booking-summary-card">
                <div class="card-icon-wrapper">${icons.package}</div>
                <div class="card-content-wrapper">
                    <div class="card-label">Chất Lượng Đóng Gói</div>
                    <div class="card-value">${data.packaging}</div>
                </div>
            </div>
            <div class="booking-summary-card active">
                <div class="card-icon-wrapper">${icons.container}</div>
                <div class="card-content-wrapper">
                    <div class="card-label">Độ Phù Hợp Container</div>
                    <div class="card-value highlight">${data.containerMatch % 1 === 0 ? data.containerMatch.toFixed(0) : data.containerMatch.toFixed(1)}/10</div>
                </div>
            </div>
        `;
    }

    function populateCarrier(dashboard, data) {
        const section = dashboard.querySelector('.carrier-section');
        if (!section) return;

        const container = section.querySelector('.carrier-container');
        if (!container) return;

        container.innerHTML = `
            <div class="carrier-card">
                <div class="carrier-logo">${data.carrier.substring(0, 2)}</div>
                <div class="carrier-info">
                    <div class="carrier-name">${data.carrier}</div>
                    <div class="carrier-rating">
                        <div class="star-rating">${generateStars(data.carrierRating)}</div>
                        <span class="rating-value">${data.carrierRating.toFixed(1)}</span>
                    </div>
                    <div class="carrier-comment">${data.carrierComment}</div>
                </div>
            </div>
        `;
    }

    function populateMilestones(dashboard, data, transitDays) {
        const section = dashboard.querySelector('.milestones-section');
        if (!section) return;

        const grid = section.querySelector('.milestones-grid');
        if (!grid) return;

        grid.innerHTML = `
            <div class="booking-summary-card">
                <div class="card-icon-wrapper">${icons.package}</div>
                <div class="card-content-wrapper">
                    <div class="card-label">Số Lượng Kiện</div>
                    <div class="card-value">${data.packages.toLocaleString()}</div>
                </div>
            </div>
            <div class="booking-summary-card">
                <div class="card-icon-wrapper">${icons.value}</div>
                <div class="card-content-wrapper">
                    <div class="card-label">Giá Trị Hàng</div>
                    <div class="card-value">$${data.cargoValue.toLocaleString()}</div>
                </div>
            </div>
            <div class="booking-summary-card">
                <div class="card-icon-wrapper">${icons.calendar}</div>
                <div class="card-content-wrapper">
                    <div class="card-label">ETD</div>
                    <div class="card-value">${formatDate(data.etd)}</div>
                </div>
            </div>
            <div class="booking-summary-card">
                <div class="card-icon-wrapper">${icons.calendar}</div>
                <div class="card-content-wrapper">
                    <div class="card-label">ETA</div>
                    <div class="card-value">${formatDate(data.eta)}</div>
                </div>
            </div>
            <div class="booking-summary-card active">
                <div class="card-icon-wrapper">${icons.time}</div>
                <div class="card-content-wrapper">
                    <div class="card-label">Transit Time</div>
                    <div class="card-value large highlight transit-time-highlight">${transitDays} ngày</div>
                </div>
            </div>
        `;
    }

    function populateParties(dashboard, data) {
        const section = dashboard.querySelector('.parties-section');
        if (!section) return;

        const grid = section.querySelector('.parties-grid');
        if (!grid) return;

        grid.innerHTML = `
            <div class="booking-summary-card">
                <div class="card-icon-wrapper">${icons.party}</div>
                <div class="card-content-wrapper">
                    <div class="card-label">Người Bán</div>
                    <div class="card-value">${data.seller}</div>
                </div>
            </div>
            <div class="booking-summary-card">
                <div class="card-icon-wrapper">${icons.party}</div>
                <div class="card-content-wrapper">
                    <div class="card-label">Người Mua</div>
                    <div class="card-value">${data.buyer}</div>
                </div>
            </div>
        `;
    }

    function populateWeatherESG(dashboard, data) {
        const section = dashboard.querySelector('.weather-esg-section');
        if (!section) return;

        const grid = section.querySelector('.weather-esg-grid');
        if (!grid) return;

        grid.innerHTML = `
            <div class="booking-summary-card">
                <div class="card-icon-wrapper">${icons.weather}</div>
                <div class="card-content-wrapper">
                    <div class="card-label">ENSO</div>
                    <div class="card-value">${data.enso}</div>
                </div>
            </div>
            <div class="booking-summary-card">
                <div class="card-icon-wrapper">${icons.weather}</div>
                <div class="card-content-wrapper">
                    <div class="card-label">Dự Báo Bão</div>
                    <div class="card-value">${data.storms} storms</div>
                </div>
            </div>
            <div class="booking-summary-card">
                <div class="card-icon-wrapper">${icons.weather}</div>
                <div class="card-content-wrapper">
                    <div class="card-label">Climate Pressure</div>
                    <div class="card-value">${data.climatePressure}/10</div>
                </div>
            </div>
            <div class="booking-summary-card">
                <div class="card-icon-wrapper">${icons.esg}</div>
                <div class="card-content-wrapper">
                    <div class="card-label">ESG Score</div>
                    <div class="card-value highlight">${data.esgScore}/100</div>
                </div>
            </div>
        `;
    }

    function populateRiskScore(dashboard, data) {
        const section = dashboard.querySelector('.risk-score-section');
        if (!section) return;

        const container = section.querySelector('.risk-score-container');
        if (!container) return;

        container.innerHTML = renderRiskScore(data.riskScore);
        
        // Animate progress
        setTimeout(() => {
            const progressCircle = container.querySelector('.risk-score-circle-progress');
            if (progressCircle) {
                progressCircle.style.transition = 'stroke-dashoffset 1.5s cubic-bezier(0.4, 0, 0.2, 1)';
            }
        }, 100);
    }

    // Helper functions
    function getTransportModeLabel(mode) {
        const labels = {
            'ocean_fcl': 'Đường Biển — FCL',
            'ocean_lcl': 'Đường Biển — LCL',
            'air_general': 'Hàng Không',
            'road_ftl': 'Đường Bộ — FTL',
            'rail_container': 'Đường Sắt'
        };
        return labels[mode] || mode;
    }

    function getCargoTypeLabel(type) {
        const labels = {
            'electronics': 'Điện Tử',
            'general': 'Thông Thường',
            'food_bev': 'Thực Phẩm & Đồ Uống',
            'garments': 'May Mặc',
            'machinery': 'Máy Móc'
        };
        return labels[type] || type;
    }

    function getContainerTypeLabel(type) {
        const labels = {
            '20ft': '20ft Standard',
            '40ft': '40ft Standard',
            '40hc': '40ft High Cube',
            'reefer': 'Reefer'
        };
        return labels[type] || type;
    }

    // Initialize when DOM is ready
    function initDashboard() {
        // Wait a bit for appData to be available
        if (window.appData) {
            populateDashboard();
        } else {
            // Retry after a short delay
            setTimeout(() => {
                populateDashboard();
            }, 1000);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDashboard);
    } else {
        initDashboard();
    }

    // Re-populate when data changes
    window.addEventListener('riskcastDataUpdated', populateDashboard);
    
    // Watch for appData updates using MutationObserver or polling
    let lastAppData = null;
    setInterval(() => {
        if (window.appData && window.appData !== lastAppData) {
            lastAppData = window.appData;
            populateDashboard();
        }
    }, 500);

    // Export for external use
    window.BookingSummary = {
        populate: populateDashboard,
        getData: getBookingData
    };

})();

