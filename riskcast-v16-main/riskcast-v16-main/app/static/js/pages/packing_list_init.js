
(function() {
    'use strict';

    function forceInitPackingList() {
        const tbody = document.getElementById('packing-list-tbody');
        const addBtn = document.getElementById('add-packing-row');
        
        if (tbody && tbody.children.length === 0) {
            // If no rows, try to add one using the exported function
            if (window.PackingList && typeof window.PackingList.addRow === 'function') {
                window.PackingList.addRow();
            } else if (addBtn) {
                // Fallback: trigger click on add button
                addBtn.click();
            } else {
                // Last resort: manually create a row
                setTimeout(function() {
                    if (tbody.children.length === 0 && addBtn) {
                        addBtn.click();
                    }
                }, 500);
            }
        }
    }
    
    // Try multiple times to ensure it runs
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(forceInitPackingList, 100);
            setTimeout(forceInitPackingList, 500);
            setTimeout(forceInitPackingList, 1000);
        });
    } else {
        setTimeout(forceInitPackingList, 100);
        setTimeout(forceInitPackingList, 500);
        setTimeout(forceInitPackingList, 1000);
    }
})();




















