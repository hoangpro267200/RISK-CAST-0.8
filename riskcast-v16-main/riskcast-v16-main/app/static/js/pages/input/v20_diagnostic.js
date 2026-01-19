/**
 * RISKCAST v20 Diagnostic Tool
 * Paste this into browser console to check data loading
 */

console.log('🔍 RISKCAST v20 Diagnostic Starting...');

// Check if LOGISTICS_DATA loaded
if (typeof LOGISTICS_DATA !== 'undefined') {
    console.log('✅ LOGISTICS_DATA loaded');
    console.log('   Routes:', Object.keys(LOGISTICS_DATA.routes || {}).length);
    console.log('   Service Routes:', (LOGISTICS_DATA.serviceRoutes || []).length);
    console.log('   Cargo Types:', (LOGISTICS_DATA.cargoTypes || []).length);
    console.log('   Countries:', (LOGISTICS_DATA.countries || []).length);
} else {
    console.error('❌ LOGISTICS_DATA NOT LOADED');
}

// Check if controller initialized
if (typeof window.RC_V20 !== 'undefined') {
    console.log('✅ Controller initialized');
    console.log('   Current state:', window.RC_V20.formData);
} else {
    console.error('❌ Controller NOT initialized');
}

// Check dropdowns
const checkDropdown = (id, name) => {
    const dropdown = document.getElementById(id);
    if (dropdown) {
        const menu = document.getElementById(`${id}-menu`);
        const items = menu ? menu.querySelectorAll('.rc-dropdown-item, button') : [];
        console.log(`   ${name}: ${items.length} items`);
    } else {
        console.warn(`   ${name}: dropdown not found`);
    }
};

console.log('📊 Dropdown Status:');
checkDropdown('tradeLane', 'Trade Lane');
checkDropdown('mode', 'Mode');
checkDropdown('shipmentType', 'Shipment Type');
checkDropdown('serviceRoute', 'Service Route');
checkDropdown('carrier', 'Carrier');

// Test service route loading
console.log('\n🧪 Testing Service Route Loading...');
if (window.RC_V20) {
    const data = window.RC_V20.formData;
    console.log('Current selections:');
    console.log('   Trade Lane:', data.tradeLane || 'NOT SELECTED');
    console.log('   Mode:', data.mode || 'NOT SELECTED');
    console.log('   Shipment Type:', data.shipmentType || 'NOT SELECTED');
    console.log('   Priority:', data.priority || 'balanced');
    
    if (!data.tradeLane || !data.mode) {
        console.warn('⚠️ SERVICE ROUTES REQUIRE: Trade Lane + Mode to be selected first!');
        console.log('\n📝 To test service routes:');
        console.log('   1. Select a Trade Lane');
        console.log('   2. Select a Mode');
        console.log('   3. Service Routes will auto-load');
    } else {
        console.log('✅ Prerequisites met, checking service routes...');
        // Try to load service routes manually
        if (typeof window.RC_V20.loadServiceRoutes === 'function') {
            window.RC_V20.loadServiceRoutes();
        }
    }
}

console.log('\n🔍 Diagnostic Complete!');






