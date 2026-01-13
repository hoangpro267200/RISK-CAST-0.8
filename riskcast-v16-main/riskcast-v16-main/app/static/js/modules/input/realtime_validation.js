
import { qsa, on, $id } from '../../core/dom.js';
import { SmartInputState } from './state_management.js';

export function initRealtimeValidation() {
    
    const requiredFields = qsa('input[required], select[required]');
    
    requiredFields.forEach(field => {
        on(field, 'blur', () => validateField(field));
        on(field, 'input', () => {
            if (field.classList.contains('error-field')) {
                validateField(field);
            } else {
                markFieldValid(field);
            }
        });
    });
}

export function validateField(field) {
    const value = field.value.trim();
    const isRequired = field.hasAttribute('required');
    
    if (isRequired && !value) {
        field.classList.add('error-field');
        field.classList.remove('field-completed');
        return false;
    }
    
    field.classList.remove('error-field');
    markFieldValid(field);
    return true;
}

function markFieldValid(field) {
    if (field.value && field.value.trim()) {
        field.classList.add('field-completed');
        SmartInputState.completedFields.add(field.id);
    }
}

export function showError(fieldId, message) {
    const field = $id(fieldId);
    const errorElement = $id(fieldId + '_error') || 
                        field?.parentElement?.querySelector('.error-message');
    
    if (field) {
        field.classList.add('error-field');
        field.style.borderColor = '#ef4444';
    }
    
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }
}

export function clearError(fieldId) {
    const field = $id(fieldId);
    const errorElement = $id(fieldId + '_error') || 
                        field?.parentElement?.querySelector('.error-message');
    
    if (field) {
        field.classList.remove('error-field');
        field.style.borderColor = '';
    }
    
    if (errorElement) {
        errorElement.textContent = '';
        errorElement.style.display = 'none';
    }
}

