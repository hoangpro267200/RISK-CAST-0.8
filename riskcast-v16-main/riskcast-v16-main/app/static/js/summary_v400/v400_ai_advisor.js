/* ==========================================================================
   SUMMARY_V400 - AI ADVISOR
   Render validation results in advisor panel
   ========================================================================== */

const V400AIAdvisor = (() => {
    
    /**
     * Render advisor panel
     */
    function render(validationResults, onItemClick) {
        const body = document.getElementById('advisorBody');
        if (!body) return;
        
        const sections = [
            {
                key: 'critical',
                title: 'Lỗi nghiêm trọng',
                icon: '🚨',
                items: validationResults.critical
            },
            {
                key: 'warning',
                title: 'Cảnh báo',
                icon: '⚡',
                items: validationResults.warning
            },
            {
                key: 'suggestion',
                title: 'Gợi ý',
                icon: '💡',
                items: validationResults.suggestion
            }
        ];
        
        // Filter out empty sections
        const visibleSections = sections.filter(s => s.items.length > 0);
        
        if (visibleSections.length === 0) {
            body.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state__icon">✨</div>
                    <div class="empty-state__text">
                        Mọi thứ đều ổn!<br>
                        Không phát hiện vấn đề với lô hàng của bạn.
                    </div>
                </div>
            `;
            return;
        }
        
        body.innerHTML = visibleSections.map(section => `
            <div class="advisor-section">
                <div class="advisor-section__header">
                    <span class="advisor-section__icon">${section.icon}</span>
                    <span class="advisor-section__title advisor-section__title--${section.key}">
                        ${section.title}
                    </span>
                    <span class="advisor-section__count">${section.items.length}</span>
                </div>
                <div class="advisor-section__list">
                    ${section.items.map(item => renderAdvisorItem(item, onItemClick)).join('')}
                </div>
            </div>
        `).join('');
    }
    
    /**
     * Render individual advisor item
     */
    function renderAdvisorItem(item, onItemClick) {
        const fields = item.fieldRefs
            .map(ref => ref.split('.').pop())
            .join(', ');
        
        return `
            <div class="advisor-item advisor-item--${item.severity}" 
                 data-rule-id="${item.id}"
                 data-fields="${item.fieldRefs.join(',')}">
                <div class="advisor-item__message">${item.message}</div>
                <div class="advisor-item__fields">Ảnh hưởng: ${fields}</div>
            </div>
        `;
    }
    
    /**
     * Attach click handlers to advisor items
     */
    function attachHandlers(onItemClick) {
        const items = document.querySelectorAll('.advisor-item');
        
        items.forEach(item => {
            item.addEventListener('click', () => {
                const ruleId = item.dataset.ruleId;
                const fields = item.dataset.fields.split(',');
                
                if (onItemClick) {
                    onItemClick(ruleId, fields);
                }
            });
        });
    }
    
    /**
     * Highlight affected fields
     */
    function highlightFields(fieldPaths) {
        // Remove existing highlights
        document.querySelectorAll('.field-tile--highlighted').forEach(el => {
            el.classList.remove('field-tile--highlighted');
        });
        
        // Add highlights
        fieldPaths.forEach(path => {
            // Find the field key from path
            const fieldKey = findFieldKeyByPath(path);
            if (fieldKey) {
                const tile = document.querySelector(`.field-tile[data-field="${fieldKey}"]`);
                if (tile) {
                    tile.classList.add('field-tile--highlighted');
                    
                    // Scroll into view
                    setTimeout(() => {
                        tile.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }, 100);
                }
            }
        });
    }
    
    /**
     * Find field key by path
     */
    function findFieldKeyByPath(path) {
        for (const [key, config] of Object.entries(V400Renderer.FIELD_MAP)) {
            if (config.path === path) {
                return key;
            }
        }
        return null;
    }
    
    // Public API
    return {
        render,
        attachHandlers,
        highlightFields
    };
})();


