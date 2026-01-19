
(function() {
    'use strict';

    let rowCounter = 0;
    const packingData = [];
    let updateTimeout = null; // Debounce timer

    // Packaging types
    const packagingTypes = [
        'Carton',
        'Pallet',
        'Wooden Crate',
        'Bundle',
        'Loose',
        'Bag',
        'Drum',
        'Box'
    ];

    /**
     * Initialize packing list (only once)
     */
    function initPackingList() {
        // Prevent multiple initializations
        if (window.packingListInitialized) {
            return;
        }
        window.packingListInitialized = true;
        
        const addBtn = document.getElementById('add-packing-row');
        if (addBtn && !addBtn.dataset.listenerAdded) {
            addBtn.dataset.listenerAdded = 'true';
            addBtn.addEventListener('click', addPackingRow);
        }

        // Add initial row only if tbody is empty
        const tbody = document.getElementById('packing-list-tbody');
        if (tbody && tbody.children.length === 0) {
            addPackingRow();
        }

        // Listen for cargo value changes to update calculations (only once)
        const cargoValueInput = document.getElementById('cargo_value');
        if (cargoValueInput && !cargoValueInput.dataset.packingListenerAdded) {
            cargoValueInput.dataset.packingListenerAdded = 'true';
            cargoValueInput.addEventListener('input', updateCalculations);
        }
    }

    /**
     * Add new packing row
     */
    function addPackingRow() {
        rowCounter++;
        const tbody = document.getElementById('packing-list-tbody');
        if (!tbody) return;

        const row = document.createElement('tr');
        row.dataset.rowId = rowCounter;
        
        row.innerHTML = `
            <td>${rowCounter}</td>
            <td>
                <input type="text" class="packing-input" placeholder="Mô tả hàng hóa" 
                       data-field="description" data-row="${rowCounter}">
            </td>
            <td>
                <input type="number" class="packing-input" placeholder="0" min="1" 
                       data-field="quantity" data-row="${rowCounter}" value="1">
            </td>
            <td>
                <select class="packing-select" data-field="packaging" data-row="${rowCounter}">
                    ${packagingTypes.map(type => `<option value="${type}">${type}</option>`).join('')}
                </select>
            </td>
            <td>
                <div class="dimensions-input-group">
                    <input type="number" class="packing-input" placeholder="Dài" min="0" step="0.1"
                           data-field="length" data-row="${rowCounter}">
                    <input type="number" class="packing-input" placeholder="Rộng" min="0" step="0.1"
                           data-field="width" data-row="${rowCounter}">
                    <input type="number" class="packing-input" placeholder="Cao" min="0" step="0.1"
                           data-field="height" data-row="${rowCounter}">
                </div>
            </td>
            <td>
                <input type="number" class="packing-input" placeholder="0" min="0" step="0.1"
                       data-field="weight" data-row="${rowCounter}">
            </td>
            <td>
                <div class="stackable-toggle">
                    <div class="toggle-switch" data-field="stackable" data-row="${rowCounter}"></div>
                </div>
            </td>
            <td>
                <button type="button" class="delete-row-btn" onclick="deletePackingRow(${rowCounter})">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 6L6 18M6 6L18 18" stroke-linecap="round"/>
                    </svg>
                </button>
            </td>
        `;

        tbody.appendChild(row);

        // Add event listeners
        setupRowListeners(row);

        // Update calculations immediately
        performCalculations();
    }

    /**
     * Setup event listeners for a row (avoid duplicates)
     */
    function setupRowListeners(row) {
        // Check if row already has listeners
        if (row.dataset.listenersAdded === 'true') {
            return;
        }
        row.dataset.listenersAdded = 'true';
        
        const inputs = row.querySelectorAll('input, select');
        inputs.forEach(input => {
            // Check if input already has listener
            if (input.dataset.hasListener === 'true') {
                return;
            }
            input.dataset.hasListener = 'true';
            
            // Input event - debounced calculation for better performance
            input.addEventListener('input', function() {
                updateCalculations();
            });
            
            // Change event - immediate update when user finishes (blur, select change, etc.)
            input.addEventListener('change', function() {
                // Clear debounce and calculate immediately
                if (updateTimeout) {
                    clearTimeout(updateTimeout);
                }
                performCalculations();
            });
            
            // Blur event - ensure calculation runs when user leaves field
            input.addEventListener('blur', function() {
                if (updateTimeout) {
                    clearTimeout(updateTimeout);
                }
                performCalculations();
            });
        });

        // Toggle switch - immediate calculation
        const toggle = row.querySelector('.toggle-switch');
        if (toggle && !toggle.dataset.hasListener) {
            toggle.dataset.hasListener = 'true';
            toggle.addEventListener('click', function() {
                this.classList.toggle('active');
                // Clear debounce and calculate immediately for toggle
                if (updateTimeout) {
                    clearTimeout(updateTimeout);
                }
                performCalculations();
            });
        }
    }

    /**
     * Delete packing row
     */
    window.deletePackingRow = function(rowId) {
        const row = document.querySelector(`tr[data-row-id="${rowId}"]`);
        if (row) {
            row.remove();
            updateRowNumbers();
            updateCalculations();
        }
    };

    /**
     * Update row numbers
     */
    function updateRowNumbers() {
        const rows = document.querySelectorAll('#packing-list-tbody tr');
        rows.forEach((row, index) => {
            row.querySelector('td:first-child').textContent = index + 1;
        });
    }

    /**
     * Update all calculations (with minimal debouncing for better UX)
     */
    function updateCalculations() {
        // Clear previous timeout to debounce
        if (updateTimeout) {
            clearTimeout(updateTimeout);
        }
        
        // Reduced debounce: wait 150ms after user stops typing before updating (faster response, prevent duplicate)
        updateTimeout = setTimeout(() => {
            performCalculations();
        }, 150);
    }
    
    /**
     * Perform actual calculations (called after debounce) - prevent duplicate execution
     */
    let isCalculating = false;
    function performCalculations() {
        // Prevent duplicate calculations
        if (isCalculating) {
            return;
        }
        isCalculating = true;
        
        try {
            const rows = document.querySelectorAll('#packing-list-tbody tr');
            let totalPackages = 0;
            let totalWeight = 0;
            let totalVolume = 0;
            let stackableCount = 0;
            let totalItems = 0;

            // Use Set to track processed rows and prevent duplicates
            const processedRows = new Set();
            
            rows.forEach(row => {
                const rowId = row.dataset.rowId;
                if (!rowId || processedRows.has(rowId)) {
                    return; // Skip if already processed
                }
                processedRows.add(rowId);
                
                const quantity = parseFloat(row.querySelector('[data-field="quantity"]')?.value || 0);
                const length = parseFloat(row.querySelector('[data-field="length"]')?.value || 0);
                const width = parseFloat(row.querySelector('[data-field="width"]')?.value || 0);
                const height = parseFloat(row.querySelector('[data-field="height"]')?.value || 0);
                const weight = parseFloat(row.querySelector('[data-field="weight"]')?.value || 0);
                const isStackable = row.querySelector('.toggle-switch')?.classList.contains('active');

                // Only count rows with valid quantity
                if (quantity > 0) {
                    totalPackages += quantity;
                    totalWeight += weight * quantity;
                    
                    // Volume in m³ (convert cm to m) - only if all dimensions are provided
                    if (length > 0 && width > 0 && height > 0) {
                        const volumePerUnit = (length * width * height) / 1000000; // cm³ to m³
                        totalVolume += volumePerUnit * quantity;
                    }

                    if (isStackable) stackableCount += quantity;
                    totalItems++;
                }
            });

            // Chargeable weight (volumetric 1:167 for sea)
            const volumetricWeight = totalVolume * 167;
            const chargeableWeight = Math.max(totalWeight, volumetricWeight);

            // Container utilization (40HQ = 67.7 m³)
            const containerVolume = 67.7; // 40HQ
            const utilization = totalVolume > 0 ? Math.min((totalVolume / containerVolume) * 100, 100) : 0;

            // Packing quality score (0-10)
            const stackableRatio = totalPackages > 0 ? stackableCount / totalPackages : 0;
            const weightDistribution = totalItems > 0 ? Math.min(totalItems / 10, 1) : 0; // More items = better distribution
            const packagingScore = calculatePackagingScore(rows);
            const packingScore = (stackableRatio * 4 + weightDistribution * 3 + packagingScore * 3).toFixed(1);

            // Update UI - prevent flickering by checking if values changed
            updateCalcDisplay('calc-total-packages', totalPackages.toLocaleString('vi-VN'));
            updateCalcDisplay('calc-total-weight', totalWeight.toLocaleString('vi-VN', {maximumFractionDigits: 0}));
            updateCalcDisplay('calc-total-volume', totalVolume > 0 ? totalVolume.toFixed(1) : '0.0');
            updateCalcDisplay('calc-chargeable-weight', chargeableWeight.toLocaleString('vi-VN', {maximumFractionDigits: 0}));
            
            // Container Utilization - ensure % symbol is always displayed
            const utilElement = document.getElementById('calc-container-util');
            if (utilElement) {
                const utilText = utilization > 0 ? utilization.toFixed(1) : '0.0';
                // Only update if value actually changed
                if (utilElement.textContent !== utilText + '%') {
                    utilElement.textContent = utilText + '%';
                }
            }
            
            updateCalcDisplay('calc-packing-score', packingScore);

            // Update progress bar
            const progressBar = document.getElementById('util-progress-bar');
            if (progressBar) {
                progressBar.style.width = `${utilization}%`;
            }

            // Update hidden input for form submission
            const packagesInput = document.getElementById('packages');
            if (packagesInput) {
                packagesInput.value = totalPackages;
            }

            // Update summary dashboard
            updateSummaryDashboard(totalPackages, totalWeight, totalVolume);
            
        } finally {
            // Always reset calculating flag
            isCalculating = false;
        }
    }

    /**
     * Calculate packaging score based on packaging types
     */
    function calculatePackagingScore(rows) {
        const packagingScores = {
            'Pallet': 1.0,
            'Wooden Crate': 0.9,
            'Carton': 0.8,
            'Box': 0.7,
            'Bundle': 0.6,
            'Bag': 0.5,
            'Drum': 0.4,
            'Loose': 0.2
        };

        let totalScore = 0;
        let count = 0;

        rows.forEach(row => {
            const packaging = row.querySelector('[data-field="packaging"]')?.value;
            if (packaging && packagingScores[packaging]) {
                totalScore += packagingScores[packaging];
                count++;
            }
        });

        return count > 0 ? totalScore / count : 0;
    }

    /**
     * Update calculation display (prevent duplicate updates)
     */
    function updateCalcDisplay(id, value) {
        const el = document.getElementById(id);
        if (el) {
            // Only update if value actually changed
            if (el.textContent !== value) {
                el.textContent = value;
            }
        }
    }

    /**
     * Update summary dashboard
     */
    function updateSummaryDashboard(packages, weight, volume) {
        const summaryPackages = document.getElementById('summary-packages');
        if (summaryPackages) {
            summaryPackages.textContent = `${packages.toLocaleString('vi-VN')} đơn vị`;
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPackingList);
    } else {
        initPackingList();
    }

    // Export for external use
    window.PackingList = {
        addRow: addPackingRow,
        updateCalculations: updateCalculations,
        getData: () => packingData
    };

})();
