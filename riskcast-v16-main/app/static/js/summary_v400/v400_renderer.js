/* ==========================================================================
   SUMMARY_V400 - RENDERER
   DOM rendering for panels, banner, and field tiles
   ========================================================================== */

const V400Renderer = (() => {
    
    // Field configuration map - matches FIELD_MAP structure
    const FIELD_MAP = {
        // Trade & Route fields
        'trade.pol': {
            section: 'trade',
            path: 'shipment.trade_route.pol',
            type: 'text',
            label: 'Cảng đi (POL)',
            placeholder: 'e.g., CNSHA, USNYC'
        },
        'trade.pod': {
            section: 'trade',
            path: 'shipment.trade_route.pod',
            type: 'text',
            label: 'Cảng đến (POD)',
            placeholder: 'e.g., DEHAM, NLRTM'
        },
        'trade.mode': {
            section: 'trade',
            path: 'shipment.trade_route.mode',
            type: 'select',
            label: 'Mode',
            options: ['', 'SEA', 'AIR', 'ROAD', 'RAIL', 'MULTIMODAL']
        },
        'trade.service_route': {
            section: 'trade',
            path: 'shipment.trade_route.service_route',
            type: 'text',
            label: 'Tuyến dịch vụ',
            placeholder: 'e.g., AE7, Pacific Express'
        },
        'trade.carrier': {
            section: 'trade',
            path: 'shipment.trade_route.carrier',
            type: 'text',
            label: 'Hãng vận chuyển',
            placeholder: 'e.g., Maersk, MSC'
        },
        'trade.container_type': {
            section: 'trade',
            path: 'shipment.trade_route.container_type',
            type: 'select',
            label: 'Loại container',
            options: ['', '20GP', '40GP', '40HC', '45HC', 'REEFER 20', 'REEFER 40', 'FLAT RACK', 'OPEN TOP']
        },
        'trade.etd': {
            section: 'trade',
            path: 'shipment.trade_route.etd',
            type: 'date',
            label: 'Ngày đi (ETD)'
        },
        'trade.eta': {
            section: 'trade',
            path: 'shipment.trade_route.eta',
            type: 'date',
            label: 'Ngày đến (ETA)',
            disabled: true
        },
        'trade.transit_time_days': {
            section: 'trade',
            path: 'shipment.trade_route.transit_time_days',
            type: 'number',
            label: 'Thời gian vận chuyển (ngày)',
            placeholder: 'e.g., 30'
        },
        'trade.incoterm': {
            section: 'trade',
            path: 'shipment.trade_route.incoterm',
            type: 'select',
            label: 'Incoterm',
            options: ['', 'EXW', 'FCA', 'FOB', 'CFR', 'CIF', 'CPT', 'CIP', 'DAP', 'DPU', 'DDP']
        },
        'trade.incoterm_location': {
            section: 'trade',
            path: 'shipment.trade_route.incoterm_location',
            type: 'text',
            label: 'Địa điểm Incoterm',
            placeholder: 'e.g., Shanghai Port'
        },
        'trade.priority': {
            section: 'trade',
            path: 'shipment.trade_route.priority',
            type: 'select',
            label: 'Mức độ ưu tiên',
            options: ['', 'STANDARD', 'EXPRESS', 'URGENT']
        },
        
        // Cargo fields
        'cargo.cargo_type': {
            section: 'cargo',
            path: 'shipment.cargo_packing.cargo_type',
            type: 'text',
            label: 'Loại hàng',
            placeholder: 'e.g., Electronics, Textiles'
        },
        'cargo.cargo_category': {
            section: 'cargo',
            path: 'shipment.cargo_packing.cargo_category',
            type: 'select',
            label: 'Nhóm hàng',
            options: ['', 'General Cargo', 'Electronics', 'Perishable', 'High Value', 'Fragile', 'Pharmaceuticals', 'Textiles']
        },
        'cargo.hs_code': {
            section: 'cargo',
            path: 'shipment.cargo_packing.hs_code',
            type: 'text',
            label: 'HS Code',
            placeholder: 'e.g., 8471.30'
        },
        'cargo.hs_chapter': {
            section: 'cargo',
            path: 'shipment.cargo_packing.hs_chapter',
            type: 'text',
            label: 'Chương HS',
            placeholder: 'e.g., 84'
        },
        'cargo.packing_type': {
            section: 'cargo',
            path: 'shipment.cargo_packing.packing_type',
            type: 'select',
            label: 'Đóng gói',
            options: ['', 'Pallet', 'Box', 'Crate', 'Bag', 'Drum', 'Bulk']
        },
        'cargo.packages': {
            section: 'cargo',
            path: 'shipment.cargo_packing.packages',
            type: 'number',
            label: 'Số kiện',
            placeholder: 'e.g., 100'
        },
        'cargo.gross_weight_kg': {
            section: 'cargo',
            path: 'shipment.cargo_packing.gross_weight_kg',
            type: 'number',
            label: 'Trọng lượng tổng (kg)',
            placeholder: 'e.g., 15000'
        },
        'cargo.net_weight_kg': {
            section: 'cargo',
            path: 'shipment.cargo_packing.net_weight_kg',
            type: 'number',
            label: 'Trọng lượng tịnh (kg)',
            placeholder: 'e.g., 14500'
        },
        'cargo.volume_cbm': {
            section: 'cargo',
            path: 'shipment.cargo_packing.volume_cbm',
            type: 'number',
            label: 'Thể tích (CBM)',
            placeholder: 'e.g., 65.5',
            step: '0.1'
        },
        'cargo.stackability': {
            section: 'cargo',
            path: 'shipment.cargo_packing.stackability',
            type: 'checkbox',
            label: 'Có thể xếp chồng'
        },
        'cargo.temp_control_required': {
            section: 'cargo',
            path: 'shipment.cargo_packing.temp_control_required',
            type: 'checkbox',
            label: 'Yêu cầu kiểm soát nhiệt độ'
        },
        'cargo.is_dg': {
            section: 'cargo',
            path: 'shipment.cargo_packing.is_dg',
            type: 'checkbox',
            label: 'Hàng nguy hiểm'
        },
        
        // Seller fields
        'seller.name': {
            section: 'seller',
            path: 'shipment.seller.name',
            type: 'text',
            label: 'Tên liên hệ',
            placeholder: 'e.g., John Smith'
        },
        'seller.company': {
            section: 'seller',
            path: 'shipment.seller.company',
            type: 'text',
            label: 'Tên công ty',
            placeholder: 'e.g., ABC Trading Co.'
        },
        'seller.email': {
            section: 'seller',
            path: 'shipment.seller.email',
            type: 'email',
            label: 'Email',
            placeholder: 'e.g., contact@company.com'
        },
        'seller.phone': {
            section: 'seller',
            path: 'shipment.seller.phone',
            type: 'tel',
            label: 'Điện thoại',
            placeholder: 'e.g., +1 555-0123'
        },
        'seller.address': {
            section: 'seller',
            path: 'shipment.seller.address',
            type: 'textarea',
            label: 'Địa chỉ',
            placeholder: 'Full address'
        },
        'seller.country': {
            section: 'seller',
            path: 'shipment.seller.country',
            type: 'text',
            label: 'Quốc gia',
            placeholder: 'e.g., CN, US'
        },
        
        // Buyer fields
        'buyer.name': {
            section: 'buyer',
            path: 'shipment.buyer.name',
            type: 'text',
            label: 'Tên liên hệ',
            placeholder: 'e.g., Jane Doe'
        },
        'buyer.company': {
            section: 'buyer',
            path: 'shipment.buyer.company',
            type: 'text',
            label: 'Tên công ty',
            placeholder: 'e.g., XYZ Imports Ltd.'
        },
        'buyer.email': {
            section: 'buyer',
            path: 'shipment.buyer.email',
            type: 'email',
            label: 'Email',
            placeholder: 'e.g., buyer@company.com'
        },
        'buyer.phone': {
            section: 'buyer',
            path: 'shipment.buyer.phone',
            type: 'tel',
            label: 'Điện thoại',
            placeholder: 'e.g., +49 123-456789'
        },
        'buyer.address': {
            section: 'buyer',
            path: 'shipment.buyer.address',
            type: 'textarea',
            label: 'Địa chỉ',
            placeholder: 'Full address'
        },
        'buyer.country': {
            section: 'buyer',
            path: 'shipment.buyer.country',
            type: 'text',
            label: 'Quốc gia',
            placeholder: 'e.g., DE, FR'
        }
    };
    
    /**
     * Render MEGA SUMMARY tile (5 columns)
     */
    function renderBanner(state, validationResults) {
        // Try MEGA SUMMARY first
        const megaGrid = document.getElementById('megaSummaryGrid');
        if (megaGrid) {
            const tiles = [
                {
                    label: 'Tuyến đường',
                    value: formatRoute(state),
                    fieldKey: 'trade.pol'
                },
                {
                    label: 'Phương thức',
                    value: state.shipment.trade_route.mode || 'Not set',
                    fieldKey: 'trade.mode'
                },
                {
                    label: 'Container',
                    value: state.shipment.trade_route.container_type || 'Not set',
                    fieldKey: 'trade.container_type'
                },
                {
                    label: 'Vận chuyển / ETD→ETA',
                    value: formatTransitAndDates(state),
                    fieldKey: 'trade.etd'
                },
                {
                    label: 'Trọng lượng / Thể tích',
                    value: formatWeightVolume(state),
                    fieldKey: 'cargo.gross_weight_kg'
                }
            ];
            
            megaGrid.innerHTML = tiles.map(tile => `
                <div class="mega-tile" data-field="${tile.fieldKey}">
                    <div class="mega-tile__label">${tile.label}</div>
                    <div class="mega-tile__value ${!tile.value || tile.value === 'Not set' ? 'mega-tile__value--empty' : ''}">
                        ${tile.value}
                    </div>
                </div>
            `).join('');
            return;
        }
        
        // Fallback to old banner grid
        const grid = document.getElementById('bannerGrid');
        if (!grid) return;
        
        const tiles = [
            {
                label: 'Route',
                value: formatRoute(state),
                fieldKey: 'trade.pol'
            },
            {
                label: 'Mode',
                value: state.shipment.trade_route.mode || 'Not set',
                fieldKey: 'trade.mode'
            },
            {
                label: 'Container',
                value: state.shipment.trade_route.container_type || 'Not set',
                fieldKey: 'trade.container_type'
            },
            {
                label: 'ETD → ETA',
                value: formatDateRange(state),
                fieldKey: 'trade.etd'
            },
            {
                label: 'Transit Time',
                value: state.shipment.trade_route.transit_time_days 
                    ? `${state.shipment.trade_route.transit_time_days} days` 
                    : 'Not set',
                fieldKey: 'trade.transit_time_days'
            },
            {
                label: 'Weight / Volume',
                value: formatWeightVolume(state),
                fieldKey: 'cargo.gross_weight_kg'
            },
            {
                label: 'HS Code',
                value: state.shipment.cargo_packing.hs_code || 'Not set',
                fieldKey: 'cargo.hs_code'
            },
            {
                label: 'Incoterm',
                value: formatIncoterm(state),
                fieldKey: 'trade.incoterm'
            }
        ];
        
        grid.innerHTML = tiles.map(tile => `
            <div class="banner-tile" data-field="${tile.fieldKey}">
                <div class="banner-tile__label">${tile.label}</div>
                <div class="banner-tile__value ${!tile.value || tile.value === 'Not set' ? 'banner-tile__value--empty' : ''}">
                    ${tile.value}
                </div>
            </div>
        `).join('');
    }
    
    /**
     * Format transit time and date range combined
     */
    function formatTransitAndDates(state) {
        const transit = state.shipment.trade_route.transit_time_days;
        const etd = state.shipment.trade_route.etd;
        const eta = state.shipment.trade_route.eta;
        
        const parts = [];
        if (transit) {
            parts.push(`${transit}d`);
        }
        if (etd && eta) {
            const etdStr = V400State.formatDate(etd);
            const etaStr = V400State.formatDate(eta);
            parts.push(`${etdStr} → ${etaStr}`);
        } else if (etd) {
            parts.push(`ETD: ${V400State.formatDate(etd)}`);
        }
        
        return parts.length > 0 ? parts.join(' / ') : 'Not set';
    }
    
    /**
     * Render panel content
     */
    function renderPanel(panelId, state, validationResults) {
        const panelBody = document.getElementById(`panel${capitalize(panelId)}`);
        if (!panelBody) return;
        
        const fields = Object.entries(FIELD_MAP)
            .filter(([key, config]) => config.section === panelId);
        
        panelBody.innerHTML = fields.map(([fieldKey, config]) => {
            const value = V400State.getValueAtPath(state, config.path);
            const fieldRules = V400Validator.getRulesForField(validationResults, config.path);
            const hasError = fieldRules.some(r => r.severity === 'critical');
            const hasWarning = fieldRules.some(r => r.severity === 'warning');
            
            return `
                <div class="field-tile ${hasError ? 'field-tile--error' : hasWarning ? 'field-tile--warning' : ''}" 
                     data-field="${fieldKey}">
                    <div class="field-tile__label">${config.label}</div>
                    <div class="field-tile__value ${V400State.isEmpty(value) ? 'field-tile__value--empty' : ''}">
                        ${formatFieldValue(value, config.type)}
                    </div>
                    ${fieldRules.length > 0 ? `
                        <div class="field-tile__status">
                            <span class="field-tile__status-icon">${hasError ? '⚠️' : hasWarning ? '⚡' : '💡'}</span>
                            <span class="field-tile__status-text">${fieldRules[0].message}</span>
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');
    }
    
    /**
     * Render all panels
     */
    function renderAllPanels(state, validationResults) {
        renderPanel('trade', state, validationResults);
        renderPanel('cargo', state, validationResults);
        renderPanel('seller', state, validationResults);
        renderPanel('buyer', state, validationResults);
    }
    
    /**
     * Format helpers
     */
    function formatRoute(state) {
        const pol = state.shipment.trade_route.pol;
        const pod = state.shipment.trade_route.pod;
        
        if (!pol && !pod) return 'Not set';
        if (!pol) return `→ ${pod}`;
        if (!pod) return `${pol} →`;
        
        return `${pol} → ${pod}`;
    }
    
    function formatDateRange(state) {
        const etd = state.shipment.trade_route.etd;
        const eta = state.shipment.trade_route.eta;
        
        if (!etd && !eta) return 'Not set';
        
        const etdStr = etd ? V400State.formatDate(etd) : '?';
        const etaStr = eta ? V400State.formatDate(eta) : '?';
        
        return `${etdStr} → ${etaStr}`;
    }
    
    function formatWeightVolume(state) {
        const weight = state.shipment.cargo_packing.gross_weight_kg;
        const volume = state.shipment.cargo_packing.volume_cbm;
        
        if (!weight && !volume) return 'Not set';
        
        const parts = [];
        if (weight) parts.push(`${weight.toLocaleString()} kg`);
        if (volume) parts.push(`${volume} CBM`);
        
        return parts.join(' / ');
    }
    
    function formatIncoterm(state) {
        const incoterm = state.shipment.trade_route.incoterm;
        const location = state.shipment.trade_route.incoterm_location;
        
        if (!incoterm) return 'Not set';
        if (!location) return incoterm;
        
        return `${incoterm} ${location}`;
    }
    
    function formatFieldValue(value, type) {
        if (V400State.isEmpty(value)) {
            return '<em>Not set</em>';
        }
        
        if (type === 'checkbox') {
            return value ? '✓ Yes' : '✗ No';
        }
        
        if (type === 'date') {
            return V400State.formatDate(value);
        }
        
        if (typeof value === 'number') {
            return value.toLocaleString();
        }
        
        return value;
    }
    
    function capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
    
    // Public API
    return {
        FIELD_MAP,
        renderBanner,
        renderPanel,
        renderAllPanels
    };
})();

