/**
 * ========================================================================
 * RISKCAST v20 - API Client
 * ========================================================================
 * Handles API calls and payload building
 * 
 * @class APIClient
 */
export class APIClient {
    /**
     * @param {StateManager} stateManager - State manager instance
     */
    constructor(stateManager) {
        this.stateManager = stateManager;
    }
    
    /**
     * Build shipment payload for API from RISKCAST_STATE
     * FIX: Ensure NO null/undefined values - backend calls .upper() on strings
     * @param {Object} state - RISKCAST_STATE object
     * @returns {Object} API payload
     */
    buildShipmentPayloadForAPI(state) {
        const transport = state.transport || {};
        const cargo = state.cargo || {};
        const seller = state.seller || {};
        const buyer = state.buyer || {};
        
        // Helper: ALWAYS return string, never null/undefined
        const safeStr = (val, defaultVal = '') => {
            if (val === null || val === undefined || val === '') return defaultVal;
            return String(val);
        };
        
        // Helper: ALWAYS return number, never null/undefined
        const toNum = (val, defaultVal = 0) => {
            if (val === null || val === undefined || val === '') return defaultVal;
            const num = Number(val);
            return isNaN(num) ? defaultVal : num;
        };
        
        // CRITICAL: Backend calls .upper() on these fields - MUST be strings, never null
        // Fields that backend uses .upper() on: pol, pod, route, carrier, port
        const pol = safeStr(transport.pol, 'UNKNOWN_POL');
        const pod = safeStr(transport.pod, 'UNKNOWN_POD');
        const routeStr = pol && pod && pol !== 'UNKNOWN_POL' && pod !== 'UNKNOWN_POD'
            ? `${pol} → ${pod}`
            : transport.tradeLane || pol || pod || 'UNKNOWN_ROUTE';
        const route = safeStr(routeStr, 'UNKNOWN_ROUTE');
        const carrier = safeStr(transport.carrier, 'UNKNOWN_CARRIER');
        
        // REQUIRED FIELDS - NEVER NULL (backend calls .upper() on these)
        const payload = {
            transport_mode: safeStr(transport.mode || transport.modeOfTransport, 'SEA'),
            cargo_type: safeStr(cargo.cargoType, 'general'),
            route: route, // Already safeStr'd above
            incoterm: safeStr(transport.incoterm, 'EXW'),
            carrier: carrier, // Already safeStr'd above
            container: safeStr(transport.containerType, 'STANDARD'),
            packaging: safeStr(cargo.packingType, 'carton'),
            priority: safeStr(transport.priority, 'standard'),
            
            // CRITICAL: Add pol and pod explicitly (backend uses these)
            pol: pol, // Already safeStr'd above
            pod: pod, // Already safeStr'd above
            
            // NUMERIC FIELDS - NEVER NULL
            packages: toNum(cargo.numberOfPackages, 1),
            transit_time: toNum(transport.transitTime || transport.transitTimeDays, 15),
            cargo_value: Math.max(toNum(state.shipment?.valueUSD || cargo.insuranceValue, 1000), 1000), // Minimum 1000 to ensure financial calculations
            distance: toNum(transport.distance, 1000),
            shipment_value: Math.max(toNum(state.shipment?.valueUSD || cargo.insuranceValue, 1000), 1000), // Minimum 1000 to ensure financial calculations
            
            // OPTIONAL STRING FIELDS - EMPTY STRING IF MISSING
            etd: safeStr(transport.etd),
            eta: safeStr(transport.eta),
            route_type: safeStr(transport.shipmentType),
            hs_code: safeStr(cargo.hsCode),
            
            // OPTIONAL NUMERIC FIELDS - 0 IF MISSING
            carrier_rating: toNum(transport.reliabilityScore),
            weather_risk: toNum(state.risk?.weatherRisk),
            port_risk: toNum(state.risk?.congestionRisk),
            cargo_weight: toNum(cargo.grossWeight),
            cargo_volume: toNum(cargo.volumeM3),
            
            // FLAGS
            use_fuzzy: true,
            use_forecast: true,
            use_mc: true,
            use_var: true,
            
            // LANGUAGE
            language: 'vi'
        };
        
        // ONLY include buyer/seller if they have data (with safe strings)
        // Always ensure country is a string, never null
        if (seller && (seller.companyName || seller.country)) {
            const sellerCountry = seller.country;
            let sellerCountryStr = 'Unknown';
            if (sellerCountry) {
                if (typeof sellerCountry === 'string') {
                    sellerCountryStr = sellerCountry;
                } else if (sellerCountry.name) {
                    sellerCountryStr = sellerCountry.name;
                } else if (sellerCountry.iso2) {
                    sellerCountryStr = sellerCountry.iso2;
                }
            }
            
            payload.seller = {
                company_name: safeStr(seller.companyName || seller.company_name, ''),
                country: safeStr(sellerCountryStr, 'Unknown'),
                contact_person: safeStr(seller.contactPerson || seller.contact_person, ''),
                email: safeStr(seller.email, ''),
                phone: safeStr(seller.phone, ''),
                business_type: safeStr(seller.businessType || seller.business_type, ''),
                address: safeStr(seller.address, ''),
                tax_id: safeStr(seller.taxId || seller.tax_id, '')
            };
        }
        
        if (buyer && (buyer.companyName || buyer.country)) {
            const buyerCountry = buyer.country;
            let buyerCountryStr = 'Unknown';
            if (buyerCountry) {
                if (typeof buyerCountry === 'string') {
                    buyerCountryStr = buyerCountry;
                } else if (buyerCountry.name) {
                    buyerCountryStr = buyerCountry.name;
                } else if (buyerCountry.iso2) {
                    buyerCountryStr = buyerCountry.iso2;
                }
            }
            
            payload.buyer = {
                company_name: safeStr(buyer.companyName || buyer.company_name, ''),
                country: safeStr(buyerCountryStr, 'Unknown'),
                contact_person: safeStr(buyer.contactPerson || buyer.contact_person, ''),
                email: safeStr(buyer.email, ''),
                phone: safeStr(buyer.phone, ''),
                business_type: safeStr(buyer.businessType || buyer.business_type, ''),
                address: safeStr(buyer.address, ''),
                tax_id: safeStr(buyer.taxId || buyer.tax_id, '')
            };
        }
        
        // FINAL CLEANUP: Ensure ALL string fields are strings, remove null/undefined
        const deepClean = (obj) => {
            if (obj === null || obj === undefined) return undefined;
            
            if (Array.isArray(obj)) {
                return obj.map(deepClean).filter(v => v !== undefined && v !== null);
            }
            
            if (typeof obj === 'object') {
                const cleaned = {};
                for (const [key, value] of Object.entries(obj)) {
                    if (value === null || value === undefined) {
                        // For string fields, use empty string instead of skipping
                        if (key.includes('name') || key.includes('country') || key.includes('type') || 
                            key.includes('mode') || key.includes('route') || key.includes('incoterm') ||
                            key.includes('carrier') || key.includes('container') || key.includes('packaging') ||
                            key.includes('priority') || key.includes('email') || key.includes('phone') ||
                            key.includes('address') || key.includes('tax') || key.includes('contact') ||
                            key.includes('business') || key.includes('company') || key.includes('person') ||
                            key.includes('role') || key.includes('etd') || key.includes('eta') ||
                            key.includes('hs_code') || key.includes('route_type') || key.includes('language')) {
                            cleaned[key] = '';
                            continue;
                        }
                        // For other fields, skip
                        continue;
                    }
                    
                    // If it's a string field that might be empty, ensure it's a string
                    if (typeof value === 'string' || (key.includes('name') || key.includes('country') || 
                        key.includes('type') || key.includes('mode') || key.includes('route'))) {
                        cleaned[key] = String(value || '');
                    } else {
                        const cleanedValue = deepClean(value);
                        if (cleanedValue !== undefined && cleanedValue !== null) {
                            cleaned[key] = cleanedValue;
                        }
                    }
                }
                return cleaned;
            }
            
            return obj;
        };
        
        const cleanedPayload = deepClean(payload);
        
        // FINAL GUARANTEE: Force all required string fields to be strings
        // CRITICAL: These fields are used by backend with .upper() - MUST be strings
        const requiredStringFields = [
            'transport_mode', 'cargo_type', 'route', 'incoterm', 'carrier', 
            'container', 'packaging', 'priority', 'etd', 'eta', 'route_type', 
            'hs_code', 'language', 'pol', 'pod' // pol and pod are critical!
        ];
        
        const defaults = {
            'transport_mode': 'SEA',
            'cargo_type': 'general',
            'route': 'UNKNOWN_ROUTE',
            'incoterm': 'EXW',
            'carrier': 'UNKNOWN_CARRIER',
            'container': 'STANDARD',
            'packaging': 'carton',
            'priority': 'standard',
            'etd': '',
            'eta': '',
            'route_type': '',
            'hs_code': '',
            'language': 'vi',
            'pol': 'UNKNOWN_POL',
            'pod': 'UNKNOWN_POD'
        };
        
        requiredStringFields.forEach(field => {
            if (!cleanedPayload[field] || typeof cleanedPayload[field] !== 'string') {
                cleanedPayload[field] = defaults[field] || '';
            }
            // Double check: ensure it's a string
            cleanedPayload[field] = String(cleanedPayload[field] || defaults[field] || '');
        });
        
        // Ensure nested objects have safe strings
        if (cleanedPayload.seller) {
            Object.keys(cleanedPayload.seller).forEach(key => {
                if (typeof cleanedPayload.seller[key] !== 'string') {
                    cleanedPayload.seller[key] = String(cleanedPayload.seller[key] || '');
                }
            });
        }
        
        if (cleanedPayload.buyer) {
            Object.keys(cleanedPayload.buyer).forEach(key => {
                if (typeof cleanedPayload.buyer[key] !== 'string') {
                    cleanedPayload.buyer[key] = String(cleanedPayload.buyer[key] || '');
                }
            });
        }
        
        // ULTIMATE SAFETY CHECK: Validate critical fields one more time
        const criticalFields = ['pol', 'pod', 'route', 'carrier', 'transport_mode', 'cargo_type'];
        criticalFields.forEach(field => {
            if (!cleanedPayload[field] || typeof cleanedPayload[field] !== 'string') {
                console.error(`❌ CRITICAL: Field '${field}' is not a string!`, cleanedPayload[field]);
                cleanedPayload[field] = defaults[field] || 'UNKNOWN';
            }
        });
        
        // Log payload for debugging
        console.log('✅ Built API Payload (NO NULL VALUES, ALL STRINGS SAFE):', cleanedPayload);
        console.log('🔍 Critical fields check:', {
            pol: typeof cleanedPayload.pol,
            pod: typeof cleanedPayload.pod,
            route: typeof cleanedPayload.route,
            carrier: typeof cleanedPayload.carrier,
            transport_mode: typeof cleanedPayload.transport_mode
        });
        
        return cleanedPayload;
    }
    
    /**
     * Submit form to Engine v2 API
     * @param {Object} payload - API payload
     * @returns {Promise<Object>} API response
     */
    async submitToEngine(payload) {
        console.log('🔄 Calling /api/v1/risk/v2/analyze...');
        
        const response = await fetch('/api/v1/risk/v2/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API error: ${response.status} - ${errorText}`);
        }
        
        const apiResult = await response.json();
        console.log('✅ API Response received:', apiResult);
        
        return apiResult.result || apiResult;
    }
    
    /**
     * Build route legs from POL/POD
     * @param {string} pol - Port of Loading
     * @param {string} pod - Port of Discharge
     * @returns {Array} Route legs array
     */
    buildRouteLegs(pol, pod) {
        const legs = [];
        const src = pol || "";
        const dst = pod || "";
        const fromVN = (src || "").toUpperCase().startsWith("VN");
        const toKR = (dst || "").toUpperCase().includes("KR");
        const toUS = (dst || "").toUpperCase().includes("US");
        const toEU = /(NL|DE|GB|FR|EU)/.test((dst || "").toUpperCase());

        if (fromVN && toKR) {
            legs.push({ from: { name: src, lat: 0, lng: 0 }, to: { name: dst, lat: 0, lng: 0 }, distanceNm: 2200 });
        } else if (fromVN && toUS) {
            legs.push(
                { from: { name: src, lat: 0, lng: 0 }, to: { name: "Singapore", lat: 0, lng: 0 }, distanceNm: 800 },
                { from: { name: "Singapore", lat: 0, lng: 0 }, to: { name: "Dubai", lat: 0, lng: 0 }, distanceNm: 3400 },
                { from: { name: "Dubai", lat: 0, lng: 0 }, to: { name: dst, lat: 0, lng: 0 }, distanceNm: 8200 }
            );
        } else if (fromVN && toEU) {
            legs.push(
                { from: { name: src, lat: 0, lng: 0 }, to: { name: "Singapore", lat: 0, lng: 0 }, distanceNm: 800 },
                { from: { name: "Singapore", lat: 0, lng: 0 }, to: { name: dst, lat: 0, lng: 0 }, distanceNm: 6500 }
            );
        } else {
            legs.push({ from: { name: src, lat: 0, lng: 0 }, to: { name: dst, lat: 0, lng: 0 }, distanceNm: 5000 });
        }

        return legs;
    }
}

