/**
 * EDIT PANEL - SMART EDIT MODE
 * Inline editing with slide-in panel
 */

(function() {
    'use strict';

    let editMode = false;
    let currentEditPath = null;
    let currentEditField = null;

    /**
     * Initialize edit mode toggle
     */
    function initEditModeToggle() {
        const toggle = document.getElementById('editModeToggle');
        if (!toggle) return;

        toggle.addEventListener('change', (e) => {
            editMode = e.target.checked;
            document.body.classList.toggle('edit-mode', editMode);
            console.log('[Edit Panel] Edit mode:', editMode ? 'ON' : 'OFF');
        });
    }

    /**
     * Initialize editable field clicks
     */
    function initEditableFields() {
        document.addEventListener('click', (e) => {
            if (!editMode) return;

            const editable = e.target.closest('.editable');
            if (!editable) return;

            const detailItem = editable.closest('.detail-item') || editable.closest('.factor-item');
            if (!detailItem) return;

            const field = detailItem.dataset.field;
            const card = detailItem.closest('.info-card');
            const editPath = card ? card.dataset.editPath : null;

            if (field && editPath) {
                openEditPanel(editPath, field, editable.textContent.trim());
            }
        });
    }

    /**
     * Open edit panel
     */
    function openEditPanel(path, field, currentValue) {
        currentEditPath = path;
        currentEditField = field;

        const panel = document.getElementById('editPanel');
        const title = document.getElementById('editPanelTitle');
        const body = document.getElementById('editPanelBody');

        if (!panel || !title || !body) return;

        // Set title
        title.textContent = `Edit ${path}.${field}`;

        // Generate form based on field type
        const form = generateEditForm(path, field, currentValue);
        body.innerHTML = form;

        // Open panel
        panel.classList.add('open');

        // Focus first input
        const firstInput = body.querySelector('input, select, textarea');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    }

    /**
     * Generate edit form based on field
     */
    function generateEditForm(path, field, currentValue) {
        const shipmentState = window.OverviewV33?.getShipmentState();
        if (!shipmentState) return '<p>No data available</p>';

        // Handle segments editing
        if (path === 'segments') {
            return generateSegmentsForm(shipmentState.segments || []);
        }

        // Handle simple field editing
        const fieldData = shipmentState[path]?.[field];
        const fieldType = getFieldType(path, field);

        let formHTML = '<div class="edit-form">';
        formHTML += `<div class="form-group">`;
        formHTML += `<label class="form-label">${field}</label>`;

        if (fieldType === 'select') {
            formHTML += generateSelectInput(path, field, currentValue);
        } else if (fieldType === 'number') {
            formHTML += `<input type="number" class="form-input" id="editValue" value="${currentValue}" step="0.1">`;
        } else if (fieldType === 'textarea') {
            formHTML += `<textarea class="form-textarea" id="editValue">${currentValue}</textarea>`;
        } else {
            formHTML += `<input type="text" class="form-input" id="editValue" value="${currentValue}">`;
        }

        formHTML += `</div>`;
        formHTML += `</div>`;

        return formHTML;
    }

    /**
     * Generate segments form
     */
    function generateSegmentsForm(segments) {
        let formHTML = '<div class="edit-form">';
        formHTML += '<div class="form-group">';
        formHTML += '<label class="form-label">Route Segments</label>';

        segments.forEach((segment, index) => {
            formHTML += `<div class="segment-editor" data-index="${index}">`;
            formHTML += `<div class="segment-header">`;
            formHTML += `<span class="segment-title">Segment ${index + 1}</span>`;
            formHTML += `<button type="button" class="btn-remove-segment" data-index="${index}">Remove</button>`;
            formHTML += `</div>`;
            formHTML += `<div class="form-group">`;
            formHTML += `<label class="form-label">From</label>`;
            formHTML += `<input type="text" class="form-input" data-field="from" value="${segment.from || ''}">`;
            formHTML += `</div>`;
            formHTML += `<div class="form-group">`;
            formHTML += `<label class="form-label">To</label>`;
            formHTML += `<input type="text" class="form-input" data-field="to" value="${segment.to || ''}">`;
            formHTML += `</div>`;
            formHTML += `<div class="coordinate-group">`;
            formHTML += `<div class="form-group">`;
            formHTML += `<label class="form-label">Latitude 1</label>`;
            formHTML += `<input type="number" class="form-input" data-field="lat1" value="${segment.lat1 || 0}" step="0.0001">`;
            formHTML += `</div>`;
            formHTML += `<div class="form-group">`;
            formHTML += `<label class="form-label">Longitude 1</label>`;
            formHTML += `<input type="number" class="form-input" data-field="lon1" value="${segment.lon1 || 0}" step="0.0001">`;
            formHTML += `</div>`;
            formHTML += `</div>`;
            formHTML += `<div class="coordinate-group">`;
            formHTML += `<div class="form-group">`;
            formHTML += `<label class="form-label">Latitude 2</label>`;
            formHTML += `<input type="number" class="form-input" data-field="lat2" value="${segment.lat2 || 0}" step="0.0001">`;
            formHTML += `</div>`;
            formHTML += `<div class="form-group">`;
            formHTML += `<label class="form-label">Longitude 2</label>`;
            formHTML += `<input type="number" class="form-input" data-field="lon2" value="${segment.lon2 || 0}" step="0.0001">`;
            formHTML += `</div>`;
            formHTML += `</div>`;
            formHTML += `<div class="form-group">`;
            formHTML += `<label class="form-label">Distance (km)</label>`;
            formHTML += `<input type="number" class="form-input" data-field="distance" value="${segment.distance || 0}" step="0.1">`;
            formHTML += `</div>`;
            formHTML += `<div class="form-group">`;
            formHTML += `<label class="form-label">Mode</label>`;
            formHTML += generateSelectInput('segments', 'mode', segment.mode || 'ocean', ['ocean', 'air', 'truck', 'rail']);
            formHTML += `</div>`;
            formHTML += `</div>`;
        });

        formHTML += `<button type="button" class="btn-add-segment">+ Add Segment</button>`;
        formHTML += `</div>`;
        formHTML += `</div>`;

        return formHTML;
    }

    /**
     * Generate select input
     */
    function generateSelectInput(path, field, currentValue, options = null) {
        let selectHTML = `<select class="form-select" id="editValue">`;

        if (field === 'mode') {
            const modeOptions = options || ['ocean', 'air', 'truck', 'rail'];
            modeOptions.forEach(opt => {
                const selected = opt === currentValue ? 'selected' : '';
                selectHTML += `<option value="${opt}" ${selected}>${opt.charAt(0).toUpperCase() + opt.slice(1)}</option>`;
            });
        } else {
            selectHTML += `<option value="${currentValue}">${currentValue}</option>`;
        }

        selectHTML += `</select>`;
        return selectHTML;
    }

    /**
     * Get field type
     */
    function getFieldType(path, field) {
        const numberFields = ['score', 'weight', 'volume', 'distance', 'lat1', 'lon1', 'lat2', 'lon2'];
        const selectFields = ['mode'];
        const textareaFields = [];

        if (numberFields.includes(field)) return 'number';
        if (selectFields.includes(field)) return 'select';
        if (textareaFields.includes(field)) return 'textarea';
        return 'text';
    }

    /**
     * Save changes
     */
    async function saveChanges() {
        const shipmentState = window.OverviewV33?.getShipmentState();
        if (!shipmentState) return;

        const body = document.getElementById('editPanelBody');
        if (!body) return;

        // Show loading
        const panel = document.getElementById('editPanel');
        const saving = document.createElement('div');
        saving.className = 'edit-panel-saving active';
        saving.innerHTML = '<div><div class="saving-spinner"></div><div class="saving-text">Saving...</div></div>';
        panel.appendChild(saving);

        try {
            // Collect form data
            if (currentEditPath === 'segments') {
                // Handle segments
                const segmentEditors = body.querySelectorAll('.segment-editor');
                const segments = Array.from(segmentEditors).map(editor => {
                    const inputs = editor.querySelectorAll('input, select');
                    const segment = {};
                    inputs.forEach(input => {
                        const field = input.dataset.field;
                        const value = input.type === 'number' ? parseFloat(input.value) : input.value;
                        segment[field] = value;
                    });
                    return segment;
                });
                shipmentState.segments = segments;
            } else {
                // Handle simple field
                const input = body.querySelector('#editValue');
                if (input) {
                    const value = input.type === 'number' ? parseFloat(input.value) : input.value;
                    if (!shipmentState[currentEditPath]) {
                        shipmentState[currentEditPath] = {};
                    }
                    shipmentState[currentEditPath][currentEditField] = value;
                }
            }

            // Send PATCH request
            const response = await fetch('/api/update_shipment', {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(shipmentState)
            });

            if (!response.ok) {
                throw new Error('Failed to save changes');
            }

            // Update UI and Cesium
            window.OverviewV33.setShipmentState(shipmentState);

            // Close panel
            closeEditPanel();

            console.log('[Edit Panel] Changes saved successfully');
        } catch (error) {
            console.error('[Edit Panel] Error saving:', error);
            alert('Failed to save changes. Please try again.');
        } finally {
            saving.remove();
        }
    }

    /**
     * Close edit panel
     */
    function closeEditPanel() {
        const panel = document.getElementById('editPanel');
        if (panel) {
            panel.classList.remove('open');
        }
        currentEditPath = null;
        currentEditField = null;
    }

    /**
     * Initialize event listeners
     */
    function init() {
        initEditModeToggle();
        initEditableFields();

        // Close button
        const closeBtn = document.getElementById('editPanelClose');
        if (closeBtn) {
            closeBtn.addEventListener('click', closeEditPanel);
        }

        // Cancel button
        const cancelBtn = document.getElementById('editPanelCancel');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', closeEditPanel);
        }

        // Save button
        const saveBtn = document.getElementById('editPanelSave');
        if (saveBtn) {
            saveBtn.addEventListener('click', saveChanges);
        }

        // Close on outside click
        document.addEventListener('click', (e) => {
            const panel = document.getElementById('editPanel');
            if (panel && panel.classList.contains('open')) {
                if (!panel.contains(e.target) && !e.target.closest('.editable')) {
                    // Don't close if clicking on editable field
                    if (!e.target.closest('.info-card')) {
                        closeEditPanel();
                    }
                }
            }
        });

        console.log('[Edit Panel] Initialized');
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();

