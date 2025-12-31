/**
 * ========================================================================
 * RISKCAST v20 - Validators
 * ========================================================================
 * Form validation utilities
 */

/**
 * Validate required fields in form data
 * @param {Object} formData - Form data object
 * @returns {Array<string>} Array of error field names
 */
export function validateRequiredFields(formData) {
    const errors = [];
    
    // Transport validation
    if (!formData.pol || formData.pol === '') {
        errors.push('POL (Port of Loading)');
    }
    if (!formData.pod || formData.pod === '') {
        errors.push('POD (Port of Discharge)');
    }
    
    // Cargo validation
    const cargoWeight = Number(formData.cargo?.weight || formData.cargo?.weights?.grossKg || 0);
    if (cargoWeight <= 0) {
        errors.push('Cargo Weight');
    }
    
    const cargoVolume = Number(formData.cargo?.volume || formData.cargo?.volumeCbm || 0);
    if (cargoVolume < 0) {
        errors.push('Cargo Volume');
    }
    
    // Seller validation
    const sellerCountry = formData.seller?.country?.name || formData.seller?.country || '';
    if (!sellerCountry || sellerCountry === '') {
        errors.push('Seller Country');
    }
    
    // Buyer validation
    const buyerCountry = formData.buyer?.country?.name || formData.buyer?.country || '';
    if (!buyerCountry || buyerCountry === '') {
        errors.push('Buyer Country');
    }
    
    return errors;
}

/**
 * Highlight error fields in the form
 * @param {Array<string>} fields - Array of field names with errors
 */
export function highlightErrors(fields) {
    // Remove existing error classes
    document.querySelectorAll('.rc-input-error').forEach(el => {
        el.classList.remove('rc-input-error');
    });
    
    // Add error class to missing fields
    fields.forEach(field => {
        // Try to find input by data-field attribute or by field name
        const fieldMap = {
            'POL (Port of Loading)': 'pol',
            'POD (Port of Discharge)': 'pod',
            'Cargo Weight': 'cargo.weight',
            'Cargo Volume': 'cargo.volume',
            'Seller Country': 'seller.country',
            'Buyer Country': 'buyer.country'
        };
        
        const fieldKey = fieldMap[field] || field.toLowerCase().replace(/\s+/g, '');
        const input = document.querySelector(`[data-field="${fieldKey}"]`) ||
                     document.querySelector(`#${fieldKey}`) ||
                     document.querySelector(`[name="${fieldKey}"]`);
        
        if (input) {
            input.classList.add('rc-input-error');
            input.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    });
}



