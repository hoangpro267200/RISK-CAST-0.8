
(function() {
    'use strict';

    // Global Data Store
    window.RiskCastData = {
        // Transport
        transport: {
            tradeLane: null,
            transportMode: null,
            route: null,
            pol: null,
            pod: null,
            departureDate: null,
            distance: null,
            transitTime: null
        },
        
        // Cargo
        cargo: {
            cargoType: null,
            packingType: null,
            grossWeight: null,
            volume: null,
            containerType: null,
            packages: null
        },
        
        // Seller
        seller: {
            companyName: null,
            country: null,
            companySize: null,
            email: null,
            phone: null,
            personInCharge: null,
            reliability: null,
            riskLevel: null,
            esgScore: null
        },
        
        // Buyer
        buyer: {
            companyName: null,
            country: null,
            companySize: null,
            email: null,
            phone: null,
            personInCharge: null,
            reliability: null,
            riskLevel: null,
            esgScore: null
        },
        
        // Advanced Parameters
        advanced: {
            distance: null,
            routeType: null,
            carrier: null,
            carrierRating: null,
            weatherRisk: null,
            portRisk: null,
            containerMatch: null,
            shipmentValue: null,
            priority: null
        },
        
        // Climate & ESG
        climate: {
            ensoIndex: null,
            typhoonFrequency: null,
            sstAnomaly: null,
            portClimateStress: null,
            climateVolatilityIndex: null,
            esgScore: null,
            climateResilience: null,
            greenPackaging: null
        }
    };

    // Data Store Manager
    window.RiskCastDataStore = {
        /**
         * Update a value in the data store
         */
        set: function(section, field, value) {
            if (window.RiskCastData[section] && field in window.RiskCastData[section]) {
                window.RiskCastData[section][field] = value;
                this.triggerUpdate(section, field, value);
            }
        },
        
        /**
         * Get a value from the data store
         */
        get: function(section, field) {
            if (window.RiskCastData[section] && field in window.RiskCastData[section]) {
                return window.RiskCastData[section][field];
            }
            return null;
        },
        
        /**
         * Update multiple fields at once
         */
        update: function(section, data) {
            if (window.RiskCastData[section]) {
                Object.assign(window.RiskCastData[section], data);
                Object.keys(data).forEach(field => {
                    this.triggerUpdate(section, field, data[field]);
                });
            }
        },
        
        /**
         * Trigger update event
         */
        triggerUpdate: function(section, field, value) {
            const event = new CustomEvent('riskcastDataUpdate', {
                detail: { section, field, value }
            });
            document.dispatchEvent(event);
        },
        
        /**
         * Sync from form inputs
         */
        syncFromInputs: function() {
            // This will be called by SummaryOverviewManager
            // Implementation in summary_overview_enterprise.js
        },
        
        /**
         * Sync to form inputs
         */
        syncToInputs: function(section, field, value) {
            // This will be called when summary is edited
            // Implementation in summary_overview_enterprise.js
        }
    };


})();







