
import { $id, qs, qsa } from '../../core/dom.js';

export function toggleClimate() {
    const climateSection = qs('.climate-section');
    const climateContent = qs('.climate-content');
    
    if (!climateSection) return;
    
    climateSection.classList.toggle('expanded');
    if (climateContent) {
        climateContent.style.display = climateSection.classList.contains('expanded') ? 'block' : 'none';
    }
}

export function resetForm() {
    const form = $id('risk_form');
    if (!form) return;
    
    if (confirm('Bạn có chắc chắn muốn reset form? Tất cả dữ liệu sẽ bị xóa.')) {
        form.reset();
        
        // Clear all custom dropdowns
        qsa('.custom-dropdown .dropdown-value').forEach(el => {
            el.textContent = el.getAttribute('data-placeholder') || 'Chọn tùy chọn';
            el.classList.add('placeholder');
        });
        
        // Clear hidden inputs
        qsa('input[type="hidden"]').forEach(input => {
            if (!input.id.includes('_csrf')) {
                input.value = '';
            }
        });
        
        // Remove has-value classes
        qsa('.has-value').forEach(el => {
            el.classList.remove('has-value');
        });
        
    }
}

export function getFormData() {
    const form = $id('risk_form');
    if (!form) return {};
    
    const formData = new FormData(form);
    const data = {};
    
    for (const [key, value] of formData.entries()) {
        if (data[key]) {
            // Handle multiple values
            if (Array.isArray(data[key])) {
                data[key].push(value);
            } else {
                data[key] = [data[key], value];
            }
        } else {
            data[key] = value;
        }
    }
    
    return data;
}

// Export to window for backward compatibility
if (typeof window !== 'undefined') {
    window.toggleClimate = toggleClimate;
    window.resetForm = resetForm;
    window.getFormData = getFormData;
}

