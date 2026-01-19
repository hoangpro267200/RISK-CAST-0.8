
(function() {
    'use strict';

    // ============================================================
    // INITIALIZATION
    // ============================================================
    document.addEventListener('DOMContentLoaded', function() {
        initParticles();
        initSidebar();
        initSearch();
        initQuickActions();
        initPerformanceChart();
        initActivityControls();
        initCircularProgress();
        initProgressBars();
        
        // Load data from analysis result
        loadAnalysisData();
    });

    // ============================================================
    // PARTICLES ANIMATION
    // ============================================================
    function initParticles() {
        const container = document.querySelector('.particles-container');
        if (!container) return;

        const particleCount = 20;
        const particles = [];

        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            const size = Math.random() * 4 + 4; // 4px to 8px
            const sizeClass = size < 5 ? 'particle--small' : 
                             size < 7 ? 'particle--medium' : 'particle--large';
            
            particle.className = `particle ${sizeClass}`;
            if (Math.random() > 0.7) {
                particle.classList.add('particle--glow');
            }

            // Random starting position
            particle.style.left = Math.random() * 100 + '%';
            particle.style.top = Math.random() * 100 + '%';
            particle.style.animationDelay = Math.random() * 20 + 's';
            particle.style.animationDuration = (Math.random() * 10 + 15) + 's';

            container.appendChild(particle);
            particles.push(particle);
        }
    }

    // ============================================================
    // SIDEBAR INTERACTIONS
    // ============================================================
    function initSidebar() {
        const menuItems = document.querySelectorAll('.sidebar__menu-item');
        const currentPath = window.location.pathname;

        // Set active menu item based on current route
        menuItems.forEach(item => {
            const href = item.getAttribute('href');
            if (href && currentPath.includes(href.replace('/', ''))) {
                item.classList.add('sidebar__menu-item--active');
            }

            // Add click handler
            item.addEventListener('click', function(e) {
                if (href && href !== '#') {
                    // Remove active from all items
                    menuItems.forEach(mi => mi.classList.remove('sidebar__menu-item--active'));
                    // Add active to clicked item
                    this.classList.add('sidebar__menu-item--active');
                }
            });
        });

        // Mobile sidebar toggle
        if (window.innerWidth <= 768) {
            const sidebar = document.querySelector('.sidebar');
            const overlay = document.createElement('div');
            overlay.className = 'sidebar__overlay';
            document.body.appendChild(overlay);

            overlay.addEventListener('click', function() {
                sidebar.classList.remove('sidebar--open');
                overlay.classList.remove('sidebar__overlay--visible');
            });
        }
    }

    // ============================================================
    // SEARCH FUNCTIONALITY
    // ============================================================
    function initSearch() {
        const searchInput = document.querySelector('.search-bar__input');
        if (!searchInput) return;

        let searchTimeout;
        searchInput.addEventListener('input', function(e) {
            clearTimeout(searchTimeout);
            const query = e.target.value.trim();

            searchTimeout = setTimeout(() => {
                if (query.length > 2) {
                    performSearch(query);
                }
            }, 300);
        });

        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const query = e.target.value.trim();
                if (query) {
                    performSearch(query);
                }
            }
        });
    }

    function performSearch(query) {
        console.log('Searching for:', query);
        // TODO: Implement actual search functionality
        // This could filter shipments, navigate to results, etc.
    }

    // ============================================================
    // QUICK ACTIONS
    // ============================================================
    function initQuickActions() {
        const actions = document.querySelectorAll('.quick-action');
        
        actions.forEach(action => {
            action.addEventListener('click', function() {
                const actionText = this.querySelector('.quick-action__text').textContent;
                
                // Add click animation
                this.style.transform = 'translateY(-2px) scale(0.98)';
                setTimeout(() => {
                    this.style.transform = '';
                }, 200);

                // Handle different actions
                if (actionText.includes('Create')) {
                    window.location.href = '/input';
                } else if (actionText.includes('Track')) {
                    // Open tracking modal or navigate
                    console.log('Track shipment');
                } else if (actionText.includes('Report')) {
                    // Generate report
                    console.log('Generate report');
                }
            });
        });
    }

    // ============================================================
    // PERFORMANCE CHART (Chart.js)
    // ============================================================
    function initPerformanceChart() {
        const chartCanvas = document.getElementById('performanceChart');
        if (!chartCanvas || typeof Chart === 'undefined') {
            console.warn('Chart.js not loaded or canvas not found');
            return;
        }

        const ctx = chartCanvas.getContext('2d');
        
        // Sample data - replace with actual data from API
        const labels = Array.from({ length: 40 }, (_, i) => i);
        const data = Array.from({ length: 40 }, () => Math.random() * 100);

        const gradient = ctx.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, 'rgba(0, 212, 255, 0.8)');
        gradient.addColorStop(1, 'rgba(0, 255, 136, 0.2)');

        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Performance',
                    data: data,
                    borderColor: '#00ff88',
                    backgroundColor: gradient,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: '#00ff88',
                    pointHoverBorderColor: '#ffffff',
                    pointHoverBorderWidth: 2,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(26, 35, 50, 0.95)',
                        borderColor: '#00d4ff',
                        borderWidth: 1,
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        padding: 12,
                        cornerRadius: 8,
                        displayColors: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.5)',
                            font: {
                                size: 11
                            }
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.5)',
                            font: {
                                size: 11
                            },
                            callback: function(value) {
                                return value;
                            }
                        },
                        min: 0,
                        max: 100
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                animation: {
                    duration: 2000,
                    easing: 'easeInOutQuart'
                }
            }
        });

        // Animate chart on load
        setTimeout(() => {
            chart.update('active');
        }, 500);

        // Store chart instance for updates
        window.dashboardChart = chart;
    }

    // ============================================================
    // ACTIVITY CONTROLS
    // ============================================================
    function initActivityControls() {
        const playPauseBtn = document.querySelector('.activity-play-pause');
        const dropdownBtn = document.querySelector('.activity-dropdown');

        if (playPauseBtn) {
            let isPlaying = true;
            playPauseBtn.addEventListener('click', function() {
                isPlaying = !isPlaying;
                this.textContent = isPlaying ? '⏸' : '▶';
                // TODO: Implement play/pause functionality for activity updates
            });
        }

        if (dropdownBtn) {
            dropdownBtn.addEventListener('click', function() {
                // TODO: Implement dropdown menu
                console.log('Activity dropdown clicked');
            });
        }
    }

    // ============================================================
    // CIRCULAR PROGRESS INDICATOR
    // ============================================================
    function initCircularProgress() {
        const progressElements = document.querySelectorAll('.circular-progress');
        
        progressElements.forEach(element => {
            const progress = parseFloat(element.dataset.progress || '75');
            const circle = element.querySelector('.circular-progress__circle-fill');
            const text = element.querySelector('.circular-progress__text');
            
            if (circle && text) {
                const radius = 40;
                const circumference = 2 * Math.PI * radius;
                const offset = circumference - (progress / 100) * circumference;
                
                // Set stroke-dasharray and stroke-dashoffset
                circle.style.strokeDasharray = circumference;
                circle.style.strokeDashoffset = offset;
                text.textContent = Math.round(progress) + '%';
            }
        });
    }

    // ============================================================
    // PROGRESS BARS
    // ============================================================
    function initProgressBars() {
        const progressBars = document.querySelectorAll('.shipment-card__progress-fill');
        
        progressBars.forEach(bar => {
            const progress = parseFloat(bar.dataset.progress || '75');
            bar.style.width = progress + '%';
            
            // Animate on load
            setTimeout(() => {
                bar.style.transition = 'width 1s ease';
            }, 100);
        });
    }

    // ============================================================
    // LOAD ANALYSIS DATA
    // ============================================================
    async function loadAnalysisData() {
        try {
            // Try to get from localStorage first (from input.html)
            let resultData = null;
            const lastResult = localStorage.getItem('last_result');
            
            if (lastResult) {
                try {
                    resultData = JSON.parse(lastResult);
                    console.log('✓ Loaded data from localStorage');
                } catch (e) {
                    console.warn('Failed to parse localStorage data:', e);
                }
            }
            
            // If no localStorage data, try API
            if (!resultData) {
                try {
                    const response = await fetch('/api/get_last_result');
                    if (response.ok) {
                        const apiData = await response.json();
                        if (apiData && !apiData.error) {
                            resultData = apiData;
                            console.log('✓ Loaded data from API');
                        }
                    }
                } catch (e) {
                    console.warn('Failed to fetch from API:', e);
                }
            }
            
            // If we have data, update dashboard
            if (resultData) {
                updateDashboardFromResult(resultData);
            } else {
                console.log('No analysis data found, using default values');
            }
        } catch (error) {
            console.error('Error loading analysis data:', error);
        }
    }

    // ============================================================
    // UPDATE DASHBOARD FROM ANALYSIS RESULT
    // ============================================================
    function updateDashboardFromResult(result) {
        console.log('Updating dashboard with result:', result);
        
        // Extract shipment data (might be in different places)
        const shipment = result.shipment || result.shipment_data || {};
        const route = shipment.route || result.route || '';
        
        // Get origin/destination from shipment data or parse from route
        let origin = shipment.origin || 'LAX';
        let destination = shipment.destination || 'JFK';
        
        // If not in shipment, try to parse from route
        if ((!origin || origin === 'LAX') && route) {
            const routeParts = route.split('_');
            if (routeParts.length >= 2) {
                const originPart = routeParts[0];
                const destPart = routeParts[1];
                
                // Common port mappings
                const portMap = {
                    'VN': 'SGN', 'VNSGN': 'SGN', 'VNHPH': 'HPH',
                    'US': 'LAX', 'USLAX': 'LAX', 'USNYC': 'NYC', 'USJFK': 'JFK',
                    'CN': 'SHA', 'CNSHA': 'SHA', 'CNPEK': 'PEK',
                    'EU': 'DEP', 'EUDEP': 'DEP', 'EULON': 'LON'
                };
                
                origin = portMap[originPart] || originPart.slice(-3) || 'LAX';
                destination = portMap[destPart] || destPart.slice(-3) || 'JFK';
            }
        }
        
        // Ensure 3-letter codes
        if (origin.length > 3) origin = origin.slice(-3);
        if (destination.length > 3) destination = destination.slice(-3);
        
        // Update Shipment Card
        const shipmentId = result.shipment_id || shipment.shipment_id || `FX-${new Date().getFullYear()}-${Math.floor(Math.random() * 1000)}`;
        const eta = shipment.eta || result.eta || new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        
        // Calculate progress (based on delay probability or transit time)
        const delayProb = result.delay_probability || 0;
        const reliability = result.reliability || result.reliability_score || 98;
        const progress = Math.max(0, Math.min(100, reliability)); // Use reliability as progress
        
        // Update shipment fields
        updateElement('[data-field="id"]', shipmentId);
        updateElement('[data-field="origin"]', origin);
        updateElement('[data-field="destination"]', destination);
        updateElement('[data-field="eta"]', eta);
        
        // Update progress bars
        const progressFill = document.querySelector('.shipment-card__progress-fill');
        const progressText = document.querySelector('.shipment-card__progress-label span:last-child');
        const circularProgress = document.querySelector('.circular-progress');
        const circularProgressText = document.querySelector('.circular-progress__text');
        
        if (progressFill) {
            progressFill.style.width = progress + '%';
            progressFill.setAttribute('data-progress', progress);
        }
        if (progressText) {
            progressText.textContent = Math.round(progress) + '%';
        }
        if (circularProgress) {
            circularProgress.setAttribute('data-progress', progress);
            const circle = circularProgress.querySelector('.circular-progress__circle-fill');
            if (circle) {
                const radius = 40;
                const circumference = 2 * Math.PI * radius;
                const offset = circumference - (progress / 100) * circumference;
                circle.style.strokeDasharray = circumference;
                circle.style.strokeDashoffset = offset;
            }
        }
        if (circularProgressText) {
            circularProgressText.textContent = Math.round(progress) + '%';
        }
        
        // Update Stats Cards
        const overallRisk = result.overall_risk || result.risk_score * 100 || 50;
        const expectedLoss = result.expected_loss || result.expected_loss_usd || 0;
        const onTimeRate = reliability;
        const delayedCount = delayProb > 0.1 ? Math.ceil(delayProb * 100) : 0;
        
        // Calculate total shipments (mock for now, could come from API)
        const totalShipments = 1234; // This could be from a separate API call
        
        updateStatsCard(0, totalShipments, '+12% from last month', true);
        updateStatsCard(1, onTimeRate.toFixed(0) + '%', '+2% from last month', true);
        updateStatsCard(2, Math.floor(totalShipments * 0.37), 'No change', false);
        updateStatsCard(3, delayedCount, '-3 from last month', false);
        
        // Update Performance Chart with forecast or MC samples
        if (result.forecast && window.dashboardChart) {
            const forecast = result.forecast;
            const labels = forecast.labels || Array.from({ length: 40 }, (_, i) => i);
            const values = forecast.values || forecast.data || Array.from({ length: 40 }, () => Math.random() * 100);
            
            window.dashboardChart.data.labels = labels;
            window.dashboardChart.data.datasets[0].data = values;
            window.dashboardChart.update();
        } else if (result.mc_samples && window.dashboardChart) {
            // Use MC samples for chart
            const samples = result.mc_samples.slice(0, 40); // Take first 40 samples
            const labels = Array.from({ length: samples.length }, (_, i) => i);
            window.dashboardChart.data.labels = labels;
            window.dashboardChart.data.datasets[0].data = samples.map(s => Math.abs(s) % 100);
            window.dashboardChart.update();
        }
        
        // Update Recent Activity
        const activities = [
            {
                icon: '📦',
                text: `Shipment ${shipmentId} updated - Risk analysis completed`,
                time: 'Just now'
            },
            {
                icon: '📊',
                text: `New tracking info - Overall risk: ${overallRisk.toFixed(1)}%`,
                time: '1 minute ago'
            },
            {
                icon: '⚠️',
                text: `Risk assessment - Expected loss: $${expectedLoss.toLocaleString()}`,
                time: '2 minutes ago'
            }
        ];
        
        updateActivityList(activities);
    }

    function updateElement(selector, value) {
        const element = document.querySelector(selector);
        if (element) {
            element.textContent = value;
        }
    }

    function updateStatsCard(index, value, change, isPositive) {
        const cards = document.querySelectorAll('.stats-card');
        if (cards[index]) {
            const valueEl = cards[index].querySelector('.stats-card__value');
            const changeEl = cards[index].querySelector('.stats-card__change');
            
            if (valueEl) valueEl.textContent = value;
            if (changeEl) {
                const changeText = changeEl.querySelector('span:last-child');
                if (changeText) changeText.textContent = change;
                
                // Update arrow
                const arrow = changeEl.querySelector('span:first-child');
                if (arrow) {
                    arrow.textContent = isPositive ? '↑' : '↓';
                }
                
                // Update class
                if (isPositive) {
                    changeEl.classList.remove('stats-card__change--negative');
                } else {
                    changeEl.classList.add('stats-card__change--negative');
                }
            }
        }
    }

    // ============================================================
    // DATA UPDATES (from API)
    // ============================================================
    window.updateDashboardData = function(data) {
        // Update stats cards
        if (data.stats) {
            updateStatsCards(data.stats);
        }

        // Update shipment info
        if (data.shipment) {
            updateShipmentCard(data.shipment);
        }

        // Update activity
        if (data.activity) {
            updateActivityList(data.activity);
        }

        // Update chart
        if (data.chartData && window.dashboardChart) {
            window.dashboardChart.data.datasets[0].data = data.chartData;
            window.dashboardChart.update();
        }
    };

    function updateStatsCards(stats) {
        const cards = document.querySelectorAll('.stats-card');
        cards.forEach((card, index) => {
            const valueElement = card.querySelector('.stats-card__value');
            if (valueElement && stats[index]) {
                valueElement.textContent = stats[index].value;
            }
        });
    }

    function updateShipmentCard(shipment) {
        const shipmentId = document.querySelector('.shipment-card__value[data-field="id"]');
        const origin = document.querySelector('.shipment-card__value[data-field="origin"]');
        const destination = document.querySelector('.shipment-card__value[data-field="destination"]');
        const eta = document.querySelector('.shipment-card__value[data-field="eta"]');

        if (shipmentId) shipmentId.textContent = shipment.id || 'FX-2023-456';
        if (origin) origin.textContent = shipment.origin || 'LAX';
        if (destination) destination.textContent = shipment.destination || 'JFK';
        if (eta) eta.textContent = shipment.eta || '2023-11-15';
    }

    function updateActivityList(activities) {
        const activityList = document.querySelector('.recent-activity__list');
        if (!activityList) return;

        activityList.innerHTML = '';
        activities.forEach(activity => {
            const item = document.createElement('div');
            item.className = 'activity-item';
            item.innerHTML = `
                <div class="activity-item__icon">${activity.icon || '📦'}</div>
                <div class="activity-item__content">
                    <div class="activity-item__text">${activity.text}</div>
                    <div class="activity-item__time">${activity.time}</div>
                </div>
            `;
            activityList.appendChild(item);
        });
    }

    // ============================================================
    // NOTIFICATION HANDLER
    // ============================================================
    const notificationIcon = document.querySelector('.notification-icon');
    if (notificationIcon) {
        notificationIcon.addEventListener('click', function() {
            // TODO: Open notification panel
            console.log('Notifications clicked');
        });
    }

    // ============================================================
    // EXPORT FOR EXTERNAL USE
    // ============================================================
    window.Dashboard = {
        updateData: updateDashboardData,
        refreshChart: function() {
            if (window.dashboardChart) {
                window.dashboardChart.update();
            }
        }
    };

})();

