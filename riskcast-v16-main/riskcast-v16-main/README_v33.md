# RISKCAST Overview v33 - FutureOS Enterprise Edition

## 🚀 Complete Integration Guide

This document provides complete instructions for integrating and using the RISKCAST Overview v33 page with Smart Edit Mode and AI Smart Assist.

---

## 📁 File Structure

```
app/
├── templates/
│   └── overview_v33.html          # Main template
├── static/
│   ├── css/
│   │   ├── overview_v33.css        # Main styles
│   │   ├── edit_panel.css         # Edit panel styles
│   │   └── ai_panel.css           # AI panel styles
│   └── js/
│       ├── overview_v33.js         # Main controller + Cesium
│       ├── edit_panel.js          # Smart Edit Mode
│       └── ai_panel.js            # AI Smart Assist
└── routes/
    ├── backend_overview_route_v33.py    # Main route
    ├── update_shipment_route_v33.py     # PATCH endpoint
    └── ai_endpoints_v33.py              # AI endpoints
```

---

## 🔧 Backend Integration

### Step 1: Register Routes in `app/main.py`

Add these imports and route registrations:

```python
# Add imports
from app.routes.backend_overview_route_v33 import router as overview_v33_router
from app.routes.update_shipment_route_v33 import router as update_shipment_router
from app.routes.ai_endpoints_v33 import router as ai_endpoints_router

# Register routes (replace existing overview router if needed)
app.include_router(overview_v33_router)  # Handles /overview
app.include_router(update_shipment_router)  # Handles /api/update_shipment
app.include_router(ai_endpoints_router)  # Handles /api/ai/*
```

### Step 2: Verify Cesium Assets

Ensure Cesium is available at:
- `/static/cesium/Cesium.js`
- `/static/cesium/Widgets/widgets.css`
- `/static/js/cesium_config.js`

---

## 📊 Data Structure

The page expects `shipmentState` JSON with this exact structure:

```json
{
    "transport": {
        "mode": "ocean",
        "vessel_name": "MV Container Ship",
        "flight_number": "-"
    },
    "cargo": {
        "commodity": "Electronics",
        "weight": "24000",
        "volume": "65",
        "container_type": "40ft HC",
        "hs_code": "8471.30"
    },
    "parties": {
        "shipper": "VN Tech Export Ltd.",
        "consignee": "Shanghai Electronics Co.",
        "forwarder": "Global Logistics Inc."
    },
    "risk": {
        "score": 7.2,
        "weather": "Moderate",
        "congestion": "Low",
        "delay_probability": "15%"
    },
    "segments": [
        {
            "from": "VNSGN",
            "to": "SGSIN",
            "lat1": 10.8231,
            "lon1": 106.6297,
            "lat2": 1.3521,
            "lon2": 103.8198,
            "mode": "ocean",
            "distance": 1087.5
        }
    ]
}
```

---

## 🎨 Features

### 1. Smart Edit Mode

**Activation:**
- Toggle "Smart Edit" switch in top-right navbar
- All editable fields become highlighted on hover
- Click any field to open edit panel

**Editable Fields:**
- Transport: mode, vessel_name, flight_number
- Cargo: commodity, weight, volume, container_type, hs_code
- Parties: shipper, consignee, forwarder
- Risk: score, weather, congestion, delay_probability
- Segments: Full segment editor with coordinates

**Edit Panel:**
- Slides in from right
- Auto-generates form based on field type
- Saves via PATCH `/api/update_shipment`
- Updates UI and Cesium globe dynamically

### 2. AI Smart Assist

**Access:**
- Click floating AI button (bottom-right)
- Panel opens with 3 skills

**AI Skills:**

1. **AI Explain**
   - Summarizes shipment, risk, route, anomalies
   - Endpoint: `POST /api/ai/explain`
   - Returns comprehensive explanation

2. **AI What-if Scenario**
   - User enters scenario (e.g., "What if POD becomes USLAX?")
   - Re-runs risk computation
   - Updates UI + Cesium globe
   - Endpoint: `POST /api/ai/what_if`

3. **AI Optimize Route**
   - Suggests best route
   - Shows preview as cyan dotted line on globe
   - User can apply or dismiss
   - Endpoint: `POST /api/ai/optimize`

**Chat Interface:**
- General chat via `POST /api/ai/chat`
- Typing animation
- Message history

### 3. Cesium 3D Globe

**Features:**
- Yellow polyline arcs between ports
- Animated ship/plane icon
- Port labels (POL/POD)
- 3D/2D toggle
- Play/Pause animation
- Zoom controls
- Reset view
- Coordinate tracking

**Controls:**
- `[3D]` / `[2D]` - Toggle view mode
- `[Play]` - Animate vehicle along route
- `[Reset]` - Re-center camera
- `[+]` / `[-]` - Zoom in/out

---

## 🔌 API Endpoints

### GET `/overview`
Returns HTML page with embedded `shipment_state_json`.

**Query Parameters:**
- `id` (optional): Shipment ID

**Response:** HTML template

---

### PATCH `/api/update_shipment`
Updates shipment data.

**Request Body:**
```json
{
    "transport": {...},
    "cargo": {...},
    "parties": {...},
    "risk": {...},
    "segments": [...]
}
```

**Response:**
```json
{
    "status": "success",
    "message": "Shipment updated successfully",
    "shipment": {...}
}
```

---

### POST `/api/ai/explain`
Generates shipment explanation.

**Request Body:**
```json
{
    "transport": {...},
    "cargo": {...},
    "parties": {...},
    "risk": {...},
    "segments": [...]
}
```

**Response:**
```json
{
    "status": "success",
    "explanation": "Detailed explanation text..."
}
```

---

### POST `/api/ai/what_if`
Processes what-if scenario.

**Request Body:**
```json
{
    "shipment": {...},
    "scenario": "What if POD becomes USLAX?"
}
```

**Response:**
```json
{
    "status": "success",
    "analysis": "Scenario analysis...",
    "updated_shipment": {...}
}
```

---

### POST `/api/ai/optimize`
Optimizes route.

**Request Body:**
```json
{
    "transport": {...},
    "segments": [...]
}
```

**Response:**
```json
{
    "status": "success",
    "recommendation": "Optimization details...",
    "optimized_route": {
        "segments": [...]
    }
}
```

---

### POST `/api/ai/chat`
General AI chat.

**Request Body:**
```json
{
    "message": "User message",
    "shipment": {...}
}
```

**Response:**
```json
{
    "status": "success",
    "response": "AI response text"
}
```

---

## 🎯 Usage Examples

### Enable Edit Mode
1. Toggle "Smart Edit" switch
2. Hover over any field → see ✏ icon
3. Click field → edit panel opens
4. Make changes → click "Save Changes"
5. UI and globe update automatically

### Use AI Explain
1. Click AI floating button
2. Click "AI Explain" skill button
3. Wait for explanation
4. Read comprehensive summary

### Use AI What-if
1. Open AI panel
2. Click "What-if Scenario"
3. Enter scenario: "What if POD becomes USLAX?"
4. System recalculates risk
5. Globe updates with new route

### Use AI Optimize
1. Open AI panel
2. Click "Optimize Route"
3. Preview appears as cyan dotted line
4. Confirm to apply or dismiss

---

## 🐛 Troubleshooting

### Cesium Not Loading
- Check `/static/cesium/Cesium.js` exists
- Verify `cesium_config.js` is loaded before Cesium.js
- Check browser console for errors

### Edit Mode Not Working
- Ensure `edit_panel.js` is loaded
- Check browser console for JavaScript errors
- Verify PATCH endpoint is registered

### AI Panel Not Responding
- Check `/api/ai/*` endpoints are registered
- Verify network requests in DevTools
- Check backend logs for errors

### Route Not Displaying
- Verify `segments` array in `shipmentState`
- Check coordinates are valid (lat/lon)
- Ensure Cesium viewer initialized

---

## 🚀 Production Deployment

1. **Minify Assets:**
   - Minify CSS and JS files
   - Enable gzip compression

2. **Cache Headers:**
   - Set appropriate cache headers for static assets
   - Use versioned filenames for cache busting

3. **Error Handling:**
   - Add error boundaries
   - Implement retry logic for API calls

4. **Performance:**
   - Lazy load Cesium
   - Optimize images
   - Use CDN for static assets

---

## 📝 Notes

- All coordinates use decimal degrees (WGS84)
- Distances are in kilometers
- Risk scores are 0-10 scale
- Cesium uses local build (no CDN)
- AI endpoints can be enhanced with Claude/OpenAI integration

---

## ✅ Checklist

- [x] HTML template created
- [x] CSS files created
- [x] JavaScript files created
- [x] Backend routes created
- [x] API endpoints implemented
- [x] Documentation complete

---

## 🎉 Ready to Use!

The Overview v33 page is production-ready. Simply register the routes in `main.py` and access `/overview` to see the FutureOS Enterprise Edition in action!

