
(function() {
    'use strict';

    // Initialize RISKCAST namespace if needed
    if (typeof window.RISKCAST === 'undefined') {
        window.RISKCAST = {};
    }
    if (typeof window.RISKCAST.modules === 'undefined') {
        window.RISKCAST.modules = {};
    }

    /**
     * Input Summary Manager
     * Updates summary section when form fields change
     */
    const InputSummaryManager = {
        initialized: false,
        
        init: function() {
            if (this.initialized) return;
            
            document.addEventListener('DOMContentLoaded', () => {
                // Wait a bit for all scripts to load
                setTimeout(() => {
                    // Initial update
                    if (typeof updateInputSummary === 'function') {
                        updateInputSummary();
                    }
                    
                    // Update summary when any form field changes
                    this.setupFormWatchers();
                }, 500);
            });
            
            this.initialized = true;
        },
        
        setupFormWatchers: function() {
            // Debounce summary updates
            const debouncedUpdate = window.RISKCAST?.core?.utils?.debounce
                ? window.RISKCAST.core.utils.debounce(() => {
                    if (typeof updateInputSummary === 'function') {
                        updateInputSummary();
                    }
                }, 300)
                : () => {
                    if (typeof updateInputSummary === 'function') {
                        setTimeout(() => updateInputSummary(), 100);
                    }
                };
            
            const formInputs = document.querySelectorAll('input[type="text"], input[type="number"], input[type="date"], select');
            formInputs.forEach(input => {
                input.addEventListener('change', debouncedUpdate);
                input.addEventListener('input', debouncedUpdate);
            });
            
            // Watch for dropdown changes
            const dropdownValues = document.querySelectorAll('.dropdown-value');
            dropdownValues.forEach(dropdown => {
                const observer = new MutationObserver(debouncedUpdate);
                observer.observe(dropdown, { childList: true, characterData: true, subtree: true });
            });
        }
    };

    /**
     * Summary Page Manager
     * Handles summary page data loading and rendering
     */
    class SummaryPage {
        constructor() {
            this.data = null;
            this.init();
        }

        async init() {
            await this.loadData();
            this.populateData();
            this.setupAnimations();
        }

        async loadData() {
            try {
                // Try localStorage first (from input.html)
                const lastResult = localStorage.getItem('last_result');
                if (lastResult) {
                    const result = JSON.parse(lastResult);
                    this.data = this.extractSummaryData(result);
                    console.log('✓ Summary data loaded from localStorage');
                    return;
                }

                // Try API
                const response = await fetch('/api/get_last_result');
                if (response.ok) {
                    const apiData = await response.json();
                    if (apiData && !apiData.error) {
                        this.data = this.extractSummaryData(apiData);
                        console.log('✓ Summary data loaded from API');
                        return;
                    }
                }
            } catch (error) {
                console.warn('Failed to load summary data:', error);
            }

            // Default empty data
            this.data = this.getDefaultData();
        }

        extractSummaryData(result) {
            const shipment = result.shipment || {};
            const route = shipment.route || result.route || '';
            
            // Extract origin/destination from route
            let origin = shipment.origin || '';
            let destination = shipment.destination || '';
            if (!origin || !destination) {
                const parts = route.split('_');
                if (parts.length >= 2) {
                    origin = this.extractPortCode(parts[0]);
                    destination = this.extractPortCode(parts[1]);
                }
            }

            return {
                route: route,
                routeLabel: this.getRouteLabel(route),
                origin: origin,
                destination: destination,
                transportMode: shipment.transport_mode || result.transport_mode || '',
                transportModeLabel: this.getTransportModeLabel(shipment.transport_mode || result.transport_mode || ''),
                cargoType: shipment.cargo_type || result.cargo_type || '',
                cargoTypeLabel: this.getCargoTypeLabel(shipment.cargo_type || result.cargo_type || ''),
                container: result.container || shipment.container || '',
                containerLabel: this.getContainerLabel(result.container || shipment.container || ''),
                incoterm: result.incoterm || shipment.incoterm || '',
                incotermLabel: this.getIncotermLabel(result.incoterm || shipment.incoterm || ''),
                packaging: result.packaging || shipment.packaging || '',
                packagingLabel: this.getPackagingLabel(result.packaging || shipment.packaging || ''),
                distance: result.distance || shipment.distance || 0,
                distanceKm: (result.distance || shipment.distance || 0) > 0 
                    ? `${(result.distance || shipment.distance || 0).toLocaleString()} km` 
                    : '-- km',
                transitTime: result.transit_time || shipment.transit_time || 0,
                transitTimeDays: (result.transit_time || shipment.transit_time || 0) > 0 
                    ? `${result.transit_time || shipment.transit_time || 0} ngày` 
                    : '-- ngày',
                carrier: result.carrier || shipment.carrier || '',
                carrierRating: result.carrier_rating || shipment.carrier_rating || 3.0,
                packages: result.packages || shipment.packages || 0,
                cargoValue: result.cargo_value || shipment.cargo_value || 0,
                etd: result.etd || shipment.etd || '',
                eta: result.eta || shipment.eta || ''
            };
        }

        getDefaultData() {
            return {
                route: '',
                routeLabel: '--',
                origin: '',
                destination: '',
                transportMode: '',
                transportModeLabel: '--',
                cargoType: '',
                cargoTypeLabel: '--',
                container: '',
                containerLabel: '--',
                incoterm: '',
                incotermLabel: '--',
                packaging: '',
                packagingLabel: '--',
                distance: 0,
                distanceKm: '-- km',
                transitTime: 0,
                transitTimeDays: '-- ngày',
                carrier: '',
                carrierRating: 3.0,
                packages: 0,
                cargoValue: 0,
                etd: '',
                eta: ''
            };
        }

        extractPortCode(routePart) {
            // Extract port code from route string
            return routePart.toUpperCase();
        }

        getRouteLabel(route) {
            // Map route keys to display labels
            const routeMap = {
                'vn_us': 'Việt Nam → Hoa Kỳ',
                'vn_eu': 'Việt Nam → Châu Âu',
                'vn_cn': 'Việt Nam → Trung Quốc',
                'vn_sg': 'Việt Nam → Singapore',
                'domestic': 'Nội Địa'
            };
            return routeMap[route] || route || '--';
        }

        getTransportModeLabel(mode) {
            const modeMap = {
                'ocean_fcl': 'Vận Tải Biển — FCL',
                'ocean_lcl': 'Vận Tải Biển — LCL',
                'air': 'Vận Tải Hàng Không',
                'rail': 'Vận Tải Đường Sắt',
                'road': 'Đường Bộ — Xe Tải'
            };
            return modeMap[mode] || mode || '--';
        }

        getCargoTypeLabel(type) {
            const typeMap = {
                'electronics': 'Điện Tử',
                'food_bev': 'Thực Phẩm & Đồ Uống',
                'garments': 'May Mặc / Dệt May',
                'agriculture': 'Nông Sản'
            };
            return typeMap[type] || type || '--';
        }

        getContainerLabel(container) {
            const containerMap = {
                '20ft': '20ft Thường',
                '40ft': '40ft Thường',
                '40hc': '40ft Cao (High Cube)',
                'reefer': 'Container Lạnh (Reefer)'
            };
            return containerMap[container] || container || '--';
        }

        getIncotermLabel(incoterm) {
            return incoterm.toUpperCase() || '--';
        }

        getPackagingLabel(packaging) {
            const packagingMap = {
                'poor': 'Kém',
                'medium': 'Trung Bình',
                'good': 'Tốt',
                'excellent': 'Xuất Sắc'
            };
            return packagingMap[packaging] || packaging || '--';
        }

        populateData() {
            // Populate summary page with data
            if (!this.data) return;
            
            // Implementation depends on HTML structure
            console.log('Summary data ready:', this.data);
        }

        setupAnimations() {
            // Setup summary page animations
        }
    }

    // Export to RISKCAST namespace
    window.RISKCAST.modules.inputSummary = {
        manager: InputSummaryManager,
        SummaryPage: SummaryPage,
        init: () => InputSummaryManager.init()
    };

    // Initialize input summary manager
    InputSummaryManager.init();

    // Initialize summary page if on summary/overview page
    if (window.location.pathname.includes('overview') || window.location.pathname.includes('summary')) {
        window.summaryPage = new SummaryPage();
    }

    // Backward compatibility
    window.InputSummaryManager = InputSummaryManager;
    window.SummaryPage = SummaryPage;

    console.log('✅ RISKCAST Module: Input Summary initialized');

})();





















