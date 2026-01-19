/* ==========================================================================
   SUMMARY_V400 - VALIDATOR
   25 logistics rules for validation
   ========================================================================== */

const V400Validator = (() => {
    
    // Rule definitions
    const RULES = [
        // TRADE & ROUTE RULES
        {
            id: 'MODE_PORT_MISMATCH_SEA',
            severity: 'critical',
            scope: 'trade',
            message: 'Phương thức là SEA nhưng POL hoặc POD có vẻ là sân bay',
            fieldRefs: ['shipment.trade_route.mode', 'shipment.trade_route.pol', 'shipment.trade_route.pod'],
            when: (state) => {
                const mode = state.shipment.trade_route.mode;
                const pol = state.shipment.trade_route.pol;
                const pod = state.shipment.trade_route.pod;
                
                if (mode !== 'SEA') return false;
                
                const airportCodes = ['JFK', 'LAX', 'ORD', 'DFW', 'ATL', 'LHR', 'CDG', 'FRA', 'AMS', 'DXB', 'HKG', 'SIN', 'NRT', 'ICN'];
                const isPolAirport = airportCodes.some(code => pol && pol.includes(code));
                const isPodAirport = airportCodes.some(code => pod && pod.includes(code));
                
                return isPolAirport || isPodAirport;
            }
        },
        {
            id: 'MODE_PORT_MISMATCH_AIR',
            severity: 'critical',
            scope: 'trade',
            message: 'Phương thức là AIR nhưng POL hoặc POD có vẻ là cảng biển',
            fieldRefs: ['shipment.trade_route.mode', 'shipment.trade_route.pol', 'shipment.trade_route.pod'],
            when: (state) => {
                const mode = state.shipment.trade_route.mode;
                const pol = state.shipment.trade_route.pol;
                const pod = state.shipment.trade_route.pod;
                
                if (mode !== 'AIR') return false;
                
                const seaportPrefixes = ['CN', 'US', 'DE', 'NL', 'GB', 'FR', 'SG', 'HK', 'JP', 'KR', 'AE', 'SA', 'IN'];
                const hasSeaportPrefix = (port) => seaportPrefixes.some(prefix => port && port.startsWith(prefix) && port.length === 5);
                
                return hasSeaportPrefix(pol) || hasSeaportPrefix(pod);
            }
        },
        {
            id: 'ETD_IN_PAST',
            severity: 'critical',
            scope: 'trade',
            message: 'ETD đã qua',
            fieldRefs: ['shipment.trade_route.etd'],
            when: (state) => {
                const etd = state.shipment.trade_route.etd;
                if (!etd) return false;
                
                const etdDate = new Date(etd);
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                
                return etdDate < today;
            }
        },
        {
            id: 'ETA_BEFORE_ETD',
            severity: 'critical',
            scope: 'trade',
            message: 'ETA trước ETD',
            fieldRefs: ['shipment.trade_route.etd', 'shipment.trade_route.eta'],
            when: (state) => {
                const etd = state.shipment.trade_route.etd;
                const eta = state.shipment.trade_route.eta;
                
                if (!etd || !eta) return false;
                
                return new Date(eta) < new Date(etd);
            }
        },
        {
            id: 'TRANSIT_DAYS_MISSING',
            severity: 'warning',
            scope: 'trade',
            message: 'Thiếu thời gian vận chuyển (ngày)',
            fieldRefs: ['shipment.trade_route.transit_time_days'],
            when: (state) => {
                const mode = state.shipment.trade_route.mode;
                const transit = state.shipment.trade_route.transit_time_days;
                
                return mode && !transit;
            }
        },
        {
            id: 'TRANSIT_DAYS_OUTLIER',
            severity: 'warning',
            scope: 'trade',
            message: 'Thời gian vận chuyển có vẻ bất thường cho phương thức này',
            fieldRefs: ['shipment.trade_route.transit_time_days', 'shipment.trade_route.mode'],
            when: (state) => {
                const mode = state.shipment.trade_route.mode;
                const transit = state.shipment.trade_route.transit_time_days;
                
                if (!mode || !transit) return false;
                
                if (mode === 'SEA' && (transit < 3 || transit > 90)) return true;
                if (mode === 'AIR' && transit > 15) return true;
                
                return false;
            }
        },
        {
            id: 'INCOTERM_LOCATION_REQUIRED',
            severity: 'warning',
            scope: 'trade',
            message: 'Địa điểm Incoterm là bắt buộc cho điều kiện này',
            fieldRefs: ['shipment.trade_route.incoterm', 'shipment.trade_route.incoterm_location'],
            when: (state) => {
                const incoterm = state.shipment.trade_route.incoterm;
                const location = state.shipment.trade_route.incoterm_location;
                
                const requiresLocation = ['FOB', 'CIF', 'CFR', 'DAP', 'DPU', 'DDP'];
                
                return requiresLocation.includes(incoterm) && !location;
            }
        },
        {
            id: 'PRIORITY_WITH_WEIRD_MODE',
            severity: 'suggestion',
            scope: 'trade',
            message: 'Ưu tiên là EXPRESS nhưng phương thức là SEA - nên xem xét phương thức AIR để giao hàng nhanh hơn',
            fieldRefs: ['shipment.trade_route.priority', 'shipment.trade_route.mode'],
            when: (state) => {
                const priority = state.shipment.trade_route.priority;
                const mode = state.shipment.trade_route.mode;
                
                return priority === 'EXPRESS' && mode === 'SEA';
            }
        },
        {
            id: 'SERVICE_ROUTE_SUGGEST',
            severity: 'suggestion',
            scope: 'trade',
            message: 'Tuyến dịch vụ trống - nên thêm để theo dõi tốt hơn',
            fieldRefs: ['shipment.trade_route.service_route'],
            when: (state) => {
                const route = state.shipment.trade_route.service_route;
                const pol = state.shipment.trade_route.pol;
                const pod = state.shipment.trade_route.pod;
                
                return !route && pol && pod;
            }
        },
        
        // CARGO & PACKING RULES
        {
            id: 'HS_CODE_REQUIRED',
            severity: 'critical',
            scope: 'cargo',
            message: 'Mã HS là bắt buộc khi đã chỉ định trọng lượng hoặc thể tích hàng hóa',
            fieldRefs: ['shipment.cargo_packing.hs_code', 'shipment.cargo_packing.gross_weight_kg', 'shipment.cargo_packing.volume_cbm'],
            when: (state) => {
                const hs = state.shipment.cargo_packing.hs_code;
                const weight = state.shipment.cargo_packing.gross_weight_kg;
                const volume = state.shipment.cargo_packing.volume_cbm;
                
                return !hs && (weight > 0 || volume > 0);
            }
        },
        {
            id: 'HS_DG_ENFORCED',
            severity: 'critical',
            scope: 'cargo',
            message: 'Sản phẩm chương HS 28/29 thường là hàng nguy hiểm - nên bật cờ DG',
            fieldRefs: ['shipment.cargo_packing.hs_chapter', 'shipment.cargo_packing.is_dg'],
            when: (state) => {
                const chapter = state.shipment.cargo_packing.hs_chapter;
                const isDG = state.shipment.cargo_packing.is_dg;
                
                return (chapter === '28' || chapter === '29') && !isDG;
            }
        },
        {
            id: 'HS_REEFER_ENFORCED',
            severity: 'warning',
            scope: 'cargo',
            message: 'Hàng dễ hỏng thường yêu cầu container lạnh',
            fieldRefs: ['shipment.cargo_packing.cargo_category', 'shipment.trade_route.container_type'],
            when: (state) => {
                const category = state.shipment.cargo_packing.cargo_category;
                const container = state.shipment.trade_route.container_type;
                
                return category === 'Perishable' && container && !container.includes('REEFER') && !container.includes('RF');
            }
        },
        {
            id: 'STACKABILITY_CHECK',
            severity: 'warning',
            scope: 'cargo',
            message: 'Hàng dễ vỡ không nên có thể xếp chồng',
            fieldRefs: ['shipment.cargo_packing.cargo_category', 'shipment.cargo_packing.stackability'],
            when: (state) => {
                const category = state.shipment.cargo_packing.cargo_category;
                const stackable = state.shipment.cargo_packing.stackability;
                
                const fragileCategories = ['Electronics', 'Fragile', 'Glass', 'Ceramics'];
                
                return fragileCategories.includes(category) && stackable;
            }
        },
        {
            id: 'WEIGHT_VOLUME_INCONSISTENT',
            severity: 'warning',
            scope: 'cargo',
            message: 'Tỷ lệ trọng lượng/thể tích có vẻ bất thường (có thể là lỗi nhập liệu)',
            fieldRefs: ['shipment.cargo_packing.gross_weight_kg', 'shipment.cargo_packing.volume_cbm'],
            when: (state) => {
                const weight = state.shipment.cargo_packing.gross_weight_kg;
                const volume = state.shipment.cargo_packing.volume_cbm;
                
                if (!weight || !volume || volume === 0) return false;
                
                const ratio = weight / volume;
                
                return ratio < 50 || ratio > 1500;
            }
        },
        {
            id: 'WEIGHT_GREATER_THAN_NET',
            severity: 'critical',
            scope: 'cargo',
            message: 'Trọng lượng tịnh không thể vượt quá trọng lượng tổng',
            fieldRefs: ['shipment.cargo_packing.gross_weight_kg', 'shipment.cargo_packing.net_weight_kg'],
            when: (state) => {
                const gross = state.shipment.cargo_packing.gross_weight_kg;
                const net = state.shipment.cargo_packing.net_weight_kg;
                
                return net && gross && net > gross;
            }
        },
        {
            id: 'PACKAGES_REQUIRED',
            severity: 'warning',
            scope: 'cargo',
            message: 'Nên chỉ định số lượng kiện hàng',
            fieldRefs: ['shipment.cargo_packing.packages', 'shipment.cargo_packing.volume_cbm'],
            when: (state) => {
                const packages = state.shipment.cargo_packing.packages;
                const volume = state.shipment.cargo_packing.volume_cbm;
                
                return volume > 0 && !packages;
            }
        },
        {
            id: 'PACKING_TYPE_MISMATCH',
            severity: 'warning',
            scope: 'cargo',
            message: 'Hàng không thể xếp chồng với đóng gói bằng pallet - nên xem xét thùng hoặc hộp',
            fieldRefs: ['shipment.cargo_packing.packing_type', 'shipment.cargo_packing.stackability'],
            when: (state) => {
                const packing = state.shipment.cargo_packing.packing_type;
                const stackable = state.shipment.cargo_packing.stackability;
                
                return packing === 'Pallet' && !stackable;
            }
        },
        
        // SELLER / BUYER RULES
        {
            id: 'SELLER_CONTACT_REQUIRED',
            severity: 'critical',
            scope: 'seller',
            message: 'Email và điện thoại người bán là bắt buộc',
            fieldRefs: ['shipment.seller.company', 'shipment.seller.email', 'shipment.seller.phone'],
            when: (state) => {
                const company = state.shipment.seller.company;
                const email = state.shipment.seller.email;
                const phone = state.shipment.seller.phone;
                
                return company && (!email || !phone);
            }
        },
        {
            id: 'BUYER_CONTACT_REQUIRED',
            severity: 'critical',
            scope: 'buyer',
            message: 'Email và điện thoại người mua là bắt buộc',
            fieldRefs: ['shipment.buyer.company', 'shipment.buyer.email', 'shipment.buyer.phone'],
            when: (state) => {
                const company = state.shipment.buyer.company;
                const email = state.shipment.buyer.email;
                const phone = state.shipment.buyer.phone;
                
                return company && (!email || !phone);
            }
        },
        {
            id: 'COUNTRY_MISMATCH_POL',
            severity: 'warning',
            scope: 'seller',
            message: 'Quốc gia người bán khác với POL - cần kiểm tra phương án vận chuyển nội địa',
            fieldRefs: ['shipment.seller.country', 'shipment.trade_route.pol', 'shipment.trade_route.incoterm'],
            when: (state) => {
                const sellerCountry = state.shipment.seller.country;
                const pol = state.shipment.trade_route.pol;
                const incoterm = state.shipment.trade_route.incoterm;
                
                if (!sellerCountry || !pol) return false;
                
                const polCountry = V400State.getCountryFromPortCode(pol);
                
                return sellerCountry !== polCountry && ['EXW', 'FCA'].includes(incoterm);
            }
        },
        {
            id: 'COUNTRY_MISMATCH_POD',
            severity: 'warning',
            scope: 'buyer',
            message: 'Quốc gia người mua khác với POD - cần kiểm tra phương án giao hàng cuối cùng',
            fieldRefs: ['shipment.buyer.country', 'shipment.trade_route.pod', 'shipment.trade_route.incoterm'],
            when: (state) => {
                const buyerCountry = state.shipment.buyer.country;
                const pod = state.shipment.trade_route.pod;
                const incoterm = state.shipment.trade_route.incoterm;
                
                if (!buyerCountry || !pod) return false;
                
                const podCountry = V400State.getCountryFromPortCode(pod);
                
                return buyerCountry !== podCountry && ['DAP', 'DPU', 'DDP'].includes(incoterm);
            }
        },
        {
            id: 'EMAIL_FORMAT_CHECK',
            severity: 'warning',
            scope: 'seller',
            message: 'Định dạng email có vẻ không hợp lệ',
            fieldRefs: ['shipment.seller.email', 'shipment.buyer.email'],
            when: (state) => {
                const sellerEmail = state.shipment.seller.email;
                const buyerEmail = state.shipment.buyer.email;
                
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                
                const sellerInvalid = sellerEmail && !emailRegex.test(sellerEmail);
                const buyerInvalid = buyerEmail && !emailRegex.test(buyerEmail);
                
                return sellerInvalid || buyerInvalid;
            }
        },
        {
            id: 'PHONE_FORMAT_CHECK',
            severity: 'warning',
            scope: 'seller',
            message: 'Số điện thoại có vẻ quá ngắn',
            fieldRefs: ['shipment.seller.phone', 'shipment.buyer.phone'],
            when: (state) => {
                const sellerPhone = state.shipment.seller.phone;
                const buyerPhone = state.shipment.buyer.phone;
                
                const isValidLength = (phone) => phone && phone.replace(/\D/g, '').length >= 8;
                
                const sellerInvalid = sellerPhone && !isValidLength(sellerPhone);
                const buyerInvalid = buyerPhone && !isValidLength(buyerPhone);
                
                return sellerInvalid || buyerInvalid;
            }
        },
        
        // RISK MODULE RULES
        {
            id: 'RISK_MODULES_OFF_FOR_LONG_ROUTE',
            severity: 'suggestion',
            scope: 'risk',
            message: 'Đối với tuyến vận chuyển dài, nên bật mô-đun Weather và Congestion',
            fieldRefs: ['shipment.trade_route.transit_time_days', 'riskModules.weather', 'riskModules.congestion'],
            when: (state) => {
                const transit = state.shipment.trade_route.transit_time_days;
                const weather = state.riskModules.weather;
                const congestion = state.riskModules.congestion;
                
                return transit > 20 && (!weather || !congestion);
            }
        },
        {
            id: 'INSURANCE_ADVICE_HIGH_RISK',
            severity: 'suggestion',
            scope: 'risk',
            message: 'Nên sử dụng mô-đun Insurance cho hàng nguy hiểm hoặc hàng có giá trị cao',
            fieldRefs: ['shipment.cargo_packing.is_dg', 'shipment.cargo_packing.cargo_category', 'riskModules.insurance'],
            when: (state) => {
                const isDG = state.shipment.cargo_packing.is_dg;
                const category = state.shipment.cargo_packing.cargo_category;
                const insurance = state.riskModules.insurance;
                
                const highValueCategories = ['High Value', 'Electronics', 'Pharmaceuticals'];
                
                return !insurance && (isDG || highValueCategories.includes(category));
            }
        }
    ];
    
    /**
     * Evaluate all rules against current state
     */
    function evaluateAll(state) {
        const results = {
            critical: [],
            warning: [],
            suggestion: [],
            all: []
        };
        
        for (const rule of RULES) {
            try {
                if (rule.when(state)) {
                    const result = {
                        ...rule,
                        timestamp: Date.now()
                    };
                    
                    results[rule.severity].push(result);
                    results.all.push(result);
                }
            } catch (error) {
                console.error(`Error evaluating rule ${rule.id}:`, error);
            }
        }
        
        return results;
    }
    
    /**
     * Get rules by scope
     */
    function getRulesByScope(results, scope) {
        return results.all.filter(r => r.scope === scope);
    }
    
    /**
     * Get rules affecting specific field
     */
    function getRulesForField(results, fieldPath) {
        return results.all.filter(r => r.fieldRefs.includes(fieldPath));
    }
    
    // Public API
    return {
        RULES,
        evaluateAll,
        getRulesByScope,
        getRulesForField
    };
})();


