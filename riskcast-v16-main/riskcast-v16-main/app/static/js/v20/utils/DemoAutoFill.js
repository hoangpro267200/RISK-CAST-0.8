/**
 * ========================================================================
 * RISKCAST v20 - Demo Auto-Fill
 * ========================================================================
 * Auto-fills form with realistic demo data for testing
 * 
 * @class DemoAutoFill
 */
export class DemoAutoFill {
    /**
     * @param {Object} controller - Main controller instance (for accessing methods)
     */
    constructor(controller) {
        this.controller = controller;
    }
    
    /**
     * Initialize auto-fill demo button
     */
    init() {
        const demoBtn = document.getElementById('rc-auto-demo');
        if (!demoBtn) return;
        
        demoBtn.addEventListener('click', () => {
            if (demoBtn.disabled) return;
            demoBtn.disabled = true;
            this.run();
            setTimeout(() => { demoBtn.disabled = false; }, 1500);
        });
        
        console.log('🔥 Auto-Fill Demo button initialized ✓');
    }
    
    /**
     * Run auto-fill demo with realistic data
     */
    run() {
        console.log('🔥 Auto-Fill Demo v20.8 starting (FULL FORM)...');
        
        // Guard
        if (!this.controller.logisticsData) {
            this.controller.showToast('Loading logistics data... Please wait', 'info');
            setTimeout(() => this.run(), 800);
            return;
        }
        
        const routes = this.controller.logisticsData.routes;
        const laneKeys = Object.keys(routes);
        
        // 1. Weighted random trade lanes
        const weighted = [
            'vn_us', 'vn_us', 'vn_us',
            'vn_cn', 'vn_cn',
            'vn_eu', 'vn_eu',
            'vn_kr', 'vn_jp', 'vn_hk', 'vn_tw', 'vn_in', 'vn_th', 'domestic',
            ...laneKeys
        ];
        const tradeKey = weighted[Math.floor(Math.random() * weighted.length)];
        const lane = routes[tradeKey];
        
        // 2. Select trade lane (via transportModule)
        if (this.controller.transportModule) {
            this.controller.transportModule.selectTradeLane(tradeKey, lane.name);
        } else {
            console.warn('⚠️ TransportModule not available');
            return;
        }
        
        // 3. Select mode (weighted)
        setTimeout(() => {
            const modePool = ['SEA', 'SEA', 'SEA', 'SEA', 'AIR', 'AIR', 'ROAD', 'RAIL'];
            const mode = modePool[Math.floor(Math.random() * modePool.length)];
            const modeLabel = {
                SEA: 'Sea Freight',
                AIR: 'Air Freight',
                ROAD: 'Road Transport',
                RAIL: 'Rail Transport'
            }[mode];
            if (this.controller.transportModule) {
                this.controller.transportModule.selectMode(mode, modeLabel);
            }
        }, 150);
        
        // 4. Select shipment type
        setTimeout(() => {
            const menu = document.getElementById('shipmentType-menu');
            if (menu && menu.children.length > 0) {
                const index = Math.random() > 0.7 ? Math.floor(Math.random() * menu.children.length) : 0;
                menu.children[index].click();
            }
            if (this.controller.transportModule) {
                this.controller.transportModule.loadServiceRoutes();
            }
        }, 300);
        
        // 5. Select service route (priority-aware with retries)
        setTimeout(() => {
            this.autoSelectServiceRoute();
        }, 450);
        
        // 6. Set priority
        setTimeout(() => {
            const weights = ['balanced', 'balanced', 'balanced', 'fastest', 'cheapest', 'reliable'];
            const value = weights[Math.floor(Math.random() * weights.length)];
            if (this.controller.stateManager) {
                this.controller.stateManager.setState('priority', value);
            } else if (this.controller.formData) {
                this.controller.formData.priority = value;
            }
            
            const pills = document.querySelectorAll('.rc-pill-group[data-field="priority"] .rc-pill');
            pills.forEach(p => p.classList.remove('active'));
            const pick = document.querySelector(`.rc-pill[data-value="${value}"]`);
            if (pick) pick.classList.add('active');
        }, 600);
        
        // 7. Container type
        setTimeout(() => {
            if (this.controller.transportModule) {
                this.controller.transportModule.loadContainerTypes();
            }
            setTimeout(() => {
                const menu = document.getElementById('containerType-menu');
                if (menu && menu.children.length > 0) {
                    const index = Math.random() > 0.7 ? Math.floor(Math.random() * menu.children.length) : 0;
                    menu.children[index].click();
                }
            }, 50);
        }, 650);
        
        // 8. ETD + ETA
        setTimeout(async () => {
            const { generateRealisticDate } = await import('./DateCalculators.js');
            const etd = generateRealisticDate(2, 6);
            const etdInput = document.getElementById('etd');
            if (etdInput) {
                etdInput.value = etd;
                if (this.controller.stateManager) {
                    this.controller.stateManager.setState('etd', etd);
                } else if (this.controller.formData) {
                    this.controller.formData.etd = etd;
                }
            }
            if (this.controller.calculateETA) {
                this.controller.calculateETA();
            }
        }, 750);
        
        // 9. Incoterm
        setTimeout(() => {
            const incoterms = ['FOB', 'CIF', 'EXW', 'DDP', 'FCA'];
            const randomIncoterm = incoterms[Math.floor(Math.random() * incoterms.length)];
            if (this.controller.transportModule) {
                this.controller.transportModule.selectIncoterm(randomIncoterm);
            }
            
            // Incoterm location
            const locationInput = document.getElementById('incotermLocation');
            if (locationInput) {
                const locations = ['Shanghai', 'Los Angeles', 'Rotterdam', 'Singapore', 'Hamburg'];
                locationInput.value = locations[Math.floor(Math.random() * locations.length)];
                if (this.controller.stateManager) {
                    this.controller.stateManager.setState('incotermLocation', locationInput.value);
                } else if (this.controller.formData) {
                    this.controller.formData.incotermLocation = locationInput.value;
                }
            }
        }, 750);
        
        // 10. POL/POD from service route
        setTimeout(() => {
            const formData = this.controller.stateManager ? this.controller.stateManager.getState() : this.controller.formData || {};
            this.fillPolPodFromRoute(formData.serviceRouteData);
        }, 850);
        
        // 11. Cargo section
        setTimeout(() => {
            this.autoFillCargoDemo(tradeKey);
        }, 950);
        
        // 12. Seller & Buyer section
        setTimeout(() => {
            this.autoFillPartyDemo(tradeKey);
        }, 1050);
        
        // 13. Final touches
        setTimeout(() => {
            this.controller.onFormDataChange();
            if (this.controller.toastManager) {
                this.controller.toastManager.showToast('Demo shipment loaded successfully', 'success');
            }
            
            const form = document.querySelector('.rc-form-panel');
            if (form) {
                form.classList.add('rc-demo-pulse');
                setTimeout(() => form.classList.remove('rc-demo-pulse'), 1600);
            }
            
            window.scrollTo({ top: 0, behavior: 'smooth' });
            console.log('✨ Auto-Fill Demo v20.8 completed (FULL FORM).');
        }, 1350);
    }
    
    /**
     * Auto-fill Cargo Section with realistic data
     * @param {string} tradeKey - Trade lane key
     */
    autoFillCargoDemo(tradeKey) {
        // Cargo Type
        const cargoMenu = document.getElementById('cargoType-menu');
        if (cargoMenu && cargoMenu.children.length > 0) {
            cargoMenu.children[0].click();
        }
        
        // Packing Type
        const packingMenu = document.getElementById('packingType-menu');
        if (packingMenu && packingMenu.children.length > 0) {
            packingMenu.children[0].click();
        }
        
        // Insurance Coverage
        const insMenu = document.getElementById('insuranceCoverage-menu');
        if (insMenu && insMenu.children.length > 0) {
            insMenu.children[0].click();
        }
        
        // Basic numeric fields
        const fields = {
            hsCode: '850440',
            packageCount: '800',
            grossWeight: '15000',
            netWeight: '14200',
            volumeCbm: '68.5',
            insuranceValue: tradeKey === 'vn_us' ? '250000' : '120000',
            cargoDescription: 'Electronics – mixed cartons on pallets'
        };
        
        Object.entries(fields).forEach(([id, value]) => {
            const el = document.getElementById(id);
            if (el) {
                el.value = value;
                el.dispatchEvent(new Event('input', { bubbles: true }));
            }
        });
        
        // Stackable = true
        const stackGroup = document.getElementById('stackableGroup');
        if (stackGroup) {
            const yes = stackGroup.querySelector('.rc-pill[data-value="true"]');
            if (yes) yes.click();
        }
        
        // Sensitivity = standard
        const sensGroup = document.getElementById('sensitivityGroup');
        if (sensGroup) {
            const pill = sensGroup.querySelector('.rc-pill[data-value="standard"]');
            if (pill) pill.click();
        }
        
        // DG = false
        const dgGroup = document.getElementById('dgGroup');
        if (dgGroup) {
            const no = dgGroup.querySelector('.rc-pill[data-value="false"]');
            if (no) no.click();
        }
    }
    
    /**
     * Auto-fill Seller & Buyer Section with realistic data
     * @param {string} tradeKey - Trade lane key
     */
    autoFillPartyDemo(tradeKey) {
        const mapBuyerISO = {
            vn_us: 'US',
            vn_eu: 'NL',
            vn_kr: 'KR',
            vn_jp: 'JP',
            vn_cn: 'CN',
            vn_hk: 'HK',
            vn_tw: 'TW',
            vn_in: 'IN',
            vn_th: 'TH',
            domestic: 'VN'
        };
        
        const sellerISO = 'VN';
        const buyerISO = mapBuyerISO[tradeKey] || 'US';
        
        const findCountryLabel = (iso2) => {
            if (!this.controller.logisticsData || !this.controller.logisticsData.countries) return null;
            const c = this.controller.logisticsData.countries.find(c => c.iso2 === iso2);
            return c ? `${c.emoji} ${c.name}` : null;
        };
        
        // Seller country dropdown
        const sellerMenu = document.getElementById('sellerCountry-menu');
        if (sellerMenu) {
            const btn = Array.from(sellerMenu.children).find(
                el => el.getAttribute('data-value') === sellerISO
            );
            if (btn) btn.click();
        }
        
        // Buyer country dropdown
        const buyerMenu = document.getElementById('buyerCountry-menu');
        if (buyerMenu) {
            const btn = Array.from(buyerMenu.children).find(
                el => el.getAttribute('data-value') === buyerISO
            );
            if (btn) btn.click();
        }
        
        // Business type dropdowns
        const sellerBizMenu = document.getElementById('sellerBusinessType-menu');
        if (sellerBizMenu && sellerBizMenu.children.length > 0) {
            sellerBizMenu.children[0].click();
        }
        const buyerBizMenu = document.getElementById('buyerBusinessType-menu');
        if (buyerBizMenu && buyerBizMenu.children.length > 0) {
            buyerBizMenu.children[0].click();
        }
        
        // Seller text inputs
        const mapSeller = {
            sellerCompany: 'VN Tech Components Co., Ltd.',
            sellerCity: 'Ho Chi Minh City',
            sellerAddress: 'Lot A2, Hi-Tech Park, District 9',
            sellerContact: 'Nguyen Minh Anh',
            sellerContactRole: 'Export Manager',
            sellerEmail: 'export@vn-components.com',
            sellerPhone: '+84 28 1234 5678',
            sellerTaxId: '0312345678'
        };
        
        Object.entries(mapSeller).forEach(([id, value]) => {
            const el = document.getElementById(id);
            if (el) {
                el.value = value;
                el.dispatchEvent(new Event('input', { bubbles: true }));
            }
        });
        
        // Buyer text inputs
        const buyerCity = buyerISO === 'US' ? 'Los Angeles' :
                          buyerISO === 'NL' ? 'Rotterdam' :
                          buyerISO === 'JP' ? 'Tokyo' : 'Global City';
        
        const mapBuyer = {
            buyerCompany: 'Global Retail Distribution Inc.',
            buyerCity,
            buyerAddress: 'Distribution Center, Industrial Zone',
            buyerContact: 'Sarah Johnson',
            buyerContactRole: 'Logistics Director',
            buyerEmail: 'logistics@global-retail.com',
            buyerPhone: '+1 310 555 0199',
            buyerTaxId: 'US-99-1234567'
        };
        
        Object.entries(mapBuyer).forEach(([id, value]) => {
            const el = document.getElementById(id);
            if (el) {
                el.value = value;
                el.dispatchEvent(new Event('input', { bubbles: true }));
            }
        });
    }
    
    /**
     * Auto-select a service route for demo (priority-aware, retries)
     * @param {number} attempt - Current attempt number
     */
    autoSelectServiceRoute(attempt = 0) {
        const maxAttempts = 5;
        
        const formData = this.controller.stateManager ? this.controller.stateManager.getState() : this.controller.formData || {};
        
        if (!this.controller.logisticsData || !formData.tradeLane || !formData.mode) {
            if (attempt < maxAttempts) {
                setTimeout(() => this.autoSelectServiceRoute(attempt + 1), 120);
            }
            return;
        }
        
        // Pull available routes (same filters as UI)
        let routes = this.controller.logisticsData.getServiceRoutes(
            formData.tradeLane,
            formData.mode
        ) || [];
        
        if (formData.shipmentType) {
            routes = routes.filter(r => !r.shipmentType || r.shipmentType === formData.shipmentType);
        }
        
        if (!routes.length) {
            if (attempt < maxAttempts) {
                setTimeout(() => this.autoSelectServiceRoute(attempt + 1), 120);
            }
            return;
        }
        
        // Sort according to current priority (mirrors loadServiceRoutes)
        const priority = formData.priority || 'balanced';
        routes = [...routes];
        
        if (priority === 'fastest') {
            routes.sort((a, b) => (a.transit_days || 999) - (b.transit_days || 999));
        } else if (priority === 'cheapest') {
            routes.sort((a, b) => (a.cost || 999999) - (b.cost || 999999));
        } else if (priority === 'reliable') {
            routes.sort((a, b) => (b.reliability || 0) - (a.reliability || 0));
        } else if (priority === 'balanced') {
            routes = routes
                .map(r => ({ 
                    ...r, 
                    _compositeScore: this.controller.priorityManager 
                        ? this.controller.priorityManager.calculatePriorityScore(r, 'balanced')
                        : 50
                }))
                .sort((a, b) => b._compositeScore - a._compositeScore);
        }
        
        // Pick recommended (first) most of the time
        const index = Math.random() > 0.7 ? Math.floor(Math.random() * routes.length) : 0;
        if (this.controller.transportModule && routes[index]) {
            this.controller.transportModule.selectServiceRoute(routes[index]);
        }
    }
    
    /**
     * Fill POL/POD from selected service route with retry (demo helper)
     * @param {Object} routeData - Route data object
     * @param {number} attempt - Current attempt number
     */
    fillPolPodFromRoute(routeData, attempt = 0) {
        const maxAttempts = 3;
        const formData = this.controller.stateManager ? this.controller.stateManager.getState() : this.controller.formData || {};
        const data = routeData || formData.serviceRouteData;
        
        if (!data) {
            if (attempt < maxAttempts) {
                setTimeout(() => this.fillPolPodFromRoute(null, attempt + 1), 140);
            }
            return;
        }
        
        if (data.pol && this.controller.selectPOL) {
            this.controller.selectPOL(data.pol_code || data.pol, data.pol);
        }
        if (data.pod && this.controller.selectPOD) {
            this.controller.selectPOD(data.pod_code || data.pod, data.pod);
        }
        
        // Retry if either field is still empty (race protection)
        const currentState = this.controller.stateManager ? this.controller.stateManager.getState() : this.controller.formData || {};
        if ((!(currentState.pol) || !(currentState.pod)) && attempt < maxAttempts) {
            setTimeout(() => this.fillPolPodFromRoute(data, attempt + 1), 140);
        }
    }
}

