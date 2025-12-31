/**
 * FLOATING LANGUAGE SWITCHER
 * A global, fixed-position language toggle component
 * 
 * Supported languages: Vietnamese (vi), English (en), Chinese (zh)
 * 
 * Usage: Include this script and CSS in any page
 * The switcher will automatically appear at bottom-right corner
 */

(function() {
    'use strict';

    // Language configurations
    const LANGUAGES = [
        { code: 'vi', name: 'Tiếng Việt', flag: '🇻🇳', shortName: 'VI' },
        { code: 'en', name: 'English', flag: '🇺🇸', shortName: 'EN' },
        { code: 'zh', name: '中文', flag: '🇨🇳', shortName: 'ZH' }
    ];

    // Storage key
    const STORAGE_KEY = 'riskcast_lang';

    // Get current language
    function getCurrentLanguage() {
        return localStorage.getItem(STORAGE_KEY) || 'vi';
    }

    // Set language
    function setLanguage(langCode) {
        localStorage.setItem(STORAGE_KEY, langCode);
        
        // Dispatch custom event for other components to listen
        window.dispatchEvent(new CustomEvent('languageChanged', { 
            detail: { language: langCode } 
        }));

        // Update HTML lang attribute
        document.documentElement.lang = langCode;

        // Try to use existing translation system if available
        if (window.RISKCAST && window.RISKCAST.core && window.RISKCAST.core.translations) {
            window.RISKCAST.core.translations.setLanguage(langCode);
        }

        // Reload page to apply translations (for server-rendered content)
        // Comment out if you have full client-side translation support
        // window.location.reload();
        
        // Update switcher UI
        updateSwitcherUI(langCode);
        
        // Try to apply translations without reload
        applyTranslations(langCode);
    }

    // Apply translations client-side
    function applyTranslations(langCode) {
        // If RISKCAST translation system exists, use it
        if (window.RISKCAST && window.RISKCAST.core && window.RISKCAST.core.translations) {
            try {
                window.RISKCAST.core.translations.setLanguage(langCode);
            } catch (e) {
                console.warn('[FloatingLangSwitcher] Could not apply translations:', e);
            }
        }
        
        // For React pages, trigger re-render via localStorage change
        // React components should listen to storage events
        window.dispatchEvent(new StorageEvent('storage', {
            key: STORAGE_KEY,
            newValue: langCode,
            oldValue: getCurrentLanguage()
        }));
    }

    // Update switcher UI to reflect current language
    function updateSwitcherUI(langCode) {
        const switcher = document.querySelector('.floating-lang-switcher');
        if (!switcher) return;

        // Update badge
        const badge = switcher.querySelector('.current-lang-badge');
        const lang = LANGUAGES.find(l => l.code === langCode);
        if (badge && lang) {
            badge.textContent = lang.shortName;
        }

        // Update active state
        switcher.querySelectorAll('.lang-option').forEach(option => {
            const optionLang = option.getAttribute('data-lang');
            if (optionLang === langCode) {
                option.classList.add('active');
            } else {
                option.classList.remove('active');
            }
        });
    }

    // Create the floating switcher HTML
    function createSwitcherHTML() {
        const currentLang = getCurrentLanguage();
        const currentLangData = LANGUAGES.find(l => l.code === currentLang) || LANGUAGES[0];

        return `
            <div class="floating-lang-switcher" id="floating-lang-switcher">
                <!-- Collapsed: Toggle Button -->
                <button class="lang-toggle-btn" id="lang-toggle-btn" title="Change Language">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="2" y1="12" x2="22" y2="12"/>
                        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                    </svg>
                    <span class="current-lang-badge">${currentLangData.shortName}</span>
                </button>

                <!-- Expanded: Language Options -->
                <div class="lang-options-panel" style="position: relative;">
                    <button class="lang-close-btn" id="lang-close-btn" title="Close">×</button>
                    <div class="lang-panel-header">
                        <span class="panel-title">Select Language</span>
                    </div>
                    ${LANGUAGES.map(lang => `
                        <button class="lang-option ${lang.code === currentLang ? 'active' : ''}" data-lang="${lang.code}">
                            <span class="lang-flag">${lang.flag}</span>
                            <div class="lang-info">
                                <span class="lang-code">${lang.shortName}</span>
                                <span class="lang-name">${lang.name}</span>
                            </div>
                            <span class="lang-check">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                                    <polyline points="20 6 9 17 4 12"/>
                                </svg>
                            </span>
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // Initialize the switcher
    function initSwitcher() {
        // Don't initialize if already exists
        if (document.getElementById('floating-lang-switcher')) {
            return;
        }

        // Inject HTML
        const container = document.createElement('div');
        container.innerHTML = createSwitcherHTML();
        document.body.appendChild(container.firstElementChild);

        // Get elements
        const switcher = document.getElementById('floating-lang-switcher');
        const toggleBtn = document.getElementById('lang-toggle-btn');
        const closeBtn = document.getElementById('lang-close-btn');

        // Toggle expand/collapse
        toggleBtn.addEventListener('click', () => {
            switcher.classList.add('expanded');
        });

        closeBtn.addEventListener('click', () => {
            switcher.classList.remove('expanded');
        });

        // Handle language selection
        switcher.querySelectorAll('.lang-option').forEach(option => {
            option.addEventListener('click', () => {
                const lang = option.getAttribute('data-lang');
                setLanguage(lang);
                
                // Collapse after selection
                setTimeout(() => {
                    switcher.classList.remove('expanded');
                }, 200);
            });
        });

        // Close on click outside
        document.addEventListener('click', (e) => {
            if (!switcher.contains(e.target)) {
                switcher.classList.remove('expanded');
            }
        });

        // Initialize current language display
        updateSwitcherUI(getCurrentLanguage());
        
        console.log('[FloatingLangSwitcher] Initialized with language:', getCurrentLanguage());
    }

    // Auto-initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSwitcher);
    } else {
        initSwitcher();
    }

    // Expose API globally
    window.FloatingLangSwitcher = {
        getCurrentLanguage,
        setLanguage,
        LANGUAGES
    };

})();

