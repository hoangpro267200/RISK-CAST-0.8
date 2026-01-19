
import { $id, on } from '../../core/dom.js';
import { SmartInputState } from './state_management.js';

export function initCountryAutoSuggest() {
    
    const sellerDropdown = $id('seller_country_dropdown') || 
                           document.querySelector('[id*="seller_country"]');
    const buyerDropdown = $id('buyer_country_dropdown') || 
                          document.querySelector('[id*="buyer_country"]');
    
    if (!sellerDropdown || !buyerDropdown) {
        return;
    }
    
    on(sellerDropdown, 'change', () => handleCountryChange());
    on(buyerDropdown, 'change', () => handleCountryChange());
}

function handleCountryChange() {
    const sellerCountry = getDropdownValue('seller_country_dropdown') || 
                         getDropdownValue('seller_country');
    const buyerCountry = getDropdownValue('buyer_country_dropdown') || 
                        getDropdownValue('buyer_country');
    
    if (!sellerCountry || !buyerCountry) {
        return;
    }
    
    autoSuggestRoute(sellerCountry, buyerCountry);
}

function autoSuggestRoute(seller, buyer) {
    
    let routeKey = null;
    
    if (seller === 'vn' || seller === 'vietnam') {
        if (buyer === 'us' || buyer === 'united_states') routeKey = 'vn_us';
        else if (buyer === 'cn' || buyer === 'china') routeKey = 'vn_cn';
        else if (buyer === 'kr' || buyer === 'south_korea') routeKey = 'vn_kr';
        else if (buyer === 'jp' || buyer === 'japan') routeKey = 'vn_jp';
        else if (buyer === 'eu' || buyer === 'nl' || buyer === 'de' || buyer === 'europe') routeKey = 'vn_eu';
        else if (buyer === 'hk' || buyer === 'hong_kong') routeKey = 'vn_hk';
        else if (buyer === 'in' || buyer === 'india') routeKey = 'vn_in';
        else if (buyer === 'th' || buyer === 'thailand') routeKey = 'vn_th';
        else if (buyer === 'tw' || buyer === 'taiwan') routeKey = 'vn_tw';
    }
    
    if (seller === buyer || (seller === 'vn' && buyer === 'vn')) {
        routeKey = 'domestic';
    }
    
    const LOGISTICS_DATA = SmartInputState.getLogisticsData();
    if (!LOGISTICS_DATA) return;
    if (routeKey && LOGISTICS_DATA.routes[routeKey]) {
        const routeData = LOGISTICS_DATA.routes[routeKey];
        
        setTimeout(() => {
            selectDropdownOption('route_dropdown', routeKey);
            SmartInputState.selectedRoute = routeKey;
            if (typeof window !== 'undefined' && window.handleRouteSelection) {
                window.handleRouteSelection(routeKey);
            }
        }, 200);
    }
}

function getDropdownValue(dropdownId) {
    const dropdown = $id(dropdownId);
    if (!dropdown) return null;
    
    const hiddenInput = $id(dropdownId.replace('_dropdown', '_input'));
    if (hiddenInput && hiddenInput.value) {
        return hiddenInput.value;
    }
    
    const selectedOption = dropdown.querySelector('.dropdown-option.selected');
    if (selectedOption) {
        return selectedOption.getAttribute('data-value');
    }
    
    return dropdown.value || null;
}

function selectDropdownOption(dropdownId, value) {
    const dropdown = $id(dropdownId);
    if (!dropdown) return;
    
    if (dropdown.tagName === 'SELECT') {
        dropdown.value = value;
        dropdown.dispatchEvent(new Event('change', { bubbles: true }));
    } else {
        const option = dropdown.querySelector(`.dropdown-option[data-value="${value}"]`);
        if (option) {
            option.click();
        }
    }
}

