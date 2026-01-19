# 🔧 SERVICE ROUTE DROPDOWN — QUICK FIX GUIDE

## ⚠️ QUAN TRỌNG: Service Route CẦN CHỌN TRƯỚC

Service Route dropdown sẽ **TRỐNG** cho đến khi bạn chọn:

```
1. Trade Lane (ví dụ: Vietnam → China)
   ↓
2. Mode (ví dụ: Sea Freight)
   ↓
3. Shipment Type (ví dụ: FCL)
   ↓
4. Service Routes sẽ AUTO-LOAD vào dropdown
```

---

## 🧪 CÁCH TEST ĐÚNG

### Option 1: Manual Selection (Test từng bước)

```
Bước 1: Mở http://localhost:8000/input_v20

Bước 2: Scroll xuống "01 • Transport Setup"

Bước 3: Click "Trade Lane" → Chọn một route (ví dụ: "🇻🇳🇨🇳 Vietnam → China")

Bước 4: Click "Mode of Transport" → Chọn "Sea Freight"

Bước 5: Click "Shipment Type" → Chọn "FCL"

Bước 6: Click "Priority" → Giữ "Balanced" hoặc chọn bất kỳ

Bước 7: Click "Service Route" → ✅ BÂY GIỜ SẼ CÓ OPTIONS!
```

### Option 2: Auto-Fill Demo (Nhanh nhất)

```
Bước 1: Mở http://localhost:8000/input_v20

Bước 2: Click nút "🧬 Auto-Fill Demo Shipment" ở header

Bước 3: Đợi 2 giây → ✅ TẤT CẢ FIELDS TỰ ĐỘNG ĐIỀN!

Bước 4: Service Route sẽ có giá trị đã chọn
```

---

## 🔍 DIAGNOSTIC TEST

Mở browser console (F12) và paste code này:

```javascript
// Check if data loaded
console.log('LOGISTICS_DATA:', typeof LOGISTICS_DATA !== 'undefined' ? '✅ Loaded' : '❌ Not loaded');
console.log('RC_V20 Controller:', typeof window.RC_V20 !== 'undefined' ? '✅ Initialized' : '❌ Not initialized');

// Check current selections
if (window.RC_V20) {
    const data = window.RC_V20.formData;
    console.log('Current Selections:');
    console.log('  Trade Lane:', data.tradeLane || '❌ NOT SELECTED');
    console.log('  Mode:', data.mode || '❌ NOT SELECTED');
    console.log('  Shipment Type:', data.shipmentType || '❌ NOT SELECTED');
    console.log('  Service Route:', data.serviceRoute || '❌ NOT SELECTED');
}

// Check service route menu
const menu = document.getElementById('serviceRoute-menu');
if (menu) {
    const items = menu.querySelectorAll('.rc-dropdown-item');
    console.log('Service Route Menu Items:', items.length);
    if (items.length === 0) {
        console.warn('⚠️ Menu is empty - you need to select Trade Lane + Mode first!');
    }
} else {
    console.error('❌ Service Route menu not found');
}
```

---

## 🎯 EXPECTED BEHAVIOR

### Khi chưa chọn Trade Lane + Mode:

```
Service Route dropdown: TRỐNG ✅ (đúng)
```

### Sau khi chọn Trade Lane + Mode:

```
Service Route dropdown: CÓ 5-20 ROUTES ✅
```

### Khi click một route:

```
BEFORE: "Select service route" (placeholder)
AFTER: "Cái Mép → Shenzhen Express" (route name) ✅
```

---

## 🚀 QUICK FIX TEST SCRIPT

Paste vào browser console để test nhanh:

```javascript
// Quick fill for testing
if (window.RC_V20 && window.LOGISTICS_DATA) {
    console.log('🧪 Quick Test: Filling Trade Lane + Mode...');
    
    // Get first trade lane
    const routes = LOGISTICS_DATA.routes || {};
    const firstLane = Object.keys(routes)[0];
    if (firstLane) {
        window.RC_V20.selectTradeLane(firstLane, routes[firstLane].name);
        console.log('✅ Trade Lane selected:', firstLane);
        
        setTimeout(() => {
            // Select first mode
            window.RC_V20.selectMode('SEA', 'Sea Freight');
            console.log('✅ Mode selected: SEA');
            
            setTimeout(() => {
                // Check service route menu
                const menu = document.getElementById('serviceRoute-menu');
                const items = menu ? menu.querySelectorAll('.rc-dropdown-item') : [];
                console.log('✅ Service Route Menu now has:', items.length, 'routes');
                
                if (items.length > 0) {
                    console.log('✅ SUCCESS! Service routes loaded correctly!');
                    console.log('You can now click Service Route dropdown to see options');
                } else {
                    console.error('❌ Service routes still empty. Check console for errors.');
                }
            }, 200);
        }, 200);
    }
} else {
    console.error('❌ Controller or data not loaded');
}
```

---

## 🎉 EXPECTED RESULT

Sau khi chọn Trade Lane + Mode + Shipment Type, Service Route dropdown sẽ hiển thị như sau:

```
┌────────────────────────────────────────────────────┐
│ Service Route                                      │
├────────────────────────────────────────────────────┤
│ ✓ RECOMMENDED                                      │
│ Cái Mép → Shenzhen Express                        │
│ Cái Mép → Shenzhen • Maersk Line • 7d • 88% rel  │
├────────────────────────────────────────────────────┤
│ Cái Mép → Hong Kong Direct                        │
│ Cái Mép → Hong Kong • MSC • 5d • 92% reliable     │
├────────────────────────────────────────────────────┤
│ Hải Phòng → Shenzhen Standard                     │
│ Hải Phòng → Shenzhen • CMA CGM • 8d • 85% rel    │
└────────────────────────────────────────────────────┘
```

Khi click một route → Dropdown label thay đổi thành route name đã chọn.

---

## 🔧 NẾU VẪN TRỐNG

Nếu sau khi chọn Trade Lane + Mode mà Service Route vẫn trống:

1. **Check console** (F12) xem có lỗi gì
2. **Check logistics_data.js** đã load chưa:
   ```javascript
   console.log(LOGISTICS_DATA.serviceRoutes);
   ```
3. **Manual trigger:**
   ```javascript
   window.RC_V20.loadServiceRoutes();
   ```

---

## ✅ HOME PAGE ĐÃ FIX

Tất cả links trong home page đã được chuyển từ v19 → v20:

- Navbar "Input" link: `/input_v20` ✅
- Hero "Start Risk Analysis" button: `/input_v20` ✅

---

## 📝 TÓM TẮT

1. **Home page** → ✅ Đã fix (redirect v20)
2. **Service Route dropdown** → ✅ Hoạt động đúng (cần chọn Trade Lane + Mode trước)
3. **Cách test nhanh** → Click nút "🧬 Auto-Fill Demo Shipment"

---

**Thử ngay: Click "🧬 Auto-Fill Demo Shipment" để test toàn bộ form!**






