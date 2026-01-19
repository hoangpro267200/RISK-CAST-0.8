# RISKCAST v20 - Modular Architecture

## 📁 Cấu trúc thư mục

```
v20/
├── core/
│   ├── RiskcastInputController.js    # Main orchestrator
│   ├── StateManager.js               # State + localStorage
│   └── APIClient.js                  # API calls + payload builder
├── modules/
│   ├── TransportModule.js            # Trade lane, mode, POL/POD, routes
│   ├── CargoModule.js                # Cargo fields international
│   ├── PartyModule.js                # Seller/Buyer management
│   ├── ModuleCardsManager.js         # 6 risk modules toggle
│   └── PriorityManager.js            # 4-mode priority system
├── ui/
│   ├── DropdownManager.js            # Dropdown + search
│   ├── AutoSuggestManager.js         # POL/POD/country suggest
│   ├── PillGroupManager.js           # Pill selections
│   ├── UploadZoneManager.js          # File upload
│   └── ToastManager.js               # Notifications
├── utils/
│   ├── DataLoaders.js                # Load logistics data
│   ├── Validators.js                 # Form validation
│   ├── DateCalculators.js            # ETA calculation
│   ├── SanitizeHelpers.js            # Sanitize state/payload
│   └── DemoAutoFill.js               # Auto-fill demo
├── effects/
│   ├── ThemeManager.js               # Dark/light theme
│   ├── ParticleBackground.js         # Canvas particles
│   ├── FormPanelGlow.js              # Glow effect
│   ├── NavigationSpy.js              # Scroll spy
│   └── SidebarManager.js             # Sidebar toggle
└── index.js                          # Entry point
```

## 🚀 Sử dụng

### 1. Import trong HTML

Thay đổi script tag trong template HTML:

```html
<!-- OLD -->
<script src="/static/js/pages/input/input_controller_v20.js"></script>

<!-- NEW -->
<script type="module" src="/static/js/v20/index.js"></script>
```

### 2. Backward Compatibility

Code mới vẫn tương thích với code cũ:
- `window.RC_V20` - Controller instance
- `window.RC_STATE` - Form state
- `window.RISKCAST_STATE` - RISKCAST_STATE từ localStorage

## 📝 Các thay đổi chính

### ✅ Đã hoàn thành

1. **Utils Layer** - Tất cả utility functions đã được tách
2. **Effects Layer** - Tất cả visual effects đã được tách
3. **UI Layer** - Tất cả UI components đã được tách
4. **Core Layer** - State management và API client đã được tách
5. **Modules Layer** - Tất cả business logic modules đã được tách
6. **Entry Point** - index.js đã được tạo

### 🔧 Tính năng

- ✅ ES6 modules (import/export)
- ✅ Dependency injection
- ✅ Separation of concerns
- ✅ Mỗi file < 400 dòng
- ✅ JSDoc đầy đủ
- ✅ Error handling
- ✅ Backward compatible

## 🧪 Testing

1. Mở browser console
2. Kiểm tra initialization: `window.RC_V20`
3. Kiểm tra state: `window.RC_STATE`
4. Test form submission
5. Test auto-fill demo

## 📚 API

### StateManager
```javascript
stateManager.getState()
stateManager.setState(key, value)
stateManager.sanitize()
stateManager.persist()
```

### APIClient
```javascript
apiClient.buildShipmentPayloadForAPI(state)
apiClient.submitToEngine(payload)
apiClient.buildRouteLegs(pol, pod)
```

### Modules
Tất cả modules có method `init()` để khởi tạo.

## ⚠️ Lưu ý

- Đảm bảo `LOGISTICS_DATA` được load trước khi init
- Đảm bảo HTML có đầy đủ các element IDs cần thiết
- ES6 modules yêu cầu server hỗ trợ (hoặc build tool)

## 🔄 Migration từ v20 cũ

1. Backup file cũ
2. Update HTML template
3. Test toàn bộ functionality
4. Verify localStorage compatibility



