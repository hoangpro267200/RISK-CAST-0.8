# PHASE 3 — JavaScript Refactor Analysis

## File Inventory (25 files, ~874 KB)

### ✅ CORE Files (Universal logic, no DOM dependencies)
1. **`streaming.js`** → `core/streaming.js`
   - StreamingHandler class
   - SSE/WebSocket streaming logic
   - Token appending logic

2. **`riskcast_data_store.js`** → `core/riskcast_data_store.js`
   - Global RiskCastData object
   - RiskCastDataStore manager
   - Data synchronization methods

3. **`translations_vi.js`** → `core/translations.js` (consolidate)
   - Vietnamese translations dictionary

4. **`translations_en.js`** → `core/translations.js` (consolidate)
   - English translations dictionary

5. **`common_lang.js`** → `core/translations.js` (consolidate)
   - Translation system
   - Language switching logic
   - DOM update functions

### 📦 MODULE Files (Component-level functionality)
6. **`smart_input.js`** → `modules/smart_input.js`
   - Auto-suggestions
   - Validations
   - Input watchers
   - Rating system
   - Container compatibility

7. **`ai_chat.js`** → `modules/ai_chat.js`
   - AI chat widget logic
   - Chat rendering
   - Message UI
   - Panel toggling

8. **`smart_progress_tracker.js`** → `modules/progress_tracker.js`
   - Progress tracking
   - Section completion detection
   - Progress bar updates

9. **`ai_adviser.js`** → `modules/ai_adviser.js`
   - AIAdviserPanel class
   - Risk analysis helper logic

10. **`input_summary_init.js`** → `modules/input_summary.js`
    - Summary generation
    - Data compilation

11. **`enterprise_input.js`** → `modules/enterprise_input.js`
    - Enterprise mode logic
    - Panel toggles
    - Multi-step form processing

12. **`summary.js`** → `modules/input_summary.js` (merge)
    - Summary building logic

### 📄 PAGE Files (Page-specific orchestration)
13. **`home.js`** → `pages/home.js`
    - Home page initialization
    - Hero animations

14. **`input.js`** → `pages/input.js`
    - Input page orchestration
    - Form initialization

15. **`input_form.js`** → Analyze: split between MODULE and PAGE
    - Form validation → MODULE
    - Form initialization → PAGE
    - Dropdown logic → MODULE

16. **`dashboard.js`** → `pages/dashboard.js`
    - Dashboard initialization
    - Stats refresh

17. **`results.js`** → `pages/results.js`
    - Results page renderer

18. **`results_core.js`** → Analyze: split between MODULE and PAGE
    - Core rendering logic → MODULE
    - Page initialization → PAGE

19. **`overview.js`** → `pages/overview.js`
    - Overview page logic

20. **`booking_summary.js`** → `pages/booking_summary.js`
    - Booking summary page

### 📚 DATA Files (Static data, can be moved to core if needed)
21. **`logistics_data.js`** → Keep in root or move to `core/data/`
    - Static logistics data

22. **`climate_data_2025.js`** → Keep in root or move to `core/data/`
    - Climate data

23. **`packing_list.js`** → Analyze: MODULE or PAGE?
    - Packing list logic

24. **`premium_input_tracker.js`** → `modules/progress_tracker.js` (merge)
    - Progress tracking logic

25. **`enterprise.js`** → Analyze
    - Enterprise page logic

## Global Variables Found
- `window.RiskCastData`
- `window.RiskCastDataStore`
- `window.TRANSLATIONS_VI`
- `window.TRANSLATIONS_EN`
- `window.RiskcastLang`
- `window.LOGISTICS_DATA`
- `window._LOGISTICS_DATA_REF`
- `window.__SMART_INPUT_INITIALIZED__`
- `window.__priorityWeightsInjected`
- Many function declarations on `window` object

## Duplicate Functions to Merge
- Language/translation logic (multiple files)
- Progress tracking (smart_progress_tracker.js, premium_input_tracker.js)
- Dropdown handling (multiple files)
- Form validation (multiple files)

## Namespace Strategy
Convert to:
- `RISKCAST.core.*`
- `RISKCAST.modules.*`
- `RISKCAST.pages.*`
- `RISKCAST.store.*`





















